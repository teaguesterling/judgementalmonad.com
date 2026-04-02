# Tool-Call Combinators

*Compose structured tool calls without crossing the computation channel boundary.*

---

## The problem

Bash beats structured tools on cost because it packs multi-step operations into single calls. A Python fix script reads a file, applies five edits, and writes it back — one tool call. Structured tools make five `file_edit` calls — five round-trips, five context re-sends.

The overhead is structural: each tool call is a turn boundary. The Harness re-sends the full conversation context on every turn. Five calls with 50K context = 250K tokens re-sent. One call = 50K tokens.

## The pattern

Combinators compose tool calls at the Harness level — no new computation channel, no executable specification, no bash. The Harness executes the composition deterministically.

### First-order combinators

**`gather`** — collect named results from parallel calls:
```json
{
  "combinator": "gather",
  "calls": {
    "source": {"tool": "file_read", "args": {"path": "src/tokenizer.py"}},
    "tests": {"tool": "file_read", "args": {"path": "tests/test_tokenizer.py"}},
    "status": {"tool": "run_tests", "args": {}}
  }
}
```
Returns `{"source": "...", "tests": "...", "status": "..."}` in one round-trip. The agent's preparation phase (read source, read tests, check status) becomes one turn instead of three.

**`for_each`** — apply a template over items:
```json
{
  "combinator": "for_each",
  "items": {"tool": "file_glob", "args": {"pattern": "src/**/*.py"}},
  "template": {"tool": "file_search", "args": {"pattern": "getattr", "path": "{item}"}}
}
```
Search for `getattr` in every Python file. One turn. The Harness fills the `{item}` holes.

**`pipe`** — output of A feeds into B:
```json
{
  "combinator": "pipe",
  "stages": [
    {"tool": "file_glob", "args": {"pattern": "src/**/*.py"}},
    {"tool": "file_read_batch", "args": {"paths": "{result}"}}
  ]
}
```
Find all Python files, then read them all. One turn.

### Second-order combinators

**`try_and_check`** — do A, then verify with B:
```json
{
  "combinator": "try_and_check",
  "do": {"tool": "file_edit_batch", "args": {"edits": [...]}},
  "check": {"tool": "run_tests", "args": {}}
}
```
Edit and verify in one turn. The edit-test cycle compressed from 2 turns to 1.

**`scope`** — run in isolation with rollback:
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
The Harness snapshots, runs the inner sequence, reverts on failure. Safe exploratory editing without the computation channel.

**`annotate`** — attach intent and observations:
```json
{
  "combinator": "annotate",
  "intent": "Fix the string quoting bug",
  "hypothesis": "The tokenizer includes quote chars in the value",
  "do": {"combinator": "try_and_check", "do": {...}, "check": {...}}
}
```
The AIDR pattern: every operation carries metadata about *why* it's being done. The intent travels with the operation through the Harness.

## The grade analysis

Every combinator stays in the specified band:

| Combinator | Monad operation | Grade of composite |
|---|---|---|
| gather | Product in Kleisli | Join of components |
| for_each | Traverse | Join of generator + template |
| pipe | Kleisli composition | Join of stages |
| try_and_check | Bind with validation | Join of do + check |
| scope | Bracket / local | Join of inner + rollback |
| annotate | Writer layer | Same as inner (metadata is data, not code) |

The composite's grade is the join of its components' grades. Combinators over data-channel tools stay in the data channel. The Harness is transparent at every step.

## What this would buy

The pre-ratchet A condition used 28 turns and 16 calls. With combinators:

```
Current:     list, list, list, run_tests, read, read, read, read, edit, edit, edit, edit, edit, run_tests, write
             = 15 calls, 28 turns

With combinators: gather({files: glob, tests: run_tests}),
                  try_and_check(do: edit_batch, check: run_tests),
                  write
                  = 3 calls, ~8 turns
```

## Implementation status

Theoretical. The combinator design is in `drafts/tool-call-combinators.md`. No MCP server implementation exists yet. The experiment showed that `file_edit_batch` (a simple first-order combinator) wasn't used by the agent — suggesting that combinators need the Strategy Instruction pattern (pattern 2) to be effective. The agent needs to know *when* to batch, not just *that it can*.

## The open question

Do agents naturally use combinators, or do they need the Strategy Instruction to change their approach? Our experiment suggests the latter: `file_edit_batch` was available but ignored until the principle instruction changed the agent's cognitive pattern. Combinators may need to be paired with strategy to be effective.
