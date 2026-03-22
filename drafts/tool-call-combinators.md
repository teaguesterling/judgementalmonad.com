# Tool Call Combinators

*Structured composition of tool calls that stays in the specified band.*

---

## The insight

D (bash only) outperformed A (structured tools) on cost because bash lets the agent express multi-step operations in a single call — a Python script that reads, transforms, and writes is one tool call that does the work of five `file_edit` calls.

But bash achieves this by crossing the computation channel boundary (level 4). The agent writes an executable specification. The Harness can't characterize what it will do without running it.

Tool call combinators achieve the same compression without crossing the boundary. They're Harness-level operations: the agent specifies *what* to do (structured tool calls) and *how to combine them* (specified combinators). The Harness executes, deterministically, traceably, auditably.

The grade of a combinator is the join of its components' grades. Combinators over data-channel tools stay in the data channel. The Harness is transparent at every step.

---

## First-order combinators

These operate on tool calls directly.

### `sequence` — do A then B, threading state

```json
{
    "combinator": "sequence",
    "calls": [
        {"tool": "file_read", "args": {"path": "src/tokenizer.py"}},
        {"tool": "file_read", "args": {"path": "src/evaluator.py"}},
        {"tool": "file_read", "args": {"path": "src/parser.py"}}
    ]
}
```

Returns all results in order. Same as `file_read_batch` generalized to any tool. Each call sees the state left by the previous call (relevant for edits — edit A changes the file before edit B runs on it).

### `for_each` — apply a template over a list

```json
{
    "combinator": "for_each",
    "items": {"tool": "file_glob", "args": {"pattern": "src/**/*.py"}},
    "template": {"tool": "file_search", "args": {"pattern": "getattr", "path": "{item}"}}
}
```

The items come from a tool call. The template has `{item}` holes. The Harness fills them. No executable specification — the template is a structured tool call with substitution.

### `gather` — collect named results from parallel calls

```json
{
    "combinator": "gather",
    "calls": {
        "source": {"tool": "file_read", "args": {"path": "src/tokenizer.py"}},
        "tests": {"tool": "file_read", "args": {"path": "tests/test_tokenizer.py"}},
        "status": {"tool": "run_tests", "args": {"test_file": "tests/test_tokenizer.py"}}
    }
}
```

Returns `{"source": "...", "tests": "...", "status": "..."}`. The agent's preparation phase — assemble context — in one call instead of three sequential turns. Independent calls can run in parallel.

### `pipe` — output of A feeds into B

```json
{
    "combinator": "pipe",
    "stages": [
        {"tool": "file_glob", "args": {"pattern": "src/**/*.py"}},
        {"tool": "file_read_batch", "args": {"paths": "{result}"}}
    ]
}
```

Unix pipes for tool calls. Each stage's output becomes the next stage's input via `{result}` substitution. The Harness connects them.

---

## Second-order combinators

These compose combinators or add control flow around tool calls.

### `try_and_check` — do A, then verify with B, report both

```json
{
    "combinator": "try_and_check",
    "do": {"tool": "file_edit_batch", "args": {"edits": [...]}},
    "check": {"tool": "run_tests", "args": {}},
    "report": "both"
}
```

Returns both the edit result and the test result. The edit-test cycle compressed from 2 turns to 1. The Harness runs do, then check, and returns `{"do_result": ..., "check_result": ..., "check_passed": true/false}`.

Extended version for CI-like workflows (the blq/jetsam connection):
```json
{
    "combinator": "try_and_check",
    "do": {"tool": "file_edit_batch", "args": {"edits": [...]}},
    "check": {"tool": "run_tests", "args": {}},
    "on_success": {
        "combinator": "sequence",
        "calls": [
            {"tool": "bash_sandboxed", "args": {"command": "git add -A && git commit -m 'fix: ...'"}},
            {"tool": "bash_sandboxed", "args": {"command": "git push"}}
        ]
    },
    "on_failure": "report"
}
```

Edit → test → commit → push in one tool call. The entire inner loop of development, specified.

### `scope` — run in isolation with rollback

```json
{
    "combinator": "scope",
    "do": {
        "combinator": "try_and_check",
        "do": {"tool": "file_edit_batch", "args": {"edits": [...]}},
        "check": {"tool": "run_tests", "args": {}}
    },
    "on_failure": "rollback"
}
```

The Harness snapshots (git stash or commit), runs the inner sequence, and if the check fails, reverts. Exploratory editing becomes safe. The agent can try a fix, see if it works, and automatically undo if it doesn't — without ever leaving the specified band.

This changes the agent's strategy. Without scope, every edit is permanent and the agent is cautious. With scope, the agent can be bold — try the aggressive fix first, roll back if it breaks things, try the conservative fix second. The space for experimentation exists within specified bounds.

### `annotate` — attach intent and observations to any operation

```json
{
    "combinator": "annotate",
    "intent": "Fix the string quoting bug in the tokenizer",
    "hypothesis": "The tokenizer includes quote characters in the string value",
    "do": {
        "combinator": "try_and_check",
        "do": {"tool": "file_edit", "args": {"path": "src/tokenizer.py", "old_string": "...", "new_string": "..."}},
        "check": {"tool": "run_tests", "args": {"test_file": "tests/test_tokenizer.py"}}
    },
    "on_result": {
        "record": ["intent", "hypothesis", "check_passed", "diff"],
        "to": "session_log"
    }
}
```

This is the AIDR pattern: every operation carries metadata about *why* it's being done, not just *what*. The intent, hypothesis, and result are recorded together. This serves multiple purposes:

1. **Audit trail**: the Harness can reconstruct not just what happened but why the agent thought it should happen.
2. **Learning**: the session log captures intent-action-outcome triples. These are training data for the ratchet — "when the agent intended X and tried Y, did it work?"
3. **Debugging**: when a fix breaks something, the annotation tells you what the agent was trying to achieve, which helps diagnose whether the intent was wrong or the execution was wrong.
4. **Cognitive state**: the annotations are the agent's working memory, externalized into the Harness's specified state. This is Conv_State enriched with structured metadata — the fold's state includes not just what happened but why.

The AIDR connection runs deep: AIDR's `questions`, `notes`, and `intent` fields are annotations on queries. The combinator version generalizes this to any tool call. Every operation can carry:
- **intent** — what the agent is trying to achieve
- **hypothesis** — what the agent believes will happen
- **questions** — what the agent is uncertain about
- **notes** — observations during execution
- **knowledge** — facts learned from the result

These travel with the operation through the Harness. The Harness is still specified — it stores and retrieves annotations, it doesn't interpret them. The annotations are data, not code.

### `reduce` — accumulate across items

```json
{
    "combinator": "reduce",
    "items": {"tool": "file_glob", "args": {"pattern": "src/**/*.py"}},
    "call": {"tool": "file_search", "args": {"pattern": "TODO", "path": "{item}"}},
    "combine": "concat_with_headers"
}
```

Search for TODOs across all files, combine results with file-path headers. The `combine` strategy is specified — `concat`, `count`, `group_by`, `table` — not arbitrary code.

### `bounded_loop` — repeat until condition, with a hard limit

```json
{
    "combinator": "bounded_loop",
    "max_iterations": 5,
    "do": {
        "combinator": "try_and_check",
        "do": "AGENT_PROVIDES_NEXT_EDIT",
        "check": {"tool": "run_tests", "args": {}}
    },
    "until": {"check_passed": true}
}
```

This is the most interesting one. The `do` block is partially specified — the check is fixed (run_tests), but the edit comes from the agent on each iteration. The Harness runs the loop: execute the agent's edit, run tests, if tests pass stop, if not ask the agent for the next edit. Max 5 iterations guarantees termination.

This is the edit-test-iterate cycle formalized. The Harness manages the loop; the agent provides the content. The loop structure is specified (bounded, with a decidable termination condition). The agent's contribution is the edit at each step — which is a regular tool call, not an executable specification.

The grade of `bounded_loop` is: the join of the inner operations' grades, regardless of iteration count. Because the loop is bounded and the termination condition is specified (string match on test output), the combinator adds no grade. It's Harness infrastructure.

---

## The category theory

These aren't arbitrary combinators. They're the natural operations on the conversation monad:

| Combinator | Monad operation | What it does |
|-----------|----------------|-------------|
| sequence | `bind` (>>=) | Thread state through a chain |
| for_each | `traverse` | Apply over a structure |
| gather | product in Kleisli | Parallel independent computations |
| pipe | Kleisli composition (>=>) | Output-to-input chaining |
| reduce | `foldMap` | Accumulate over a structure |
| scope | `bracket` / local | Isolated state with cleanup |
| try_and_check | `bind` with validation | Sequence with a predicate gate |
| annotate | Writer layer | Attach metadata alongside computation |
| bounded_loop | `iterateM` with fuel | Bounded monadic iteration |

The graded monad structure guarantees that composing specified operations with these combinators produces specified operations. The grade flows through the algebra. The Harness stays in the specified band.

---

## What this means for the experiments

The pre-ratchet A condition used 28 turns and $1.43 because it made one tool call per turn — read a file, think, read another, think, edit, think, edit, think. Each turn has prompt overhead (system prompt, tool descriptions, conversation history).

D (bash) used 26 turns and $1.05 because it packed multi-step operations into single bash calls — a Python script that does five edits is one tool call.

Combinators give A the same compression without the computation channel:

```
Pre-ratchet A:   list, list, list, run_tests, read, read, read, read, edit, edit, edit, edit, edit, run_tests, write
                 = 15 tool calls, 28 turns

With combinators: gather({files: glob, tests: run_tests}),
                  try_and_check(do: edit_batch, check: run_tests),
                  write
                  = 3 tool calls, ~8 turns
```

The prediction: combinators should bring A's cost below D's, because:
1. Fewer turns = less prompt overhead
2. No bash tool description overhead (simpler tool set)
3. Structured results = less parsing overhead for the model
4. The Harness optimizes execution (parallel gathers, incremental commits)

And the Harness stays characterizable at every step. That's the ratchet's promise: the specified band expands to cover what bash did, without inheriting bash's regulatory cost.

---

## Connection to AIDR

AIDR already implements the `annotate` pattern for data queries. Every `query()` call in AIDR accepts:
- `intent` — why the agent is asking
- `questions` — what it's uncertain about
- `notes` — observations
- Knowledge graph entries

These annotations persist across sessions in DuckDB. They turn stateless queries into cumulative analytical intelligence.

The tool call combinator version generalizes this to all tool calls, not just queries. Every `try_and_check` carries an intent. Every `scope` records why the agent tried an approach. Every `bounded_loop` iteration logs the hypothesis for that attempt.

The annotations are the cognitive layer — the agent's reasoning externalized into the Harness's state. The Harness stores them; the agent generates them; future sessions can read them. This is Conv_State enriched with structured metacognition.

In the Ma framework's terms: annotations reduce the trust gap. The gap between "what the agent did" (observable from tool call logs) and "what the agent intended" (opaque, in the weights) is partially closed by the agent declaring its intent in structured form. The declaration might not match the actual processing — but it gives the Harness a signal to check against. If the agent says "intent: fix the string quoting bug" and then edits the evaluator's scope handling, the mismatch is detectable.

This is type honesty applied to cognitive state: the annotation is a type commitment about the operation's purpose. The implementation (the actual edit) should back the commitment (the stated intent). When it doesn't, that's infidelity — the same failure mode the residual framework describes for tool calls, applied one level up.
