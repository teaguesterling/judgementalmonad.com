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

## Concrete probe design

### Level 0: Static profile lookup

Before any probe runs, check if we have a known profile:

```python
KNOWN_PROFILES = {
    "claude-haiku-4-5": {
        "planning_capacity": "low",
        "tool_selection": "poor_with_many",
        "batch_capable": False,
        "strategy_impact": "essential",
        "recommended_kit": "simple_tools + run_tests + principle",
    },
    "claude-sonnet-4-6": {
        "planning_capacity": "medium",
        "tool_selection": "good",
        "batch_capable": True,
        "strategy_impact": "helpful",
        "recommended_kit": "file_tools + bash_sandboxed",
    },
    "claude-opus-4-6": {
        "planning_capacity": "high",
        "tool_selection": "excellent",
        "batch_capable": True,
        "strategy_impact": "harmful",
        "recommended_kit": "simple_tools + run_tests",
    },
}
```

If the model is known, skip the probe. If it's unknown or the profile is stale (model updated), run the probe.

### Level 1: Behavioral probe (3 tool calls)

Give the agent a trivial task with all tools available. Observe:

```
Probe task: "This codebase has a file called README.md.
Read it and tell me what the project does."

Observe:
  Call 1: What does the agent do first?
    - file_glob("*.md") → "explorer" (maps before reading)
    - file_read("README.md") → "direct" (goes straight to the answer)
    - file_list(".") → "cautious" (checks what's available)
    - bash("cat README.md") → "bash-native" (reaches for bash first)

  Call 2: Does the agent stop after getting the answer?
    - Yes → "focused" (answers the question, done)
    - Reads more files → "thorough" (over-investigates)
    - Runs tests → "habitual" (follows a workflow regardless of task)

  Call 3: How does it present the result?
    - Brief answer → "concise"
    - Detailed analysis → "verbose" (may need action-oriented coaching)
```

### Level 2: Stress probe (5 tool calls)

Give the agent a task with a deliberate trap — two plausible approaches, one correct:

```
Probe task: "The file src/config.py has a function called
parse_value that returns the wrong type for boolean inputs.
The tests in tests/test_config.py document the expected behavior.
Fix it."

Observe:
  - Does the agent read the test first or the source first?
    → Tests first = "diagnosis-oriented" (configure with principle)
    → Source first = "implementation-oriented" (may need principle)
  - Does the agent run tests before editing?
    → Yes = "verify-first" (good workflow, may not need strategy)
    → No = "edit-first" (needs strategy instruction)
  - How many edits before running tests?
    → 1 = "cautious" (good, may be slow)
    → 3+ = "batch-oriented" (efficient, give batch tools)
    → 0 (never edits) = "over-analyzing" (skip strategy instruction)
```

### Probe cost

| Probe level | Calls | Estimated cost | When to use |
|---|---|---|---|
| Level 0 (lookup) | 0 | $0.00 | Known model, profile not stale |
| Level 1 (behavioral) | 3 | $0.03-0.10 | Unknown model, quick characterization |
| Level 2 (stress) | 5 | $0.05-0.20 | Unknown model, need detailed profile |

The probe cost is <1% of a typical task. A misconfigured task costs 15-56% more.

## When profiles go stale

Model updates can change behavior without changing the model name. Signs that a profile is stale:

- Pass rate drops below the profile's predicted rate
- Cost per run diverges from the profile's predicted range
- The Coach detects new tool usage patterns (model started using batch tools where it didn't before)

When staleness is detected, the Quartermaster triggers a Level 2 probe on the next task and updates the profile from the results.

## What's next

The probe feeds the Quartermaster. The Quartermaster configures the executor. The Mode Controller monitors the executor and can re-probe if behavior changes mid-task (model degrades, task turns out to be different than expected). The Coach tracks whether the probe's predictions hold over time — closing the learning loop.
