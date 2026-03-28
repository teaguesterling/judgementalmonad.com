# The Experiment That Proved Us Wrong

*We tried to lock down a coding agent without increasing costs. We failed — then one paragraph changed everything.*

---

## The question

This started as a security exercise.

The configuration ratchet claims that you can lock down a system — replace computation channels with data channels, close the specified band, make every operation characterizable — without sacrificing quality or increasing costs. We wanted to test that claim on the most common coding activity: an agent fixing bugs in a codebase. Can we remove bash, replace it with structured tools the Harness can fully characterize, and get the same work done?

The framework predicts yes. Restriction should have superlinear returns. Replace a computation channel (bash — level 4, Turing-complete) with data channel tools (structured read, edit, search — levels 0-2), and the system should become cheaper to regulate, easier to audit, and at least as productive. The specified band should expand. The grade should drop. The ratchet should turn.

We built the tools. We ran the experiment. We measured.

## What we expected

Structured tools (Condition A) should outperform bash (Condition D) on cost while matching on quality. The tools close the computation channel. The Harness can characterize every operation. The trust gap shrinks. The model's inference budget is freed from shell mechanics and output parsing. Restriction pays for itself.

## What we got

| Condition | n | Tools | Cost per run | Pass rate |
|---|---|---|---|---|
| A (structured tools) | 28 | file_read, file_edit, file_search, run_tests | **$1.35** | 82% |
| D (bash only) | 13 | bash_sandboxed | **$1.03** | 100% |

Bash was 24% cheaper (p<0.05, d=0.80) and more reliable. The structured tools that were supposed to free the model's inference budget instead *increased* the inference cost — and occasionally failed the task entirely.

We were wrong.

## Why we were wrong

We looked at *what* the agent did and crystallized it into tools. Bash runs `grep -r`? Build `file_search`. Bash runs `cat`? Build `file_read`. Bash edits files with `sed`? Build `file_edit`. Each tool matched a bash operation. Each was structurally equivalent. Each was a lower grade. The channel closed.

We didn't look at *how* the agent used bash.

When the agent had bash, it wrote Python scripts. Not one-line commands — 50-line programs that read a file, applied all five fixes, and wrote it back. One tool call. One round-trip. Everything planned before execution.

When the agent had structured tools, it called `file_edit` five times. One fix per call. Each call was a separate turn. Each turn re-sent the full conversation context. Five round-trips where bash needed one.

We captured *what* was being done (read, search, edit) and crystallized each operation. We didn't capture *how* it was being done (plan everything, execute in batch). The tools replicated bash's operations at the atomic level. They didn't replicate bash's workflow at the compositional level.

## The cognitive insight

Bash doesn't just let you do things. It lets you *think in programs*.

A bash script is a plan. Writing `read → fix → fix → fix → fix → write` as a Python program forces you to plan all five fixes before executing any of them. The tool's interface — "give me a program" — is a cognitive forcing function that induces planning.

`file_edit` is a scalpel. Its interface — "give me one old string and one new string" — induces incremental editing. Fix one thing. Check. Fix the next. Check. Each fix is locally reasonable. The sequence is globally inefficient.

The computation channel's advantage wasn't computation. It was *cognition*. Bash thinks in programs. Structured tools think in operations. Programs are plans. Operations are steps.

## The 50-token fix

We asked: what makes bash induce planning? Answer: you have to understand the whole problem before writing the script. You can't write a fix script for bugs you haven't diagnosed yet.

So we told the structured-tools agent the same thing. One paragraph, 39 words, roughly 50 tokens:

> *Important: Do not start editing until you understand the full picture. Read the code, run the tests, and identify all the bugs first. Multiple test failures often share a root cause — find the root causes before fixing symptoms.*

The core principle is six words: "understand the full picture before editing." But the effective instruction includes tactical guidance ("read the code, run the tests") and a diagnostic hint ("failures share root causes"). All of it mattered — we didn't test the six-word version separately.

No new tools. No bash. Just the paragraph.

We also tried the opposite: a detailed four-phase strategy prescription telling the agent exactly which tools to use in which order. And batch tools with improved tool descriptions teaching the agent about efficient patterns.

| Condition | n | Instruction | Cost | Change from baseline | Output tokens |
|---|---|---|---|---|---|
| **G** (four-phase strategy) | 5 | Detailed prescription (~200 tokens) | **$2.06** | **+56%** | 90,702 |
| **H** (batch tools + guidance) | 5 | Tool-specific guidance (~100 tokens) | $1.86 | +41% | 75,919 |
| A (structured, no guidance) | 22 | Generic | $1.32 | — | 49,292 |
| F (run_tests + bash) | 13 | Generic | $1.17 | -11% | 39,372 |
| **I (structured + 50 tokens)** | 24 | **Principle + guidance** | **$1.11** | **-16%** | **36,987** |
| D (bash only) | 13 | Generic | $1.03 | -22% | 30,104 |
| **E (file tools + bash)** | 13 | Generic | **$0.98** | **-26%** | **27,731** |

The spectrum: more instruction = more cost. G (detailed prescription, $2.06) is the most expensive. E (file tools + bash, no instructions about strategy, $0.98) is the cheapest. The principle instruction (I, $1.11) lands between bash (D, $1.03) and the baseline (A, $1.32) — a 16% improvement over A, roughly tied with D.

The early pilot (n=5) suggested I was 32% cheaper than A. At n=24, it's 16%. The effect is real — d=0.49, medium — but smaller than the pilot indicated. The pattern held: the principle helps. The magnitude didn't.

What did hold: **over-specification is consistently worse.** G ($2.06) and H ($1.86) are the two most expensive conditions — worse than having no strategy at all. The detailed prescription generated 3× the output tokens of I because the agent wrote verbose phase-by-phase analysis. The principle told the agent *when* to act. The prescription told it *how*, and the how was overhead.

What surprised us: **E (file tools + bash) is the cheapest condition.** E uses structured file tools for reading, searching, and editing — and bash for exactly one thing: running pytest. Every bash call across 13 runs was `python -m pytest`. No scripts, no `cat`, no `grep`. The agent naturally selected the right tool for each job: structured tools for file operations, bash for execution. This is Claude Code's design — and it's the most efficient configuration we tested.

## Which 50 tokens

Fifty tokens are cheap to deploy. Knowing *which* 50 tokens required the full experiment.

We didn't start with "understand first." We started with "close the computation channel" — the security exercise. That failed on cost (A: +22% over bash, confirmed at p<0.05). So we analyzed *why* bash was cheaper and discovered the cognitive forcing function. Then we tried to replicate it with a detailed prescription (G: +56% — the most expensive condition). Then we stripped the prescription back to its core principle (I: -16% vs A).

The discovery path was: ratchet theory → observation → characterization → security improvement → experiment → cognitive insight → strategy distillation. Each step depended on the previous. The 50 tokens are the residue of that entire process.

This matters because "just add a principle instruction" is the wrong takeaway. The right takeaway is: the ratchet's observation phase — watching how the agent works, not just what it does — is where the value is created. The 50 tokens are what you extract. The observation is what tells you which 50 tokens to extract. G proves that guessing wrong about the strategy costs more than having no strategy at all.

## What we actually found

We set out to test whether closing the computation channel improves outcomes. The answer is nuanced:

**Closing the channel alone hurts.** Removing bash and replacing it with structured tools (A) costs 22% more (p<0.05). The tools work correctly — every operation is specified, auditable, characterizable. But the agent uses them one at a time, burning inference budget on round-trips that bash handles in a single script.

**The channel wasn't the variable.** We thought we were measuring the effect of the computation channel (W axis — what tools are available). We were actually measuring the effect of the *cognitive pattern* the channel induces (d_reachable — which paths through the decision surface the agent takes). The channel is the mechanism. The pattern is the cause.

**Fifty tokens restore what the channel provided.** The principle "understand before editing" changes d_reachable without changing W. The agent has exactly the same tools. It takes fewer paths through the same space. The paths it takes are the ones that bash would have induced — read everything, diagnose everything, then act. The principle is a specified substitute for the computation channel's cognitive side effect.

**The axes are coupled.** Post 6 argues that d_reachable is downstream of W — the tools you provide shape the paths the agent takes. This experiment shows the mechanism: tool interfaces are cognitive forcing functions. Bash's "give me a program" induces planning. `file_edit`'s "give me a replacement" induces incrementalism. Strategy instructions reshape the paths without changing the tools. You can't optimize W and d_reachable independently — and the [revised Rule 7](../ma/09-building-with-ma) develops the practical implications.

## Back to security

Remember: we started with a security question. Can we lock down a coding activity without sacrificing quality or increasing costs? The answer turns out to be yes — but not the way we expected.

The 50-token version is also the most *secure* configuration.

To understand why, consider what bash actually is in production. Our experiment's Condition D ran bash inside bubblewrap — sandboxed to the workspace, no network, isolated processes. Even sandboxed, it's a level 4 computation channel (level 7 without `--die-with-parent`, which we had to add after discovering that forked processes survived the tool call).

Default Claude Code bash — what ships in production — is **level 8**. No sandbox. The agent can read any file the user can, write anywhere, install packages (level 5), create executable scripts (level 6), spawn persistent background processes (level 7), and edit `CLAUDE.md` and `.mcp.json` — modifying its own regulatory parameters (level 8). The permission gate (the Principal approving each bash call) is the only thing between the tool and level 8 effects. That gate is a human reading a command string and deciding if it's safe — doing manually, for every call, what Rice's theorem says can't be automated.

With `--dangerously-skip-permissions` — the configuration used for CI, batch processing, and autonomous agents — the gate is gone. Level 8, no filter.

Condition I is a level 3 system. The agent *writes* code (via `file_edit` — level 3, mutation) and *verifies* it (via `run_tests` — level 1 interface, sandboxed execution). The critical structural property: **the agent cannot close the write-execute loop on its own.** It writes through one tool (structured, logged, auditable) and the only execution path goes through a sandbox it doesn't control.

```
D (bash):    write + execute in one opaque tool call     → level 7
I (struct):  write (file_edit) | execute (run_tests)     → level 3
                                    ↑
                            sandboxed: read-only workspace,
                            no network, isolated processes
```

The separation is what keeps I below level 4. Level 4 is "the agent generates executable specification and the tool executes it." In I, the agent generates code, but the execution goes through `run_tests` — a fixed program (pytest) that the agent can't configure, running in a sandbox the agent can't escape. The agent doesn't choose the interpreter, the flags, the sandbox bounds, or whether child processes are allowed. It submits a structured query ("run the tests") and gets a structured result ("13 failed, 35 passed").

The analogy: a SQL query is level 1. The database engine is Turing-complete. But the interface is structured and the effects are bounded by access controls. The engine's internal complexity doesn't leak through the interface. `run_tests` is a query over the test suite. Pytest's internal complexity is bounded by the sandbox.

What the Harness can decide about each condition's tool calls *before execution*:

| Property | Condition I | Condition D |
|---|---|---|
| What files will be read? | Yes (path in args) | Undecidable |
| What files will be written? | Yes (path in args) | Undecidable |
| Will it access the network? | No (by construction) | No (bwrap) |
| Will it spawn subprocesses? | No (run_tests is sandboxed) | Undecidable |
| Will it terminate? | Yes (timeout) | Yes (timeout) |
| What are the effects? | Enumerable | Uncharacterizable |

I is characterizable on every dimension. D is characterizable only on the bwrap-guaranteed dimensions (network, termination). The difference isn't a matter of degree — it's the difference between decidable and undecidable properties. The Harness can write an exhaustive policy for I. It structurally cannot for D.

In our experiment, D was sandboxed — level 4 with `--die-with-parent`. In production, bash is level 8. The grade gap between I (level 3) and production bash (level 8) is five levels of the computation taxonomy. The permission gate that the Principal applies to each bash call — reading the command, deciding if it's safe — is a human doing System 3 work on every turn. Condition I eliminates that work entirely. Every tool call is self-evidently characterizable. The Principal doesn't need to evaluate it.

Cheaper, simpler, more auditable, and provably lower grade. Not by adding more infrastructure — by separating write from execute and sandboxing the execute path.

## The two products of the ratchet

The framework defines *ma* on two axes: world coupling (W — what the system can reach) and decision surface (d_reachable — which paths through the computation the agent takes). The ratchet was supposed to operate on W — close computation channels, replace with data channels, lower the grade.

The experiment shows the ratchet operates on both axes:

| Ratchet product | Axis | What it is | Cost effect |
|---|---|---|---|
| Better tools (batch edit, batch read) | W | Change what's available | **+41%** (worse) |
| Strategy instruction (50 tokens) | d_reachable | Change which paths are taken | **-16%** (better) |
| Natural tool selection (E: agent chooses) | Both | Agent picks the right tool per operation | **-26%** (best) |

Building a tool without teaching its strategy is half a ratchet turn. But the most efficient configuration (E) had no strategy instruction at all — the agent selected structured file tools for reading/editing and bash for execution without being told to. The ratchet's most valuable product might be *the right tool set* — one where the agent's natural selection aligns with efficient workflow.

The revised ratchet cycle: explore → capture → crystallize **tools AND strategy** → teach → exploit. But also: observe which tools the agent naturally reaches for and why. E wasn't designed — it was discovered.

## The hierarchy

The experiment measured three layers:

1. **Model** — not varied (Sonnet throughout). The layer everyone benchmarks.
2. **Tools** — seven configurations (A through F, plus E). The layer the industry focuses on. Effect: -26% to +22%.
3. **Strategy** — one sentence vs none. The layer nobody measures. Effect: **-16%**.

The cheapest layer to change (strategy) had a significant effect — but the best overall result came from tool selection (E), not strategy. Fifty tokens of strategy closed most of the gap between structured tools and bash. But the agent choosing its own tool mix (structured file ops + bash for execution) beat everything, including the principle instruction.

The real hierarchy: the right tools with natural selection (E) > the right tools with the right strategy (I) > the wrong tools with the right strategy > the right tools with the wrong strategy (H, G).

## The same 50 tokens, three models

Everything above used Sonnet. We ran the same conditions with Haiku (n=5) and Opus (n=10-16). The principle instruction — the same ~50 tokens — does something different to each model:

| Model | Without principle (A) | With principle (I) | Effect |
|---|---|---|---|
| **Haiku** (n=5) | 40% pass, $0.69 | **100% pass**, $0.66 | **Capability enabler** |
| **Sonnet** (n=13-28) | 82% pass, $1.35 | 100% pass, $1.08 | Cost optimizer + reliability fix |
| **Opus** (n=10-16) | 100% pass, $1.64 | 100% pass, $1.61 | **No effect** |

**Haiku needs the principle to function.** Without it, Haiku passes 40-60% of the time across conditions A/D/E. It starts editing before it understands the problem, misdiagnoses bugs, and gets lost in cascading failures. "Understand before editing" gives Haiku the planning structure it can't generate on its own. The principle isn't a cost optimization for weak models — it's a prerequisite for correctness.

**Opus doesn't need the principle at all.** Opus passes 100% with or without the instruction, at essentially the same cost ($1.61 vs $1.64). It plans naturally — the instruction adds ~50 tokens to the prompt that Opus doesn't use. It's not harmful, just unnecessary. Opus already does what the principle asks.

**The principle's value is inversely proportional to model capability.** Essential for Haiku (can't complete the task without it). Helpful for Sonnet (completes the task either way, but cheaper and more reliable with it). Unnecessary for Opus (makes no difference). The weaker the model's built-in planning, the more the instruction helps.

```
Haiku:   needs instruction → can't self-organize without it
Sonnet:  benefits from instruction → plans better with a nudge
Opus:    doesn't need instruction → already plans naturally
```

This is the supermodularity prediction applied to the model axis. Restricting d_reachable (via the principle) has larger returns when the model's planning capacity is lower. Haiku has the largest d_reachable (explores everything, plans nothing). Opus has the smallest d_reachable naturally (plans deeply before acting). The principle constrains what Haiku wastes but constrains nothing Opus would have wasted.

The practical implication: a model-aware system needs different CLAUDE.md instructions per model. The same instruction file that makes a Haiku agent reliable is unnecessary overhead for Opus. This is the Quartermaster pattern — select the strategy per model, not per task alone.

**Opus also reverses the bash advantage.** Sonnet is cheaper with bash ($1.03) than structured tools ($1.35). Opus is *more expensive* with bash ($1.66) than structured tools ($1.64). Bash's cognitive forcing function adds value for models that don't naturally plan. Opus already plans. Bash gives Opus more tools to compose elaborate approaches it doesn't need.

The hierarchy from earlier — model < tools < strategy — needs a caveat. The layers *interact*. The right strategy depends on the model. The right tools depend on the model. There may not be a model-independent optimal configuration — but there is a model-independent *approach*: match the configuration to the model's capability profile. That's the Quartermaster.

## What this means for practice

**The security-efficiency tradeoff has a price tag.** E (file tools + bash, level 4) costs $0.98. I (structured tools + principle, level 3) costs $1.11. That's ~13% for full characterizability — every tool call decidable, every effect enumerable, no computation channel. Whether 13% is worth it depends on your deployment context. For autonomous agents with `--dangerously-skip-permissions`, it almost certainly is. For interactive sessions with a human approving every bash call, maybe not.

**Watch what the agent reaches for.** E wasn't designed. Nobody told the agent to use structured file tools for reading and bash for pytest. It naturally selected the right tool for each operation — and that natural selection produced the most efficient configuration we tested. The ratchet's observation phase should watch *which tools the agent selects and why*, not just what operations it performs. E is the agent's own answer to the tool design question.

**Strategy instructions are model-dependent.** The principle helps Sonnet (-16% cost, +18% reliability). It's essential for Haiku (+60% reliability). It destroys Opus (100% → 0% pass). "Good instructions" is not an absolute property — it's relative to the model's capability profile. A CLAUDE.md written for Sonnet will over-constrain Opus and under-constrain Haiku. Configuration should be model-aware.

**Over-specification is consistently the worst intervention, regardless of model.** G (+56%) and H (+41%) are more expensive than no strategy across all conditions tested. The right strategy is a principle, not a procedure. But even principles have a capability ceiling beyond which they become procedures — "understand before editing" is a principle for Sonnet and a procedure for Opus.

**Structured tools earn their keep through auditability, not efficiency.** On this task, structured tools cost more than bash (confirmed, p<0.05). They earn that cost back through characterizability — every operation is typed, logged, and enumerable. The security properties are real. The efficiency properties are partially recovered by strategy (Sonnet) but never fully match the computation channel (E, D).

---

*This post describes experiments conducted during the development of The Ma of Multi-Agent Systems, March 2026. n=13-28 per condition (Sonnet) plus n=2-5 (Haiku, Opus) on one synthetic task (600-line Python codebase, 13 bugs, 48 tests). Multi-model results are preliminary (n=5) and included for the qualitative pattern, not the point estimates.*

*Statistical update (Sonnet, n=13-28 per condition): A vs D reaches significance (d=0.80, p<0.05) — structured tools cost more than bash, confirmed. I vs A (d=0.49) does not reach significance — the principle helps but the effect is medium, not large. The early pilot (n=5) estimated a 32% savings; at n=24 it's 16%. The ranking is stable (E ≤ D ≤ I < A) but the gaps are smaller than first reported. The grade comparison (I at level 3 vs D at level 4-7) is structural and doesn't require statistics. The Haiku and Opus results (n=2-5) are directional only — the qualitative pattern (opposite effects at capability extremes) needs replication.*

*The code, data, and analysis scripts are in the experiments/ directory of the project repository.*

---

*Companion to [The Ma of Multi-Agent Systems](../ma/00-intro) and [Ratchet Fuel](../fuel/00-ratchet-review)*
