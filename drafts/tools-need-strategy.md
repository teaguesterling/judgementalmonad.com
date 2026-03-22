# Tools Need Strategy: The Missing Half of the Ratchet

*A finding from the experimental program, March 2026. To be integrated into the Ma series, Ratchet Fuel, and the experimental findings.*

---

## The observation

We built structured tools to replace bash. The agent used them naively and they cost more. We added batch tools. The agent ignored them. We wrote a detailed four-phase strategy. The agent followed it rigidly, adding overhead. We stated one principle — "understand before editing" — and the agent figured out the rest, producing the cheapest runs in the entire experiment.

The ratchet produces two artifacts:
1. **Tools** — the specified operations (file_edit_batch, run_tests, structured search)
2. **Strategy** — when and how to compose the tools effectively

Crystallizing the tool without crystallizing the strategy is half a ratchet turn. The tool exists but the agent uses it like a worse version of bash, because it doesn't know how to make the tools work together.

## The data

All conditions: same task (fix 13 bugs in a 600-line Python codebase), same model (Sonnet), 100% pass rate.

| Condition | Tools | Instruction | Cost | Calls |
|-----------|-------|-------------|------|-------|
| A (baseline) | Structured + run_tests | Generic | $1.43 | 16.2 |
| D (bash only) | Bash | Generic | $1.05 | 12.0 |
| E (file + bash) | Structured + bash | Generic | $1.01 | 11.4 |
| H (batch tools) | Structured + batch + run_tests | Generic | ~$1.20 | ~13 |
| G (strategy) | Structured + batch + run_tests | 4-phase prescribed | TBD | TBD |
| **I (principle)** | **Structured + run_tests** | **"Understand before editing"** | **$0.97** | **12.2** |

I has the same tools as A. The only difference is one sentence. That sentence is worth 32% cost reduction — more than adding bash (D: 27%), more than adding batch tools (H), more than a detailed strategy document (G).

## How we got there

The instruction wasn't designed from theory. It was reverse-engineered:

1. **Observed** D (bash-only) naturally adopting a read-everything → diagnose-all → fix-in-batch pattern
2. **Asked why** — bash lets you express a whole program, so the agent naturally plans the entire fix before executing
3. **Identified the principle** — "understand before acting" is what bash induces implicitly through its cognitive fit
4. **Tested the principle** without bash, without batch tools, without prescribed phases — just one sentence
5. **Found it works** — and it's cheaper than bash

The principle is a ratchet artifact. Discovery happened through observing the computation channel (bash). Crystallization expressed it as a minimal instruction. The instruction works without the computation channel.

## Why this matters

### For tool design

Building a tool is not enough. The agent needs to know how to use it in context — and "read the tool description" is insufficient. The tool description says *what* the tool does. It doesn't say *when* to use it or *how it composes* with other tools.

file_edit_batch's tool description: "Apply multiple edits across one or more files in a single call. Much more efficient than calling file_edit repeatedly."

The agent read this, understood it, and still made 5 individual file_edit calls. The description tells you *what* it does. It doesn't tell you *when* to use it — specifically, "after you've read all the code and diagnosed all the bugs, express all fixes for each file as a single batch call."

### For the ratchet narrative

The configuration ratchet essay says: "explore → capture → crystallize → exploit." The missing step: **teach**. Between crystallize and exploit, someone has to teach the agent (or the next developer, or the next session) how to use the crystallized artifact effectively. CLAUDE.md files, AGENTS.md files, tool descriptions, system prompts — these are the teaching layer. Without it, the tools are deployed but underused.

The revised ratchet: explore → capture → crystallize → **teach** → exploit.

### For the Ma framework

The series says "which tools matters more than which model." Our experiment adds: "how you use the tools matters more than which tools you have." The hierarchy:

1. Model selection (internal ma — the weights)
2. Tool configuration (configuration lattice — what the Harness grants)
3. **Usage strategy** (how the agent navigates the configured space)

Each layer is more leveraged than the one below it. The industry focuses on layers 1 and 2. Layer 3 is where the most value lives — and it's the cheapest to change (one sentence vs new model vs new tool infrastructure).

## Where to cite

### Ma series

**Post 00 (intro):** Add to the "why this exists" section. Alongside LangChain (52.8% → 66.5%, same model better harness) and Crandall (78% vs 42%): "And within the same harness, a one-sentence strategy instruction reduced costs by 32% — more than any tool configuration change."

**Post 09 (Building With Ma):** Add to design rules. Rule 7: "Teach the strategy, not just the tools. A structured tool without usage guidance is a worse version of the bash command it replaced."

**The Configuration Ratchet:** Add "teach" to the ratchet cycle. The crystallized artifact needs a strategy layer — when to use it, how it composes, what pattern it replaces.

### Ratchet Fuel

**Post 0 (Ratchet Review):** The 7 practical rules should include strategy as distinct from tool selection.

**Post 1 (Fuel):** The failure stream includes *strategy failures* — the agent has the right tools but uses them naively. These are visible in the cost data: high tool-call counts with low progress per call.

**Post 5 (Closing the Channel):** The before/after should include the strategy instruction, not just the tool. "You built the tool. Now teach the agent when to use it."

**Post 8 (Teaching Without Theory):** This entire post is about the teaching layer. The I experiment is the evidence that teaching works — and that less teaching (principle) outperforms more teaching (prescription).

### Experimental findings

Add as Section 10 in pilot-findings.md with the full data and methodology.
