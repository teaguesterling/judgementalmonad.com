# Plan: Quartermaster Experiment

*Tests whether a planning phase that selects the executor's tool set improves outcomes.*

---

## The idea

Plan mode in Claude Code already acts as a configuration generator — it reads the codebase, identifies relevant files, and produces a structured plan. The quartermaster extension: the plan also specifies *which tools the executor needs*.

This is Experiment 11 (autonomy placement) with an additional dimension: the planner doesn't just produce a plan, it produces a *configuration*.

## Design

### Phase 1: Quartermaster (plan mode)

Tools: `{file_read, file_read_batch, file_search, file_search_context, file_glob, file_count, run_tests}`. Broad read access, no edits, no bash. The agent explores and produces:

```json
{
  "diagnosis": "description of what's wrong and why",
  "files_to_modify": ["src/tokenizer.py", "src/evaluator.py"],
  "approach": "Fix the string quoting in tokenizer first, then fix 4 evaluator bugs",
  "tools_needed": {
    "read": ["file_read_batch"],
    "edit": ["file_edit_batch"],
    "verify": ["run_tests"],
    "not_needed": ["file_search", "file_glob", "bash_sandboxed", "file_edit"]
  },
  "tool_rationale": {
    "file_edit_batch": "Multiple edits per file — tokenizer needs 1 edit, evaluator needs 4. Batch is more efficient than individual file_edit calls.",
    "file_read_batch": "Need to read 2 source files + 2 test files at start. One call instead of four.",
    "run_tests": "Verify after each file's fixes. Expect 2 calls: once after tokenizer, once after evaluator."
  },
  "estimated_calls": 5,
  "estimated_sequence": [
    "file_read_batch([src/tokenizer.py, src/evaluator.py, tests/test_tokenizer.py, tests/test_evaluator.py])",
    "file_edit_batch([tokenizer fix])",
    "run_tests()",
    "file_edit_batch([4 evaluator fixes])",
    "run_tests()"
  ],
  "risks": ["tokenizer fix may cascade — run tests after tokenizer before evaluator"]
}
```

The quartermaster selects batch tools over atomic ones — `file_edit_batch` over `file_edit`, `file_read_batch` over sequential `file_read`. This is the tool-selection intelligence that a fixed mode can't provide. The quartermaster knows that 5 edits across 2 files is a batch job, not 5 individual operations.

### Phase 2: Executor (implementation mode)

Tools: only what the quartermaster specified, plus `file_read` on the specified files only. The executor sees the plan as its prompt and has a scoped tool set.

If the quartermaster said `tools_needed: ["file_edit", "run_tests"]`, the executor gets exactly those tools — no bash, no search, no glob. It doesn't need to explore because the quartermaster already did that. It executes the plan.

### Comparison conditions

| Condition | Planning phase | Execution phase | Tool selection |
|---|---|---|---|
| **QM** (quartermaster) | Broad read + run_tests | Tools selected by planner | Adaptive per task |
| **B-fixed** (fixed front-load) | Broad read + run_tests | file_edit + run_tests only | Same every task |
| **E** (no planning) | — | file_tools + bash | Agent decides everything |
| **D** (bash, no planning) | — | bash only | Agent decides everything |

### Predictions

- **QM < E on cost** if the quartermaster correctly scopes the executor, reducing the executor's exploration overhead
- **QM ≈ D on cost** if the scoped executor is as efficient as bash (fewer round-trips because it knows exactly what to do)
- **QM > B-fixed on quality** because the tool selection is task-adaptive, not one-size-fits-all
- **QM's planning phase cost is offset** by the executor's reduced exploration

### What this tests

1. **Does adaptive tool selection beat fixed tool sets?** (QM vs B-fixed)
2. **Does planning + scoped execution beat unscoped execution?** (QM vs E, QM vs D)
3. **Can specified planning replace the computation channel?** (QM vs D — does the plan give the executor what bash's flexibility provides?)

### Connection to the framework

The quartermaster is the ratchet applied at task level. Each task gets its own crystallization:
- Discovery: plan mode explores the problem space
- Crystallization: the plan specifies files, approach, and tools
- Application: the executor works within the crystallized configuration

The key difference from our current ratchet experiments (G, H, I): those crystallize patterns across tasks (better tools, better instructions). The quartermaster crystallizes within a single task (this specific bug needs these specific tools). Both are ratchet turns. The quartermaster turns faster (per-task) but doesn't accumulate (the plan is ephemeral).

### Connection to modes

The quartermaster is the missing piece in the modes essay. The essay defines modes (debug, implementation, test-dev, review) and describes failure-driven transitions between them. But it doesn't say who selects the *initial* mode or configures the mode sequence for a given task. The quartermaster does that.

| Component | When | What | How |
|---|---|---|---|
| Quartermaster | Before task | Select initial mode + tool set | Plan mode with broad read access |
| System 2 (Harness) | Every turn | Route messages, enforce permissions | Specified protocol |
| System 3 (Controller) | On failure thresholds | Switch modes, reallocate | Failure-driven specified rules |

### Implementation

Requires two `claude -p` calls per task:
1. Plan call: broad tools, structured output (JSON plan)
2. Execute call: scoped tools (from plan), plan as prompt

The runner would need a `--two-phase` mode that:
1. Runs phase 1 with the quartermaster prompt and captures the JSON plan
2. Parses the plan to determine which tools to enable
3. Runs phase 2 with the scoped tool set and the plan as the prompt

### Cost model

The quartermaster adds one planning call (~$0.30-0.50 based on our data). If it reduces the executor from 16 calls to 6-8 calls (by eliminating exploration), the total cost could be:

- Plan phase: $0.40
- Execute phase: $0.40 (6 calls vs A's 16)
- Total: $0.80

Compare: A = $1.43, D = $1.05, E = $1.05. If QM achieves $0.80, it's the cheapest condition — and it's fully specified (no computation channel).

### Priority

After the current batch (A-I) completes and results are analyzed. The quartermaster experiment depends on understanding whether the planning phase actually produces useful tool selection, which requires analyzing G and I results (do strategy instructions help?).

### Risk

The quartermaster might over-specify or under-specify the executor's tools. Over-specification: the executor doesn't have a tool it turns out to need. Under-specification: the executor has tools it doesn't use (same as current A). The experiment should measure both — track how often the executor hits a tool boundary it shouldn't have, and how often it has tools it never calls.
