# The Two Products of the Ratchet

*The grade lattice has two axes. The ratchet operates on both. We forgot one and it cost us 32%.*

---

## What happened

We ran an experiment. Same model (Sonnet), same task (fix 13 bugs in a Python codebase), six different tool configurations. The question: does replacing bash with structured tools maintain or improve outcomes?

The baseline: **Condition A** — structured file tools (Read, Edit, Search, Glob) plus a structured test runner (run_tests). No bash. Data channels only. Levels 0-2.

We restricted the world coupling axis aggressively. The agent went from having bash (level 4 — a universal machine that can express any computation) to having specific tools for specific operations (level 0-2 — structured queries with known effect signatures). The framework predicted this should help: supermodularity says restriction has superlinear returns when the decision surface is large.

**It didn't help. It hurt.**

Condition A cost $1.43 per run. Condition D (bash only) cost $1.05. Same outcome — 100% of tests passing. The structured tools were 36% more expensive than the thing they replaced.

We investigated. The problem wasn't the tools themselves — they worked correctly. The problem was *how the agent used them*. With bash, the agent naturally wrote multi-step programs: read everything, diagnose all bugs, fix them in a batch script. With structured tools, the agent made one tool call per turn: read a file, think, read another file, think, make one edit, think, make another edit. Same work, twice the round-trips.

So we built batch tools. `file_edit_batch` — apply multiple edits in one call. `file_read_batch` — read multiple files at once. We told the agent about them in the server instructions.

**The agent ignored them and kept making individual calls.** Cost barely changed.

So we wrote a detailed strategy: "Work in four phases — gather, diagnose, fix, verify. Use file_edit_batch for all fixes." Prescribed the exact workflow.

**The agent followed the prescription rigidly, spending more time on each phase.** Early data suggests it was slower, not faster.

Then we tried one sentence: *"Do not start editing until you understand the full picture."*

**$0.97 per run. The cheapest condition in the entire experiment.** Cheaper than bash. Cheaper than bash plus file tools. Cheaper than batch tools. Cheaper than the detailed strategy. Same tools as A. Same pass rate. One sentence.

---

## What this means

The grade lattice measures two things: **world coupling** (W — what the actor can reach) and **decision surface** (D — how many paths through the computation an input can take).

The ratchet produces two corresponding artifacts:

**Tools** operate on W. Each tool changes what the agent can reach — which files it can read, what queries it can make, what effects it can produce. `file_edit_batch` is a W-axis artifact. `run_tests` is a W-axis artifact. Every MCP server, every sandbox configuration, every structured tool — W-axis. This is what the industry focuses on. This is what we built first.

**Strategy** operates on D — specifically on d_reachable, the portion of the decision surface the agent actually traverses. "Understand before editing" doesn't change which tools exist. It changes which *paths* through the tool space the agent takes. It prunes the path space from "try everything in every order" to "read first, then diagnose, then fix." Same W, dramatically different d_reachable.

We restricted W aggressively (removing bash, adding structured tools) and it hurt. Then we restricted d_reachable gently (one sentence) and it helped more than any tool change. The grade lattice has two axes. We ratcheted one and forgot the other.

---

## The data

| Condition | W change | d_reachable change | Cost | vs baseline |
|---|---|---|---|---|
| **A** (baseline) | Structured tools, no bash | Unrestricted | $1.43 | — |
| **D** (bash only) | Universal machine | Naturally constrained (programs) | $1.05 | -27% |
| **E** (file + bash) | Both | Naturally constrained | $1.01 | -29% |
| **H** (batch tools) | Better structured tools | Unrestricted | ~$1.20 | -16% |
| **G** (strategy) | Better structured tools | Prescribed phases | TBD | TBD |
| **I** (principle) | Same as A | **One sentence constrains paths** | **$0.97** | **-32%** |

A and I have identical W — same tools, same capabilities, same world coupling. The only difference is d_reachable. The principle reduces the number of paths the agent explores without reducing the number of paths *available*. It's not restriction — it's *guidance*. The agent can still do anything A can do. It just doesn't waste tokens on paths that don't contribute to the solution.

---

## Why the principle works and the prescription doesn't

We tested three levels of d_reachable intervention:

1. **No intervention** (A): The agent explores freely. High d_reachable. Many wasted paths (list directories three times, read files one at a time, edit one bug at a time with verification between each).

2. **Full prescription** (G): "Work in four phases. Use file_glob for discovery. Use file_read_batch for reading. Use file_edit_batch for editing. Use run_tests for verification." This constrains d_reachable to a specific path. Early data: the agent follows the prescription but spends more time on each phase, producing higher total cost.

3. **Minimal principle** (I): "Do not start editing until you understand the full picture." This constrains *when* to act but not *how*. The agent chooses its own tools, its own reading order, its own edit strategy. But it front-loads understanding, which eliminates the false starts that inflated A's cost.

The prescription over-constrains. It specifies both *when* and *how*, leaving the agent no room to adapt. The principle constrains only *when*, leaving *how* to the agent's judgment. The judgment is good — the agent naturally selects efficient tool usage when it has enough context to plan.

This is the Taylor/Johannsen principle from Where the Space Lives: "The purpose of specification is to free the unspecifiable to do its work." The principle specifies the transition point (understand → act). Everything within each phase — which tools to use, how to compose them, how many edits to batch — is the unspecifiable work that the agent's trained judgment handles.

Over-specifying the *how* (G) is Taylor measuring the transitions between lathe cuts. Under-specifying the *when* (A) is letting the worker interleave exploration and action without structure. The principle (I) is Taylor's tables for the cuts, freeing Johannsen's expertise for the transitions.

---

## The ratchet's two products

The configuration ratchet essay describes the cycle: explore → capture → crystallize → exploit. Each turn converts a piece of high-ma behavior into low-ma infrastructure.

This is correct but incomplete. The ratchet has two outputs, corresponding to the two axes:

**Tool artifacts** (W-axis): The crystallized tool — `file_edit_batch`, `run_tests`, a Fledgling macro, a blq query. These change what the system can do.

**Strategy artifacts** (d_reachable axis): The crystallized understanding — a CLAUDE.md instruction, an AGENTS.md guideline, a one-sentence principle. These change how the system navigates what it can do.

Both are products of the same ratchet cycle. Both follow the same pattern: discover through high-ma exploration, capture the pattern, crystallize into a specified artifact. The tool artifact is code. The strategy artifact is text. Both are specified, auditable, and improvable.

The revised ratchet: explore → capture → crystallize **tools** AND **strategy** → teach → exploit.

---

## Why bash naturally constrains d_reachable

The experiment's most counterintuitive finding: bash (level 4, Turing-complete, maximal W) produced *lower effective d_reachable* than structured tools (levels 0-2, restricted W).

Why? Because **bash forces you to write a program before executing it.** When the agent writes a Python fix script, it has to:
1. Decide which files to read
2. Decide which edits to make
3. Express all of them in a coherent program
4. Execute the program in one step

Steps 1-3 are *planning*. The agent plans because the tool requires a program, and a program is a plan. The program is the strategy artifact, embedded in the tool call.

Structured tools don't force planning. `file_edit(path, old, new)` takes one edit. The agent can make it without thinking about the next edit. The tool's granularity enables a read → edit → read → edit → read → edit pattern that is locally reasonable at each step but globally inefficient.

The principle "understand before editing" reimplements what bash does cognitively — it forces the agent to plan before acting — without the computation channel. The planning happens in the agent's reasoning, not in a Python script. The output is the same (a sequence of well-chosen edits) but the mechanism is different (principle-guided reasoning vs program-structured tool call).

---

## The hierarchy

The experiment measured three layers of the stack, each more leveraged than the last:

| Layer | What it is | Framework concept | Experiment finding |
|---|---|---|---|
| Model | The weights | Internal ma | Not varied (Sonnet throughout) |
| Tools | What's available | W (world coupling) | Varying tools: -29% to +0% vs baseline |
| **Strategy** | **How to use what's available** | **d_reachable** | **One sentence: -32% vs baseline** |

The cheapest layer to change (one sentence) had the largest effect. The most expensive layer to change (tool infrastructure) had a smaller effect. The framework predicts this through supermodularity: the axes interact, and reducing d_reachable at high W (many tools available) has the largest marginal return.

What the industry focuses on:
- Model selection (layer 1) — extensive benchmarks, model comparisons
- Tool configuration (layer 2) — harness engineering, MCP servers, tool design
- Strategy (layer 3) — CLAUDE.md files, treated as documentation rather than as the most leveraged intervention

The ratchet should prioritize layer 3 first. Not because tools don't matter — they do, especially the tools that provide capabilities bash can't express (FindDefinitions, blq, structured diagnostics). But because strategy is cheaper, faster, and more effective than infrastructure when the tools are already sufficient.

---

*This finding emerged from the experimental program for The Ma of Multi-Agent Systems, March 2026. The experiment was designed to test computation channel effects. The strategy finding was not predicted — it was discovered through the ratchet process itself: observing bash's behavior, identifying the principle, testing it, finding it works better than the tool changes we originally set out to test.*
