# The Experiment That Proved Us Wrong

*We set out to prove structured tools beat bash. We were wrong — then we found something better.*

---

## The hypothesis

The framework predicts that restriction has superlinear returns. Replace a computation channel (bash — level 4, Turing-complete) with data channel tools (structured read, edit, search — levels 0-2), and the system should become cheaper to regulate, easier to audit, and at least as productive. The specified band should expand. The grade should drop. The ratchet should turn.

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

| Condition | Cost | Change from baseline |
|---|---|---|
| A (structured, no guidance) | $1.43 | — |
| D (bash only) | $1.05 | -27% |
| **I (structured + six tokens)** | **$0.97** | **-32%** |

I beat bash. Same structured tools as A. Same pass rate. 32% cheaper than the baseline, 8% cheaper than bash. The six-token instruction reimplemented bash's cognitive forcing function — "plan before you act" — without the computation channel.

Flip it: omitting those six tokens costs 47% more per run. Every blank line in your CLAUDE.md has a price.

## What we actually found

We set out to test whether closing the computation channel improves outcomes. The answer is nuanced:

**Closing the channel alone hurts.** Removing bash and replacing it with structured tools (A) costs 36% more. The tools work correctly — every operation is specified, auditable, characterizable. But the agent uses them one at a time, burning inference budget on round-trips that bash handles in a single script.

**The channel wasn't the variable.** We thought we were measuring the effect of the computation channel (W axis — what tools are available). We were actually measuring the effect of the *cognitive pattern* the channel induces (d_reachable — which paths through the decision surface the agent takes). The channel is the mechanism. The pattern is the cause.

**Six tokens restore what the channel provided.** The principle "understand before editing" changes d_reachable without changing W. The agent has exactly the same tools. It takes fewer paths through the same space. The paths it takes are the ones that bash would have induced — read everything, diagnose everything, then act. The principle is a specified substitute for the computation channel's cognitive side effect.

## The security bonus

And here's the part we didn't expect: the six-token version is also the most *secure* configuration.

Condition D (bash) needs bubblewrap sandboxing, shell metacharacter filtering, a command allowlist, PID namespace isolation, and network lockdown. Every tool call passes through a Turing-complete interpreter where Rice's theorem applies. The Harness pattern-matches on command strings and hopes.

Condition I (structured + principle) needs none of that. Every tool call is structured, typed, and logged. The Harness can enumerate every possible operation. The attack surface is characterizable — prompt injection and path traversal are still possible, but the Harness can reason about them. Test execution runs inside bwrap (sandboxing the *consequences* of what the agent wrote), but the agent itself never touches a shell.

Cheaper, simpler, more auditable, characterizable attack surface. Not by adding more infrastructure — by adding six tokens and removing bash.

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
