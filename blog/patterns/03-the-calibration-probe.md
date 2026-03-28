# The Calibration Probe

*A 3-5 turn diagnostic that characterizes how a model behaves — before committing to a configuration.*

---

## The problem

The Quartermaster needs to know what kind of model it's configuring. Hardcoded profiles ("Haiku needs focus, Opus plans naturally") work until the model changes. A new model version, a fine-tune, or an entirely new model makes the profiles stale.

## The pattern

Before the real task, run a short diagnostic sequence — 3-5 tool calls — and observe the model's behavior. The probe doesn't solve the task. It characterizes the solver.

### The diagnostic sequence

```
1. file_glob("**/*.py")              — does the model explore broadly or narrowly?
2. file_read(first_result)           — does it read one file or request everything?
3. run_tests()                       — does it analyze the output or immediately edit?
```

From these three calls, the Quartermaster classifies:

| Behavior pattern | Interpretation | Configuration |
|---|---|---|
| Reads everything before acting | Opus-like (deep planner) | Minimal tools, no strategy instruction |
| Starts editing after one file | Haiku-like (impulsive) | Simple tools + strategy instruction |
| Reads then acts methodically | Sonnet-like (balanced) | Full tool set, optional strategy |
| Makes many tool selection errors | Overwhelmed | Reduce tool count |
| Uses batch tools naturally | Strong planner | Include batch tools |
| Ignores batch tools | Weak planner or preference for simple | Remove batch tools, reduce noise |

### The cost

3 tool calls × ~$0.01-0.05 per call = $0.03-0.15. The probe costs less than 1% of the task. A misconfigured task costs 20-56% more (our experimental data). The probe pays for itself immediately.

## Implementation

The probe runs as the first few turns of the task, not as a separate session. The Quartermaster observes the first 3-5 tool calls, then dynamically adjusts the configuration — enabling or disabling tool groups, injecting or withholding the strategy instruction.

This requires a Harness that can reconfigure mid-session — which is what the Mode Controller (pattern 7) provides.

## Three layers of model knowledge

1. **Hardcoded profiles** — starting point, covers known models. Updated by the ratchet.
2. **Experimental data** — periodic validation runs that confirm or update profiles.
3. **Calibration probe** — real-time characterization for unknown or changed models.

Each layer is a fallback for the one above. The probe runs when the profiles are uncertain. The profiles are updated when experiments produce new data.

## What's next

The probe feeds the Quartermaster. The Quartermaster configures the executor. The Mode Controller monitors the executor and can re-probe if behavior changes mid-task (model degrades, task turns out to be different than expected).
