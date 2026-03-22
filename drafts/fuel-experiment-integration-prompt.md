# Integration Prompt: Experimental Findings for Ratchet Fuel

*Give this to the Fuel authoring session so it can incorporate the experimental results.*

---

## Before you start

Read these files:
1. `drafts/the-two-products.md` — The central finding
2. `drafts/tools-need-strategy.md` — The "teach" step in the ratchet
3. `drafts/external-evidence-crandall.md` — Crandall's harness comparison and how to cite it
4. `experiments/pilot-findings.md` — Full experimental data and analysis

## What the experiments found

We ran a controlled experiment: same model (Sonnet), same task (fix 13 bugs in a 600-line Python codebase), varying tool configurations and instructions. Key results:

### The data

| Condition | What it has | Cost | Key insight |
|---|---|---|---|
| A (structured tools) | file tools + run_tests | $1.43 | Baseline — structured tools only |
| D (bash only) | bash | $1.05 | Bash is 27% cheaper — it naturally batches |
| E (file + bash) | both | $1.01 | Best tool mix — Claude Code's design |
| I (one-sentence principle) | file tools + run_tests | **$0.97** | **Cheapest — just "understand before editing"** |

### Three key findings

**1. The ratchet has two products.** Tools (W axis) and strategy (d_reachable). We built tools and forgot strategy. The strategy mattered more.

**2. Bash's advantage is cognitive, not computational.** Bash forces you to write a program before executing it. Writing a program IS planning. Structured tools allow edit-by-edit exploration without planning. One sentence ("understand before editing") reimplements what bash does cognitively, without the computation channel.

**3. The hierarchy: model < tools < strategy.** Each layer is more leveraged and cheaper to change. The industry focuses on model and tool selection. Strategy (CLAUDE.md files, principles, usage guidance) had the largest measured effect.

### Anti-patterns discovered

- **run_tests as a separate tool** added round-trip overhead without adding diagnostic value. The agent runs pytest just fine through bash. Wrapping it in a structured tool added a tool call boundary. Conditions without run_tests (D, E) were cheaper.
- **file_edit_batch** was built and the agent ignored it. The tool description says "more efficient" but the agent doesn't change its approach just because a batch tool exists. It needs the strategy instruction.
- **Detailed strategy prescription** (four-phase plan with tool guidance) was slower than the one-sentence principle. Over-specification constrains the agent without improving outcomes.

## Where to integrate in Fuel

### Post 0 (Ratchet Review)
Add to the practical rules: "Which tools matters more than which model. How you use them matters most of all." Cite the I result as evidence.

### Post 1 (Fuel)
The failure stream includes *strategy failures* — the agent has the right tools but uses them naively. These show up as high tool-call counts with low progress per call. A run_tests call that returns "13 failed" followed by five individual file_edit calls is a strategy failure. The fix isn't a better tool — it's a principle: understand before editing.

### Post 2 (The Two-Stage Turn)
The ratchet cycle should include "teach" between crystallize and exploit. The crystallized tool needs a strategy layer. `file_edit_batch` without "batch your edits" is half a ratchet turn.

### Post 3 (Where the Failures Live)
The placement principle applies to cognitive resource, not just tool access. "Understand before editing" places the agent's *attention* on diagnosis before action. That's a d_reachable constraint — it doesn't remove tools, it constrains which paths the agent takes through the tool space.

### Post 4 (The Failure-Driven Controller)
The modes essay describes which tools each mode has. Add: each mode also needs a *strategy instruction* — one sentence that tells the agent how to approach work in that mode. Debug mode: "identify all failures before proposing fixes." Implementation mode: "batch your changes by file." Review mode: "read everything before forming an opinion."

### Post 5 (Closing the Channel)
The before/after for a ratchet turn should include:
- Before: bash command pattern (the discovery)
- After: structured tool (the crystallization)
- **Also after: one-sentence strategy instruction (the teaching)**

Without the instruction, the tool is deployed but underused. With it, the tool is cheaper than bash. The instruction is the most cost-effective artifact in the ratchet.

### Post 8 (Teaching Without Theory)
This entire post is about the teaching layer. The I experiment is the evidence. Key points:
- Less teaching is more (principle beats prescription)
- The principle should specify *when to act*, not *how to act*
- Teaching is the cheapest intervention ($0 infrastructure cost)
- Teaching compounds with tools (I's principle + A's tools = cheaper than D's bash)

### Post 10 (Ratchet Metrics)
Add a metric: **strategy effectiveness ratio** — cost per run with strategy instruction / cost per run without. If this ratio is < 1, the instruction is earning its keep. For our experiment: I/A = 0.68 (the instruction saves 32%). Track this ratio over time — if it degrades, the strategy needs updating.

## Voice note

These findings emerged from doing the work, not from theorizing about it. The Fuel voice — direct, building-from-failure — fits naturally. "We built the tools. They cost more than bash. Then we added one sentence to the prompt and it cost less than bash. Here's what we learned."

Don't oversell. The experiment is n=5 per condition on one task on a 600-line codebase. The findings are suggestive, not definitive. Frame them as "here's what we measured" not "here's what's true." The Ma series values being precise enough to be wrong.
