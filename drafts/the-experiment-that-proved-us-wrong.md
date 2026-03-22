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

| Condition | Tools | Cost per run | Pass rate |
|---|---|---|---|
| A (structured tools) | file_read, file_edit, file_search, run_tests | **$1.43** | 100% |
| D (bash only) | bash_sandboxed | **$1.05** | 100% |

Bash was 27% cheaper. Same outcome. Every metric — turns, tool calls, output tokens, wall time — favored bash. The structured tools that were supposed to free the model's inference budget instead *increased* the inference cost.

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

| Condition | Instruction | Cost | Change from baseline | Output tokens |
|---|---|---|---|---|
| **G** (four-phase strategy) | Detailed prescription | **$2.06** | **+44%** | 90,702 |
| **H** (batch tools + guidance) | Tool-specific guidance | $1.86 | +30% | 75,919 |
| A (structured, no guidance) | Generic | $1.43 | — | 50,170 |
| D (bash only) | Generic | $1.05 | -27% | 30,739 |
| **I (structured + six tokens)** | **"Understand first"** | **$0.97** | **-32%** | **30,445** |

The spectrum runs from $2.06 (most instruction) to $0.97 (least instruction that works). More instruction produced more output tokens — the agent wrote detailed phase-by-phase analysis because we asked for it, and all that writing was overhead. G generated 3× the output tokens of I for the same outcome.

The detailed prescription didn't just fail to help. It was the most expensive condition in the entire experiment — worse than bash, worse than no guidance at all. Over-specification constrains the agent into a rigid workflow and generates verbose compliance with the prescription instead of efficient problem-solving.

I beat everything. Same structured tools as A. Same pass rate. 32% cheaper than the baseline. 53% cheaper than the detailed strategy. 8% cheaper than bash. The six-token instruction reimplemented bash's cognitive forcing function — "plan before you act" — without the computation channel and without the overhead of detailed instructions.

Flip it: omitting those six tokens costs 47% more per run. Adding sixty tokens of detailed strategy costs 112% more. Every blank line in your CLAUDE.md has a price. So does every unnecessary line.

## Which six tokens

Six tokens are cheap to deploy. Knowing *which* six tokens required the full experiment.

We didn't start with "understand first." We started with "close the computation channel" — the security exercise. That failed on cost (A: +36%). So we analyzed *why* bash was cheaper and discovered the cognitive forcing function. Then we tried to replicate it with a detailed prescription (G: +44% — the most expensive condition). Then we stripped the prescription back to its core principle (I: -32%).

The discovery path was: ratchet theory → observation → characterization → security improvement → experiment → cognitive insight → strategy distillation. Each step depended on the previous. The six tokens are the residue of that entire process.

This matters because "just add a principle instruction" is the wrong takeaway. The right takeaway is: the ratchet's observation phase — watching how the agent works, not just what it does — is where the value is created. The six tokens are what you extract. The observation is what tells you which six tokens to extract. G proves that guessing wrong about the strategy costs more than having no strategy at all.

## What we actually found

We set out to test whether closing the computation channel improves outcomes. The answer is nuanced:

**Closing the channel alone hurts.** Removing bash and replacing it with structured tools (A) costs 36% more. The tools work correctly — every operation is specified, auditable, characterizable. But the agent uses them one at a time, burning inference budget on round-trips that bash handles in a single script.

**The channel wasn't the variable.** We thought we were measuring the effect of the computation channel (W axis — what tools are available). We were actually measuring the effect of the *cognitive pattern* the channel induces (d_reachable — which paths through the decision surface the agent takes). The channel is the mechanism. The pattern is the cause.

**Six tokens restore what the channel provided.** The principle "understand before editing" changes d_reachable without changing W. The agent has exactly the same tools. It takes fewer paths through the same space. The paths it takes are the ones that bash would have induced — read everything, diagnose everything, then act. The principle is a specified substitute for the computation channel's cognitive side effect.

**The axes are coupled.** Post 6 argues that d_reachable is downstream of W — the tools you provide shape the paths the agent takes. This experiment shows the mechanism: tool interfaces are cognitive forcing functions. Bash's "give me a program" induces planning. `file_edit`'s "give me a replacement" induces incrementalism. Strategy instructions reshape the paths without changing the tools. You can't optimize W and d_reachable independently — and the [revised Rule 7](../ma/09-building-with-ma) develops the practical implications.

## Back to security

Remember: we started with a security question. Can we lock down a coding activity without sacrificing quality or increasing costs? The answer turns out to be yes — but not the way we expected.

The six-token version is also the most *secure* configuration.

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

I is characterizable on every dimension. D is characterizable only on the bwrap-guaranteed dimensions (network, termination). The Harness can write an exhaustive policy for I. It structurally cannot for D.

In our experiment, D was sandboxed — level 4 with `--die-with-parent`. In production, bash is level 8. The grade gap between I (level 3) and production bash (level 8) is five levels of the computation taxonomy. The permission gate that the Principal applies to each bash call — reading the command, deciding if it's safe — is a human doing System 3 work on every turn. Condition I eliminates that work entirely. Every tool call is self-evidently characterizable. The Principal doesn't need to evaluate it.

Cheaper, simpler, more auditable, and provably lower grade. Not by adding more infrastructure — by separating write from execute and sandboxing the execute path.

## The two products of the ratchet

The framework defines *ma* on two axes: world coupling (W — what the system can reach) and decision surface (d_reachable — which paths through the computation the agent takes). The ratchet was supposed to operate on W — close computation channels, replace with data channels, lower the grade.

The experiment shows the ratchet operates on both axes, and the d_reachable product is more valuable:

| Ratchet product | Axis | What it is | Cost effect |
|---|---|---|---|
| Better tools (batch edit, batch read) | W | Change what's available | **+30%** (worse) |
| Strategy instruction (six tokens) | d_reachable | Change which paths are taken | **-32%** (better) |

Building a tool without teaching its strategy is half a ratchet turn. Teaching the strategy without the tool might be the better half.

The revised ratchet cycle: explore → capture → crystallize **tools AND strategy** → teach → exploit.

## The hierarchy

The experiment measured three layers:

1. **Model** — not varied (Sonnet throughout). The layer everyone benchmarks.
2. **Tools** — six configurations (A through F). The layer the industry focuses on. Effect: -29% to +36%.
3. **Strategy** — one sentence vs none. The layer nobody measures. Effect: **-32%**.

The cheapest layer to change had the largest effect. Six tokens of text outperformed months of tool engineering.

## What this means for practice

**Every CLAUDE.md file is a strategy artifact.** It's not documentation. It's not a nice-to-have. It's the most cost-effective intervention available. Every sentence that tells the agent *when* to act, *how* to compose tools, or *what to understand first* is worth more than the tool infrastructure it operates on.

**The ratchet's observation phase should watch *how*, not just *what*.** We observed the agent running `grep -r` and built `file_search`. We should have observed the agent planning all fixes before executing any and built... one sentence in the prompt.

**Structured tools earn their keep through auditability, not efficiency.** On this task, structured tools cost more than bash. They earn that cost back through characterizability — every operation is typed, logged, and enumerable. The security properties are real. The efficiency properties require strategy to activate.

**Bash's advantage is a cognitive side effect you can replicate.** Bash forces program-writing, which forces planning. A principle instruction forces planning directly. You don't need the computation channel to get the planning behavior. You need the planning behavior to get the efficiency.

---

*This post describes experiments conducted during the development of The Ma of Multi-Agent Systems, March 2026. n=5 per condition on one synthetic task (600-line Python codebase, 13 bugs, 48 tests). All conditions achieved 100% pass rate — the differences are in cost, not quality.*

*Statistical honesty: the effect sizes are large (Cohen's d = 1.40 for I vs A, 1.11 for A vs D) but the confidence intervals overlap at n=5. I vs A is marginal (p ≈ 0.07). Nothing reaches conventional significance. The 32% savings is the point estimate; the 95% confidence interval for I's cost is [$0.70, $1.24] vs A's [$0.92, $1.94] — overlapping. The patterns are suggestive. The sample sizes require replication at n=15-20 per condition for confident conclusions.*

*The code, data, and analysis scripts are in the experiments/ directory of the project repository.*

---

*Companion to [The Ma of Multi-Agent Systems](../ma/00-intro) and [Ratchet Fuel](../fuel/00-ratchet-review)*
