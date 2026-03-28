# Sandbox Specifications

*Declarative execution environment bounds that make every command's grade explicit, enforceable, and queryable.*

---

## The problem

Every registered command has an implicit grade — how much world coupling it has, what computation level it operates at. But the grade is invisible. You can't query it, enforce it, or reason about it. Two commands with the same `bash -c` interface have different actual grades depending on what the sandbox allows.

## The pattern

Declare the execution environment bounds alongside the command. The bounds make the grade explicit.

```toml
[commands.test]
cmd = "python -m pytest tests/"

[commands.test.sandbox]
network = "none"
filesystem = "readonly"
timeout = "60s"
memory = "512m"
cpu = "30s"
processes = "isolated"
```

### Effects ceiling vs tool interface

The sandbox provides an **effects ceiling** — the maximum computation level that the sandbox's effect constraints allow. The actual risk depends on two things:

1. The **tool interface** — what the agent can ask for (a property of the tool's design)
2. The **effects ceiling** — what the sandbox permits (a property of the sandbox spec)

```
A level 1 tool in a level 7 sandbox: effective risk = level 1
  (the tool doesn't use the sandbox's full allowance)

A level 4 tool in a level 2 sandbox: effective risk = level 2
  (the sandbox constrains the consequences)
```

The sandbox can't distinguish level 3 (writing data) from level 4 (writing executable code). Both look like "writes bytes to a file." The level 3/4 distinction lives in the *tool interface*, not the sandbox. The sandbox bounds effects; the tool interface determines the computation level.

### Presets

| Preset | Network | Filesystem | Timeout | Memory | Effects ceiling |
|---|---|---|---|---|---|
| **readonly** | none | readonly | 30s | 256m | Level 2 |
| **test** | none | readonly | 60s | 512m | Level 2 |
| **build** | none | workspace_only | 5m | 2g | Level 4 |
| **integration** | localhost | workspace_only | 10m | 4g | Level 7+ |

## The grade computation

```python
@property
def effects_ceiling(self) -> int:
    if self.network != "none":
        return 8  # can reach external services
    if self.processes == "visible" and self.filesystem not in ("readonly",):
        return 7  # can spawn persistent subprocesses + write
    if self.filesystem not in ("readonly",):
        return 4  # can write; can't distinguish data from code
    return 2      # read + compute only
```

### What the sandbox can enforce

| Dimension | Mechanism | What it bounds |
|---|---|---|
| Network | `--unshare-net` (bwrap) | Data exfiltration |
| Filesystem | `--ro-bind` / `--bind` | Persistent mutation |
| Processes | `--unshare-pid` + `--die-with-parent` | Subprocess spawning |
| Timeout | `subprocess.run(timeout=N)` | Infinite loops |
| Memory | cgroup `memory.max` | Memory exhaustion |
| CPU | cgroup `cpu.max` | CPU exhaustion |

### What the sandbox cannot enforce

- Whether a file write is data or executable code (level 3 vs level 4)
- Whether the computation's output is faithful to its input (infidelity)
- What information the process reads from mounted paths (information disclosure within scope)

These are properties of the *tool interface* and the *agent's training*, not of the sandbox.

## Implementation

Full design: `~/Projects/lq/main/docs/design/design-sandbox-specs.md`

The sandbox spec integrates with blq's command registry — every registered command has a declared sandbox spec, logged alongside its output, queryable by DuckDB.

## From our experiments: what D actually is

We assumed our sandboxed bash (Condition D) was level 4. It was level 7.

We tested empirically: a forked process inside bwrap survived after the tool call completed. The parent process exited, the bwrap container terminated, but the child process persisted on the host. The fold model broke — there was computation happening that the Harness didn't invoke and couldn't observe.

Adding `--die-with-parent` to bwrap fixed it — all children are killed when bwrap exits. One flag changed D from level 7 to level 4. That's the sandbox spec doing its job: making the grade explicit so you can reason about it.

```
D without --die-with-parent:  (scoped-rw, level 7)  — can spawn persistent processes
D with --die-with-parent:     (scoped-rw, level 4)  — can write + execute, no spawning
I (separated write/execute):  (scoped, level 3)     — structured write, sandboxed verify
Production bash (no sandbox): (open, level 8)        — unrestricted
```

Without the sandbox spec, you don't know your system's grade. With it, you can see that one bwrap flag is the difference between level 4 and level 7.

## Integration with blq

The sandbox spec integrates with blq's command registry. Every registered command has a declared sandbox spec:

```toml
# blq command with sandbox spec
[commands.test]
cmd = "python -m pytest tests/"
sandbox = "test"  # preset: readonly + no network + 60s + 512m

[commands.build]
cmd = "make -j8"
sandbox = "build"  # preset: workspace_only + no network + 5m + 2g
```

blq logs the spec alongside every run:

```sql
-- What grade is each command?
SELECT command, sandbox_preset, effects_ceiling
FROM blq_commands
ORDER BY effects_ceiling DESC;

-- Were any bounds hit?
SELECT run_id, command, violation_type
FROM blq_sandbox_violations
ORDER BY timestamp DESC;
```

The sandbox spec makes the grade queryable. You can ask "what's the highest-grade command in my system?" and get a precise answer.

## The monitoring-before-enforcing workflow

You don't start with enforcement. You start with observation:

### Phase 0: Monitor (no enforcement)

```toml
[commands.test]
cmd = "python -m pytest tests/"
sandbox = "monitor"  # log resource usage, don't enforce limits
```

blq captures: actual memory usage, actual CPU time, actual network activity, actual filesystem writes. After 100 runs, you know what the command *actually does*.

### Phase 1: Declare (spec, no enforcement)

```toml
[commands.test]
cmd = "python -m pytest tests/"
sandbox.network = "none"       # declare: this command shouldn't need network
sandbox.filesystem = "readonly" # declare: this command shouldn't write
# enforcement = false (still monitoring)
```

blq warns if the command violates its declaration — but doesn't block. You're building confidence that the spec matches reality.

### Phase 2: Enforce

```toml
[commands.test]
cmd = "python -m pytest tests/"
sandbox.network = "none"
sandbox.filesystem = "readonly"
sandbox.timeout = "60s"
sandbox.memory = "512m"
# enforcement = true (bwrap wraps the command)
```

Now violations are blocked, not just logged. The spec is backed by bwrap.

### Phase 3: Tighten

After 1000 runs at 512m with actual usage never exceeding 300m:

```toml
sandbox.memory = "400m"  # tightened with margin
```

Each phase is a ratchet turn. The grade drops. The characterizability improves. The spec becomes more precise — and more valuable as documentation of what the command actually needs.
