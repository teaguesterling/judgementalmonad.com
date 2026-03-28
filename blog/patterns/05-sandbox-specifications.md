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

## The ratchet connection

The sandbox spec tightens over time:
1. Start with `sandbox = "unrestricted"` (observe resource usage)
2. After 100 runs that never exceed 300MB: tighten to `memory = "512m"`
3. After 1000 runs: tighten to `memory = "400m"`

Each tightening is a ratchet turn — the grade drops, characterizability improves, regulatory cost decreases. The spec IS the ratchet artifact for execution environments.
