# The Strategy Instruction

*~50 tokens that reshape how the agent navigates its tools — without changing the tools.*

---

## The problem

You gave the agent structured tools: file_read, file_edit, file_search, run_tests. Every tool works correctly. Every operation is auditable. The grade dropped from level 4 (bash) to level 3 (structured). The security posture improved.

Then you measured the cost. It's 22% higher than bash (p<0.05, n=28 vs n=13). The agent uses the tools one at a time — read a file, think, read another file, think, make one edit, think, make another edit. Same work, twice the round-trips. The structured tools are correct. They're just expensive.

## The pattern

Add a short principle instruction to the task prompt that tells the agent *when* to act, not *how*. The instruction reshapes which paths through the decision surface the agent takes (d_reachable) without changing which tools are available (W).

The effective instruction from our experiments (39 words, ~50 tokens):

> *Important: Do not start editing until you understand the full picture. Read the code, run the tests, and identify all the bugs first. Multiple test failures often share a root cause — find the root causes before fixing symptoms.*

Three components:
- **The principle** (6 words): "understand the full picture before editing"
- **Tactical guidance** (15 words): "read the code, run the tests, identify all the bugs first"
- **Diagnostic hint** (18 words): "multiple test failures often share a root cause — find the root causes before fixing symptoms"

## The evidence

### Sonnet (n=24 with instruction vs n=28 without)

| | Without (A) | With (I) | Effect |
|---|---|---|---|
| Pass rate | 82% | **100%** | +18% reliability |
| Mean cost | $1.35 | **$1.08** | -20% cost |
| Output tokens | 49,292 | **36,987** | -25% reasoning overhead |
| Effect size | | d = 0.56 | Medium (trending, p≈0.06) |

### Haiku (n=5 each)

| | Without (A) | With (I) | Effect |
|---|---|---|---|
| Pass rate | **40%** | **100%** | **+60% reliability** |
| Mean cost | $0.69 | $0.66 | Cost neutral |

### Opus (n=13 with instruction vs n=10 without)

| | Without (A) | With (I) | Effect |
|---|---|---|---|
| Pass rate | **100%** | **85%** | **-15% reliability** |
| Mean cost | $1.15 | $1.67 | +45% cost |

## The grade analysis

The strategy instruction operates on d_reachable, not W. Same tools, same world coupling, same computation level. The instruction is context — it enters through the token window and changes which attention paths activate.

- **Without instruction**: The agent explores freely. High d_reachable. Many paths lead to edit-before-understanding, one-at-a-time tool usage, and false starts that waste turns.
- **With instruction**: The agent front-loads understanding. Lower d_reachable. Fewer paths — but the paths it takes are the productive ones.

The instruction adds ~50 tokens to the prompt. The cost reduction comes from eliminating ~13,000 output tokens of wasted reasoning (49K → 37K for Sonnet). The instruction costs ~50 tokens and saves ~13,000. That's a 260:1 return.

## The model-dependent effect

The same instruction has opposite effects at different capability levels:

| Model capability | What the agent already does | What the instruction adds | Net effect |
|---|---|---|---|
| **Low (Haiku)** | Doesn't plan. Starts editing immediately. Wastes turns on wrong approaches. | Forces planning. Prevents premature action. | **+60% reliability** |
| **Medium (Sonnet)** | Plans somewhat. Sometimes explores before understanding. | Reinforces planning. Reduces false starts. | **-20% cost** |
| **High (Opus)** | Plans deeply already. Front-loads understanding naturally. | Amplifies planning. Delays action past the useful point. | **-15% reliability, +45% cost** |

The instruction is a d_reachable constraint. For models with high d_reachable (Haiku explores too much), the constraint prunes wasteful paths. For models with already-focused d_reachable (Opus plans deeply), the constraint over-prunes — removing productive action paths alongside wasteful ones.

**Implication**: Strategy instructions must be model-aware. The Quartermaster pattern addresses this.

## Implementation

Add the instruction to the task prompt, CLAUDE.md, or system prompt. No tool changes. No infrastructure.

For model-aware deployment:
```yaml
strategy:
  haiku: "Do not start editing until you understand the full picture. Read the code, run the tests, and identify all the bugs first. Multiple test failures often share a root cause — find the root causes before fixing symptoms."
  sonnet: "Do not start editing until you understand the full picture. Read the code, run the tests, and identify all the bugs first. Multiple test failures often share a root cause — find the root causes before fixing symptoms."
  opus: null  # Opus plans naturally. Adding the instruction hurts.
```

## The anti-pattern: over-specification

A detailed strategy prescription — "Work in four phases: 1) Use file_glob to find files, 2) Use file_read_batch to read all source and test files, 3) Use file_edit_batch to apply fixes, 4) Use run_tests to verify" — costs +56% over baseline (Condition G, $2.06). The agent writes verbose phase-by-phase analysis, complying with the prescription instead of solving the problem.

The principle tells the agent *when* to act. The prescription tells it *how*. The *how* is overhead. The agent's own judgment about *how* — which tools, which order, how many edits per call — is better than the prescription. The purpose of the instruction is to free that judgment by constraining the timing.

This is the Taylor/Johannsen principle from the Ma series: the purpose of specification is to free the unspecifiable to do its work. The instruction specifies the transition point (understand → act). Everything within each phase is the agent's business.

## The ratchet connection

This pattern is a ratchet product. It was discovered by:
1. Observing bash's behavior (D: the agent writes fix scripts — planning implicitly)
2. Asking why (bash forces program-writing, which forces planning)
3. Identifying the principle (planning before acting is what makes bash efficient)
4. Testing the principle without bash (I: same efficiency, lower grade)

The instruction is the crystallized strategy — the second product of the ratchet alongside the tools. Building tools without teaching the strategy is half a ratchet turn.
