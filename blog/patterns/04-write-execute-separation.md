# Write/Execute Separation

*The agent writes through auditable tools. Execution goes through a sandbox it doesn't control.*

---

## The problem

The agent needs to modify code and verify the modifications work. With bash, both happen in one tool call: write a fix script and run it, then run pytest. Write and execute in one opaque operation. The Harness receives the command string and cannot decide non-trivial semantic properties of it (Rice's theorem).

With structured tools, the agent writes through `file_edit` (auditable, logged, typed) and verifies through `run_tests` (sandboxed, structured output). The two operations are separate tool calls. The Harness sees the write, can audit the content, and controls the execution environment independently.

## The pattern

Separate the write path from the execute path. Each has its own tool, its own sandbox, its own audit trail.

```
Write path:   file_edit → workspace (level 3, mutation, logged)
Execute path: run_tests → bwrap(readonly, no-net, pid-isolated) → pytest
```

The agent cannot close the loop on its own. It writes code through one tool and the only execution path goes through a sandbox it doesn't control. The Harness mediates the transition.

## Why this matters

### Bash combines write and execute (level 4-7)

A single bash tool call can write a file containing arbitrary code and then execute it. The Harness receives this as a string. Can it tell whether the file content is safe? Not in general (Rice's theorem). Can it tell what executing the written code will do? Not without running it. The write and the execute are composed in an opaque channel.

Without `--die-with-parent`, bash can also spawn persistent subprocesses (level 7): processes that outlive the tool call, invisible to the Harness. We confirmed this empirically — forked processes survive even after `subprocess.run` timeout.

### Structured tools separate them (level 3)

```
Tool call 1: file_edit(path="src/evaluator.py", old_string="...", new_string="...")
  → Harness logs: what file, what changed, auditable diff
  → Grade: level 3 (structured mutation)

Tool call 2: run_tests()
  → Executes inside bwrap: read-only workspace, no network, no spawning
  → Agent's code runs but can't exfiltrate, persist, or modify the workspace
  → Grade: level 1 interface, level 2 effects ceiling
```

The Harness sees the write (tool call 1) before the execute (tool call 2). It could:
- Audit the content of the edit (static analysis, pattern matching)
- Reject the edit before execution (policy check)
- Run the tests in a stricter sandbox than the writes require
- Log the full chain: intent → write → execute → result

None of this is possible when write and execute are one opaque bash call.

## The grade analysis

Two components determine the grade:

**Tool interface level** — what the agent can ask for:
- `file_edit`: level 3 (structured mutation — path, old_string, new_string)
- `run_tests`: level 1 (structured query — test_file, verbose)
- `bash_sandboxed`: level 4+ (arbitrary executable specification)

**Effects ceiling** — what the sandbox allows:
- `file_edit`: writes one file at the specified path
- `run_tests` under bwrap: read-only, no network, no process spawning
- `bash_sandboxed` under bwrap: read-write, no network, can spawn (level 7 without `--die-with-parent`)

The composite:

| Configuration | Write level | Execute level | Composite | Decidable? |
|---|---|---|---|---|
| **Separated (I)** | 3 (file_edit) | 2 (run_tests in bwrap-ro) | **3** | **Yes** — all effects enumerable |
| **Combined (D)** | 4+ (bash writes + executes) | 4-7 (bash in bwrap-rw) | **4-7** | **No** — Rice's theorem |
| **Production bash** | 8 (unrestricted) | 8 (unrestricted) | **8** | **No** — can modify controller |

## The evidence

From the experiments, separated (I) and combined (D) achieve the same outcomes:

| | I (separated) | D (combined) |
|---|---|---|
| Pass rate (Sonnet) | 100% | 100% |
| Cost | $1.08 | $1.03 |
| Grade | Level 3 | Level 4 |

The ~5% cost premium ($1.08 vs $1.03) buys:
- Every write is auditable before execution
- Execution is read-only (can't persist malicious changes)
- No subprocess spawning (fold model holds)
- The Harness can enumerate all possible effects

## Implementation

### The write side

Use structured file tools with simple interfaces:
```python
file_edit(path: str, old_string: str, new_string: str) -> str
file_write(path: str, content: str) -> str
```

Each call is logged to JSONL with the full arguments. The Harness can diff the workspace before and after.

### The execute side

Run pytest inside bubblewrap with strict bounds:
```python
bwrap_cmd = [
    "bwrap",
    "--ro-bind", workspace, workspace,      # read-only workspace
    "--ro-bind", "/usr", "/usr",            # system libraries
    "--tmpfs", "/tmp",                       # writable scratch
    "--unshare-net",                         # no network
    "--unshare-pid",                         # isolated processes
    "--die-with-parent",                     # kill all children on exit
    "--new-session",
    "bash", "-c", f"PYTHONPATH={workspace} python3 -m pytest tests/"
]
```

Key: `--ro-bind` for workspace (agent's code runs but can't write back), `--die-with-parent` (no persistent subprocesses), `--unshare-net` (no exfiltration).

### What the Harness can decide (before execution)

| Property | Separated (I) | Combined (D) |
|---|---|---|
| Files that will be read | Yes (path in args) | Undecidable |
| Files that will be written | Yes (path in args) | Undecidable |
| Network access | No (by construction) | No (bwrap) |
| Subprocess spawning | No (bwrap) | Undecidable |
| Termination | Yes (timeout) | Yes (timeout) |
| All effects | Enumerable | Uncharacterizable |

## The anti-pattern: wrapping bash

`run_tests` as a wrapper around pytest (still runs arbitrary code) doesn't provide full separation if the agent can also write through bash. The pattern only works when:
1. ALL writes go through structured tools (no `bash_sandboxed` for file modification)
2. ALL execution goes through sandboxed tools (no direct bash for running code)
3. The sandbox for execution is strictly more constrained than the write permissions

If the agent has both `file_edit` and `bash_sandboxed`, it can bypass the separation by using bash for everything — which is what we observed in Condition C (file tools + bash): the agent treated structured tools as optional.

## The ratchet connection

Write/Execute Separation is the structural argument for Condition I (principle + structured tools): same cost as bash, but the write path is auditable and the execute path is consequence-bounded. The ~13% cost premium over E (file tools + bash) is the price of this separation. Whether it's worth paying depends on the deployment context — but the separation is what makes the system characterizable.
