# Experimental Foundations

*~200 runs across 3 models and 9 configurations. The surprising findings.*

---

## The experiments

We ran a synthetic bug-fixing task — 5 seeded bugs in a Python evaluator (~600 lines) — across nine tool configurations and three models (Haiku, Sonnet, Opus). ~200 total runs. Everything logged, everything queryable.

The configurations varied three dimensions:
- **Tools**: structured file tools vs. file tools + bash vs. structured + semantic
- **Strategy**: no instruction vs. 50-token principle vs. detailed four-phase prescription
- **Sandbox**: read-only bwrap vs. read-write bwrap vs. no sandbox

The full experimental design and raw data are in [the experiment series](../fuel/index). What follows are the findings that surprised us.

---

## Finding 1: Strategy instructions are model-dependent — and the wrong one is worse than none

A 39-word instruction — "Do not start editing until you understand the full picture. Read the code, run the tests, and identify all the bugs first. Multiple test failures often share a root cause — find the root causes before fixing symptoms." — had opposite effects at different capability levels:

| Model | Without instruction | With instruction | Effect |
|---|---|---|---|
| **Haiku** (n=5 each) | 40% pass, $0.69 | **100% pass**, $0.66 | **+60% reliability** |
| **Sonnet** (n=24 vs 28) | 82% pass, $1.35 | **100% pass**, $1.08 | +18% reliability, **-20% cost** |
| **Opus** (n=13 vs 10) | **100% pass**, $1.15 | 85% pass, $1.67 | **-15% reliability, +45% cost** |

The instruction costs ~50 tokens and saves ~13,000 output tokens for Sonnet (49K → 37K). That's a 260:1 return. But for Opus, it amplifies the model's natural tendency to plan — delaying action past the useful point.

A detailed four-phase prescription — "1) Use file_glob to find files, 2) Use file_read_batch to read all source and test files, 3) Use file_edit_batch to apply fixes, 4) Use run_tests to verify" — cost +56% over baseline. The agent writes verbose phase-by-phase analysis, complying with the prescription instead of solving the problem.

**The lesson:** strategy instructions constrain which paths the agent takes through its decision space. For models that explore too much (Haiku), the constraint prunes waste. For models that already focus well (Opus), the constraint over-prunes. A universal instruction is always wrong for at least one model.

---

## Finding 2: Structured tools cost 5% more than bash — and buy characterizability

| | Structured (I) | Bash (D) |
|---|---|---|
| Pass rate (Sonnet) | 100% | 100% |
| Mean cost | $1.08 | $1.03 |
| Grade | Level 3 | Level 4-7 |

The ~5% cost premium ($1.08 vs $1.03) buys:
- Every write is auditable before execution
- Execution is read-only (can't persist unexpected changes)
- No subprocess spawning
- The system can enumerate all possible effects

With bash, the agent writes code and executes it in one opaque operation. The system receives a command string and cannot decide non-trivial semantic properties of it (Rice's theorem). With structured tools, writes go through `file_edit` (logged, typed, diffable) and execution goes through a read-only sandbox the agent doesn't control.

The separation matters because it changes what kind of system you're running. Structured tools are level 3 — the system can characterize what the agent can do. Bash is level 4+ — it can't.

---

## Finding 3: One sandbox flag was the difference between level 4 and level 7

We assumed our sandboxed bash (bubblewrap with `--ro-bind`, `--unshare-net`, `--unshare-pid`) was level 4. It was level 7.

A forked process inside bwrap survived after the tool call completed. The parent exited, bwrap terminated, but the child persisted on the host. There was computation happening that the system didn't invoke and couldn't observe.

Adding `--die-with-parent` fixed it. One flag. Level 7 → level 4.

```
Without --die-with-parent:  level 7 — persistent subprocesses
With --die-with-parent:     level 4 — contained execution
Structured tools:           level 3 — auditable writes, sandboxed execution
Production bash:            level 8 — unrestricted
```

**The lesson:** you don't know your system's grade until you measure it. The sandbox spec makes the grade explicit — and queryable:

```sql
SELECT command, sandbox_preset, effects_ceiling
FROM blq_commands
ORDER BY effects_ceiling DESC;
```

---

## Finding 4: Don't restrict what you haven't measured

The monitoring-before-enforcing workflow:

1. **Monitor** — run commands with logging, no enforcement. After 100 runs, you know what the command actually does: actual memory, CPU, network, filesystem writes.
2. **Declare** — write the spec based on observations. Log violations but don't block. Build confidence that spec matches reality.
3. **Enforce** — violations are blocked. The spec is backed by bwrap.
4. **Tighten** — after 1000 runs at 512MB with actual usage never exceeding 300MB, tighten to 400MB with margin.

Each phase is a ratchet turn. The grade drops. The characterizability improves. The spec becomes more precise — and more valuable as documentation of what the command actually needs.

---

## Finding 5: The optimal configuration for each model

| Model | Best config | Pass | Cost | Why |
|---|---|---|---|---|
| **Haiku** | 5 structured tools + principle | **100%** | $0.66 | Focus. Fewer tools, clear strategy. |
| **Sonnet** | File tools + bash | **100%** | $0.98 | Natural selection. Picks the right tool per operation. |
| **Opus** | Structured tools, no principle | **100%** | $1.62 | Plans naturally. Instruction hurts. |

The optimal for one model is the worst for another. The [Calibration Probe](02-the-calibration-probe) pattern addresses this — characterize the model before committing to a configuration.

---

## What these findings mean for the rest of the patterns

The remaining patterns in this series build on these findings:

- **[The Calibration Probe](02-the-calibration-probe)** — runtime characterization so you select the right configuration without running 200 experiments per task
- **[Tool-Call Combinators](03-tool-call-combinators)** — compose structured tool calls efficiently, reducing the cost premium of separation
- **[The Mode Controller](04-the-mode-controller)** — failure-driven transitions between configurations during a task
- **[The Coach](05-the-coach)** — continuous observation that feeds data back into the ratchet

---

```{seealso}
- [Ratchet Fuel](../fuel/index) — The practitioner series where these experiments live
- [The Ma of Multi-Agent Systems](../ma/index) — The theory behind grades and computation levels
```
