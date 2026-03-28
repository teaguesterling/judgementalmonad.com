# Session 3 Intent: The Ratchet Applied to Ourselves

## Two tasks, in order

### Task 1: Why do we use bash when structured tools are available?

This session has Fledgling, blq, and jetsam as MCP tools — and used bash for almost everything. Analyze our own tool call patterns:

1. Query this session's conversation log (or recent sessions) for tool usage
2. Categorize every bash call: what did it do? Does a structured equivalent exist in Fledgling/blq/jetsam?
3. For each bash pattern with a structured equivalent: why wasn't the structured tool used?
   - Agent doesn't know the tool exists?
   - Tool interface doesn't match the operation?
   - Bash composes better (multiple operations in one call)?
   - Habit / training bias?
4. Produce a ratchet candidates list: bash patterns → structured tool promotions

This is the experiment's discovery phase applied to our own workflow. The observation that E (file tools + bash) is the most efficient Sonnet configuration may explain why this session behaves the same way.

### Task 2: Which combinators would address the actual gaps?

From Task 1's analysis, identify where bash wins because of *composition*, not capability:
- `git add -A && git commit -m "..."` → `sequence(jetsam.save, jetsam.status)`?
- `python3 -c "import json; ..."` → needs a data transform tool?
- `grep X | head -5` → needs pipe combinator?

Design the combinators that would close the composition gap. Ground them in the actual bash patterns from Task 1, not in theory.

Reference: `drafts/tool-call-combinators.md` has the theoretical design. Task 2 validates which of those are actually needed.

## Context to read

- `experiments/pilot-findings.md` — the E finding (why file+bash wins)
- `drafts/tool-call-combinators.md` — combinator theory
- `drafts/the-two-products.md` — W/D coupling (tools shape cognitive patterns)
- This session's conversation log (for Task 1 analysis)

## The meta-point

We are the experiment. The same model (Claude), the same tools (Fledgling, blq, jetsam, bash), the same finding (bash wins on cognitive fit). The ratchet should turn on our own infrastructure, not just on synthetic codebases.
