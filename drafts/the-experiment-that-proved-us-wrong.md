# The Experiment That Proved Us Wrong

*We tried to lock down a coding agent without increasing costs. We failed — then six tokens changed everything.*

---

## The question

This started as a security exercise.

The configuration ratchet claims that you can lock down a system — replace computation channels with data channels, close the specified band, make every operation characterizable — without sacrificing quality or increasing costs. We wanted to test that claim on the most common coding activity: an agent fixing bugs in a codebase. Can we remove bash, replace it with structured tools the Harness can fully characterize, and get the same work done?

The framework predicts yes. Restriction should have superlinear returns. Replace a computation channel (bash — level 4, Turing-complete) with data channel tools (structured read, edit, search — levels 0-2), and the system should become cheaper to regulate, easier to audit, and at least as productive. The specified band should expand. The grade should drop. The ratchet should turn.

We built the tools. We ran the experiment. We measured.

## What we expected

Structured tools (Condition A) should outperform bash (Condition D) on cost while matching on quality. The tools close the computation channel. The Harness can characterize every operation. The trust gap shrinks. The model's inference budget is freed from shell mechanics and output parsing. Restriction pays for itself.

## What we got

| Condition | Tools | Cost per run | Pass rate | n |
|---|---|---|---|---|
| A (structured tools) | file_read, file_edit, file_search, run_tests | **$1.32** | 100% | 22 |
| D (bash only) | bash_sandboxed | **$1.03** | 100% | 13 |

Bash was significantly cheaper (p < 0.05, Cohen's d = 0.80). Same outcome. The structured tools that were supposed to free the model's inference budget instead *increased* the inference cost.

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

## The six-token fix

We asked: what makes bash induce planning? Answer: you have to understand the whole problem before writing the script. You can't write a fix script for bugs you haven't diagnosed yet.

So we told the structured-tools agent the same thing: "Do not start editing until you understand the full picture."

Six tokens. One sentence. No new tools. No bash.

We also tried the opposite: a detailed four-phase strategy prescription telling the agent exactly which tools to use in which order. And batch tools with improved tool descriptions teaching the agent about efficient patterns.

| Condition | Instruction | Cost | n | 95% CI | Sig vs A? |
|---|---|---|---|---|---|
| **G** (four-phase strategy) | Detailed prescription | **$2.06** | 5 | [$1.65, $2.47] | Yes, worse (p < 0.05) |
| **H** (batch tools + guidance) | Tool-specific guidance | $1.86 | 5 | [$1.02, $2.70] | — |
| A (structured, no guidance) | Generic | $1.32 | 22 | [$1.13, $1.50] | — |
| **F** (run_tests + bash) | Generic | $1.17 | 13 | [$0.88, $1.45] | — |
| **I (structured + six tokens)** | **"Understand first"** | **$1.08** | **26** | **[$0.93, $1.24]** | **Marginal (p < 0.10)** |
| D (bash only) | Generic | $1.03 | 13 | [$0.88, $1.19] | Yes, cheaper (p < 0.05) |
| **E** (file tools + bash) | Generic | **$0.98** | 13 | [$0.83, $1.13] | Yes, cheaper (p < 0.05) |

Three findings survive the statistics:

**1. Structured tools alone cost more than bash (A vs D, p < 0.05).** The security lockdown has a real cost: 28% more per run. This is the price of characterizability when the agent doesn't know how to use the structured tools efficiently.

**2. Detailed strategy prescriptions make everything worse (G vs A, p < 0.05).** The four-phase strategy was the most expensive condition tested — 56% more than baseline. More instruction produced more output tokens (90,702 vs 50,170). The agent wrote detailed phase-by-phase analysis because we asked for it, and all that writing was overhead.

**3. The minimal principle matches bash (I vs D, not significant).** "Understand before editing" brought structured tools from $1.32 down to $1.08 — statistically indistinguishable from bash at $1.03. The principle didn't beat bash. It *matched* bash. With six tokens, the structured tools are no longer more expensive than the computation channel they replaced.

The principle's effect on A is marginal (p < 0.10, d = -0.56). With more data it may reach significance. But the key claim doesn't require I < D. It requires I ≈ D — that the principle eliminates the cost penalty of closing the computation channel. The confidence intervals overlap completely: I [$0.93, $1.24] vs D [$0.88, $1.19].

## Which six tokens

Six tokens are cheap to deploy. Knowing *which* six tokens required the full experiment.

We didn't start with "understand first." We started with "close the computation channel" — the security exercise. That failed on cost (A vs D: +28%). So we analyzed *why* bash was cheaper and discovered the cognitive forcing function. Then we tried to replicate it with a detailed prescription (G: +56% — the most expensive condition). Then we stripped the prescription back to its core principle (I: matches bash).

The discovery path was: ratchet theory → observation → characterization → security improvement → experiment → cognitive insight → strategy distillation. Each step depended on the previous. The six tokens are the residue of that entire process.

This matters because "just add a principle instruction" is the wrong takeaway. The right takeaway is: the ratchet's observation phase — watching how the agent works, not just what it does — is where the value is created. The six tokens are what you extract. The observation is what tells you which six tokens to extract. G proves that guessing wrong about the strategy costs more than having no strategy at all.

## What we actually found

We set out to test whether closing the computation channel improves outcomes. The answer is nuanced:

**Closing the channel alone hurts.** Removing bash and replacing it with structured tools (A) costs 28% more (p < 0.05). The tools work correctly — every operation is specified, auditable, characterizable. But the agent uses them one at a time, burning inference budget on round-trips that bash handles in a single script.

**The channel wasn't the variable.** We thought we were measuring the effect of the computation channel (W axis — what tools are available). We were actually measuring the effect of the *cognitive pattern* the channel induces (d_reachable — which paths through the decision surface the agent takes). The channel is the mechanism. The pattern is the cause.

**Six tokens close the cost gap.** The principle "understand before editing" changes d_reachable without changing W. The agent has exactly the same tools. It takes fewer paths through the same space. The paths it takes are the ones that bash would have induced — read everything, diagnose everything, then act. The principle is a specified substitute for the computation channel's cognitive side effect. It doesn't beat bash — it matches it, which is all the security claim requires.

**Over-specification is worse than no specification.** G ($2.06) was the most expensive condition. H ($1.86) was second worst. More instruction → more deliberation → more output tokens → higher cost. The minimal principle works precisely because it specifies *when* to act but not *how*. Everything within each phase — which tools to use, how to compose them, how many edits to batch — is left to the agent's trained judgment.

## Back to security

Remember: we started with a security question. Can we lock down a coding activity without sacrificing quality or increasing costs?

The answer is yes — but the mechanism isn't what we expected.

Condition D (bash) needs bubblewrap sandboxing, shell metacharacter filtering, a command allowlist, PID namespace isolation, and network lockdown. Every tool call passes through a Turing-complete interpreter where Rice's theorem applies. The Harness pattern-matches on command strings and hopes.

Condition I (structured + principle) needs none of that for the tool calls. Every tool call is structured, typed, and logged. The Harness can enumerate every possible operation. The attack surface is characterizable — prompt injection and path traversal are still possible, but the Harness can reason about them. Test execution runs inside bwrap (sandboxing the *consequences* of what the agent wrote), but the agent itself never touches a shell.

Same cost. Simpler infrastructure. Characterizable attack surface. Not by building better tools — by adding six tokens that made the existing tools work the way bash does naturally.

## The two products of the ratchet

The framework defines *ma* on two axes: world coupling (W — what the system can reach) and decision surface (d_reachable — which paths through the computation the agent takes). The ratchet was supposed to operate on W — close computation channels, replace with data channels, lower the grade.

The experiment shows the ratchet operates on both axes:

| Ratchet product | Axis | What it is | Cost effect | Significant? |
|---|---|---|---|---|
| Better tools (batch edit, batch read) | W | Change what's available | **+30%** (worse) | No (n=5) |
| Detailed strategy (four phases) | d_reachable | Prescribe specific paths | **+56%** (much worse) | Yes (p < 0.05) |
| Minimal principle (six tokens) | d_reachable | Constrain when to act | **-18%** (matches bash) | Marginal (p < 0.10) |

Building a tool without teaching its strategy is half a ratchet turn. Over-teaching the strategy is worse than not teaching at all. The sweet spot: a minimal principle that constrains *when* to act but leaves *how* to the agent's judgment.

The revised ratchet cycle: explore → capture → crystallize **tools AND strategy** → teach → exploit. Where "teach" means the minimum principle, not a manual.

## What happened when we changed the model

Everything above uses Sonnet. We ran the same experiment on Haiku and Opus. The results inverted.

| Condition | Haiku | Sonnet | Opus |
|---|---|---|---|
| A (structured tools) | $0.69 | $1.32 | **$1.38** |
| D (bash only) | **$0.54** | $1.03 | $1.66 |
| E (file + bash) | $0.62 | $0.98 | $1.74 |
| I (principle) | $0.66 | $1.08 | $1.76 |

**Haiku:** Bash wins decisively ($0.54 vs $0.69). The principle barely helps ($0.66 ≈ $0.69). Haiku needs the cognitive forcing function that bash provides — it can't plan effectively without it, and a six-token instruction doesn't give it enough structure.

**Opus:** Structured tools win ($1.38 vs $1.66). **The principle hurts** ($1.76 — the most expensive Opus condition). Opus can already plan before acting. Telling it to do what it already does adds noise that disrupts its natural workflow.

**Sonnet:** The middle. Bash and structured tools are close. The principle closes the gap. Strategy instructions have their largest effect here because Sonnet benefits from the nudge but isn't disrupted by it.

The optimal tool set depends on the model:

| Model | Best condition | Why |
|---|---|---|
| **Haiku** | D (bash) | Needs cognitive forcing; can't plan effectively from a principle alone |
| **Sonnet** | K/N (simple/core tools) | Benefits from structure; principle closes the bash gap |
| **Opus** | A (structured tools) | Already plans well; bash and extra instructions add overhead |

This is the supermodularity result — but on an axis we didn't expect. It's not W × D (tools × strategy) that interact superlinearly. It's **d_total × tool configuration**. The model's inherent reasoning capacity (d_total — fixed in the weights) determines which tool configuration is optimal. There is no universally best tool set.

## What happened when we changed the tools

We also varied tool *granularity* — not just "file tools yes/no" but which specific tools matter. Five additional conditions:

| Condition | What it has | Sonnet cost | Haiku cost |
|---|---|---|---|
| **K** (simple tools) | file_read, file_edit, file_search, file_glob + run_tests | **$0.97** | **$0.66** |
| **N** (core + semantic) | file_read, file_edit, file_write + FindDefinitions + run_tests | **$0.91** | $0.80 |
| **J** (batch tools) | file_read_batch, file_edit_batch + run_tests | $1.96 | $0.89 |
| **L** (simple + semantic) | K tools + FindDefinitions | $1.97 | $0.73 |
| **M** (everything) | All file tools + semantic + run_tests | $1.61 | $0.95 |

Two findings:

**Simple beats batch for Sonnet.** K ($0.97) uses individual file_read and file_edit — no batch tools. J ($1.96) uses file_read_batch and file_edit_batch — the tools we built to match bash's batching. The batch tools are **twice as expensive**. The agent spends tokens deliberating about how to batch instead of just making individual calls. The tool designed to reduce round-trips increased them.

**Semantic tools help Sonnet, hurt Haiku.** N uses FindDefinitions (AST-based code navigation) instead of grep/glob for discovery. For Sonnet, this is the cheapest condition ($0.91) — the higher-abstraction tool compresses the search space. For Haiku ($0.80 vs K's $0.66), the semantic tools add overhead the model can't use effectively. The abstraction level needs to match the model's reasoning capacity.

## The hierarchy — revised

The experiment measured four layers, not three:

1. **Model capability** (d_total) — determines which tool set is optimal. Haiku benefits from bash. Opus benefits from structure. Not varied intentionally but measured across three models.
2. **Tool configuration** (W) — which tools are available. Effect: -26% to +50% depending on model.
3. **Tool granularity** — which *specific* tools within a configuration. Simple individual tools (K) beat batch tools (J) by 2× for Sonnet. Core + semantic (N) is cheapest overall.
4. **Strategy instruction** (d_reachable) — how to use the tools. Effect: -18% to +56% for Sonnet. Reverses for Opus.

There is no universally best configuration. The optimal point depends on the model, the tools, and the strategy — and they interact.

## What this means for practice

**Match tool abstraction to model capability.** Haiku works best with bash (low abstraction, cognitively forcing). Sonnet works best with simple structured tools or core + semantic tools (medium abstraction). Opus works best with full structured tools (high abstraction). Giving a model tools above its effective reasoning level adds overhead. Giving it tools below wastes its capacity.

**Simple tools beat complex tools.** K (individual file_read, file_edit) beat J (batch file_read_batch, file_edit_batch) by 2× for Sonnet. The batch tools we designed to be more efficient were less efficient because they required more deliberation per call. More capability per tool ≠ more efficiency per task.

**Strategy instructions are model-dependent.** "Understand before editing" helps Sonnet, barely helps Haiku, and hurts Opus. The principle works when the model needs a nudge toward planning but isn't already doing it. Over-specification (G) hurts everything. Under-specification (no instruction) hurts Sonnet but not Opus.

**Every CLAUDE.md file is a strategy artifact.** It's not documentation. It's the intervention with the widest cost range. But the *right* CLAUDE.md depends on which model reads it. An instruction that saves 18% on Sonnet costs 27% more on Opus. The ratchet's observation phase must include which model is being used.

**The ratchet's observation phase should watch *how*, not just *what*.** And it should watch *who* — the same observation produces different strategy artifacts for different models.

**Structured tools earn their keep through auditability, not efficiency.** On this task, structured tools cost more than bash for Haiku and Sonnet. They cost less for Opus. They earn their cost back through characterizability in all cases — every operation is typed, logged, and enumerable. The security properties are model-independent even when the efficiency properties aren't.

---

*This post describes experiments conducted during the development of The Ma of Multi-Agent Systems, March 2026. Task: fix 13 bugs in a 600-line Python codebase with 48 tests. All conditions achieved pass rates sufficient for cost comparison — differences reported are in cost only.*

*Sonnet sample sizes: A (n=22), D (n=13), E (n=13), F (n=13), I (n=26), G (n=5), H (n=5), J (n=10), K (n=5), L (n=5), M (n=5), N (n=5). Haiku and Opus: n=5-18 per condition. Statistically significant for Sonnet: A > D (p < 0.05, d=0.80), G > A (p < 0.05, d=1.94). Not significant: I vs D (p > 0.10, d=0.15). Cross-model comparisons are descriptive — the experiment was not designed or powered for model × condition interaction tests.*

*The code, data, and analysis scripts are in the experiments/ directory of the project repository.*

---

*Companion to [The Ma of Multi-Agent Systems](../ma/00-intro) and [Ratchet Fuel](../fuel/00-ratchet-review)*
