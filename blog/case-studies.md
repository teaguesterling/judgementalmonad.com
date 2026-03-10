# Case Studies in Characterization Difficulty

*Worked examples applying the formal framework to concrete systems.*

---

These studies use the characterization difficulty measure from the [formal companion](formal-companion.md) (Def. 4.6, Prop. 4.7):

```
chi(w, d) = I(w) . log P(d)
```

where `I(w)` counts distinguishable inputs at world coupling level `w`, and `P(d)` counts distinguishable execution paths at decision surface level `d`. The supermodularity of `chi` means restriction on either axis saves more when the other axis is high.

Each study states a setup, applies the formalism, and derives a result — often one that wasn't obvious from the setup alone.

---

## Study 1: The context window as world coupling ceiling

**Setup.** A single agentic Inferencer with a fixed tool set. The context window has a hard token limit — say 200k tokens.

**Analysis.** For the LLM composite, `I(w)` is bounded by the number of distinguishable context windows the Harness can construct. The token limit caps this: `I(w) <= |Vocab|^200k` in the absolute worst case, though in practice far fewer context windows are distinguishable (the model can't distinguish arbitrary token permutations; many distinct token sequences map to identical behavior).

As the conversation progresses and the context fills, `I(w)` approaches its ceiling. The Harness has fewer degrees of freedom in scope construction — most of the context is determined by history, leaving only a narrow band for new information injection.

**Result.** Near the context ceiling, the marginal return of adding more world coupling drops to zero — you literally cannot feed the model more distinguishable inputs. But the marginal return of *restricting d* stays proportional to `I(w)`, which is now large:

```
delta_chi_from_restricting_d = I(w_ceiling) . (log P(d_current) - log P(d_restricted))
```

This is maximized when `I(w)` is at its ceiling. **Tool restriction is maximally effective at the context limit** — precisely the regime where systems are hardest to regulate. The supermodularity isn't just a static property; it has a temporal signature. As conversations progress and contexts fill, the case for restriction strengthens.

**Corollary.** Context management (compaction, summarization, scope pruning) reduces `I(w)` by reducing the number of distinguishable context states. This is the formal content of the claim from post 6 that context management is the single most leveraged Harness operation — it controls the ceiling against which all other costs are measured.

---

## Study 2: Communication channel amplification

**Setup.** Two agentic Inferencers, A and B, communicating through a Harness. Neither has Bash — both are below computation channel level 4 with bounded tools, individually convergent dynamics. Concretely:

- **Agent A** (researcher): `{Read, Glob, Grep, WriteDesign}`
- **Agent B** (implementer): `{Read, Edit, Write, RunTests}`

A produces design documents. B reads designs and produces code with test results. The Harness mediates all communication.

**The independent case.** If A and B never communicate, the composite `chi` is additive:

```
chi_composite = chi_A + chi_B = I(w_A) . log P(d_A) + I(w_B) . log P(d_B)
```

The observer characterizes each independently. Behaviors are a product; log of a product is a sum.

**The single-agent baseline.** A single agent with token window `T_A`, working alone over `N = T_A / c` turns:

```
chi_single = (T_A / c) . log P(d_A)
```

Linear in the token window.

**Case 2a: Unstructured communication.** A sends arbitrary natural language. B works internally for `M = T_B / c_B` turns per round (B has its own context window `T_B`). Over K rounds:

```
chi_two = (T_A / c_A) . (log P(d_A) + (T_B / c_B) . log P(d_B))
        = chi_A_solo + (T_A . T_B) / (c_A . c_B) . log P(d_B)
```

The amplification term is proportional to the **product** of the two context windows (formal companion Prop. 8.17). A single agent with window `2T` has `chi ~ 2T . log P(d)`. Two agents with windows `T` each have `chi ~ T^2 . log P(d)`. The second agent changes the growth from linear to quadratic in total token budget.

Why? Because B-as-a-tool-for-A is a computation channel, even though B's individual tools are all data channels. B accepts a natural-language specification and returns the result of executing it over its full context window. From A's perspective, that's a level 4 tool — the input is a program, the output is the result of executing it. **The computation channel emerges from composition, not from any individual tool** (formal companion Prop. 9.11).

For N agents in a pipeline, `chi ~ T_1 . T_2 . ... . T_N` — polynomial of degree N. Finite (token windows bound everything), but the degree grows with agent count.

**Case 2b: Structured communication.** A co-domain funnel with schema cardinality K at the boundary replaces the amplification term:

```
(T_A . T_B) / (c_A . c_B) . log P(d_B)  -->  (T_A / c_A) . log K
```

The funnel decouples A's `chi` from B's context window entirely. Growth returns to linear (formal companion Cor. 8.19). The funnel prevents the computation channel from emerging by projecting B's effective decision surface from `trained` to `specified`.

**What the second agent changes:**

| Property | Single agent (2T) | Two agents, unstructured (T each) | Two agents, structured |
|---|---|---|---|
| Growth in total tokens | Linear: 2T | Quadratic: T^2 | Linear: T + log K |
| Effective computation level | Level 2-3 (tools) | Level 4 (emergent) | Level 2-3 (preserved) |
| Bounded by | Token window | Product of windows | Window + schema |

**Result.** Two individually sub-Turing agents compose into a system with emergent Turing-like capability at the delegation boundary. Neither agent crosses the computation channel threshold alone, but the pair does. The token windows bound everything finitely, but the growth rate shifts from linear to polynomial.

**Implication for the star topology.** The Harness breaks the amplification by mediating every exchange:

1. **Funnel B's output** before injection into A's context (replace T_B with log K)
2. **Scope A's request** before injection into B's context (reduce what B sees)
3. **Terminate the loop** after N rounds (cap the polynomial degree)

Each is a `chi`-management operation at the communication boundary. The star topology provides a `chi` management point at every inter-agent boundary — and the formal companion shows exactly what each intervention buys.

**Prediction.** Multi-agent systems where agents communicate through unstructured natural language should exhibit `chi` that grows as the product of participant context windows. Systems with structured communication schemas should exhibit linear growth. This is testable: measure observer prediction error as a function of total token budget, with and without structured channels.

---

## Study 3: Structured build output as co-domain funnel

**Setup.** An agentic Inferencer needs information about build failures. Two architectures:

- **Architecture 1:** Agent has Bash, runs `make -j8 2>&1`, parses raw output.
- **Architecture 2:** Agent uses [blq](https://github.com/teaguesterling/blq-cli) MCP tools (`errors`, `inspect`, `diff`) to query structured build events.

**Architecture 1 analysis.** Raw Bash is computation channel level 4+ — the agent sends arbitrary text to a universal machine. The build output is unstructured: 500 lines of interleaved compiler messages, warnings, errors, progress indicators. The agent's world coupling includes the full cardinality of raw build output — every possible output the build system could produce. And parsing that output *requires* high `d` (the agent needs trained intelligence to extract errors from noise).

```
chi_bash = I(w_build_raw) . log P(d_parse + d_task)
```

Both factors are large: `I(w_build_raw)` because raw output is high-cardinality, `P(d_parse + d_task)` because the agent must both parse and act.

**Architecture 2 analysis.** blq's MCP tools are computation channel levels 0-2 — structured queries, data channels, convergent dynamics. `errors()` returns a table: file, line, severity, message. The schema has bounded cardinality `K_blq`. Parsing is eliminated — the agent receives pre-structured events.

```
chi_blq = I(w_blq_structured) . log P(d_task)
```

Both factors are smaller: `I(w_blq_structured) << I(w_build_raw)` because the structured schema has far fewer distinguishable outputs than raw text, and `P(d_task) < P(d_parse + d_task)` because parsing is no longer the agent's job.

**Result.** blq reduces `chi` on *both axes simultaneously*:

| | World coupling `I(w)` | Decision surface `P(d)` |
|---|---|---|
| Raw Bash | High (raw output cardinality) | High (parse + reason) |
| blq tools | Low (structured schema) | Lower (reason only) |

The reduction is superlinear by Prop. 4.7 — reducing both axes together saves more than the sum of reducing each independently.

**The multi-agent case.** When Agent A runs a build and Agent B needs results:

- **Without blq:** A passes raw build output through the Harness. A's contribution to `I(w_B)` is the full cardinality of raw output — unstructured, high `chi` contribution. (Study 2, case 2b.)
- **With blq:** A runs the build, blq captures it, B queries `blq errors`. The communication goes through a structured intermediary with bounded schema `K_blq`. (Study 2, case 2a.)

blq is a Harness-mediation point for the build-system-to-agent communication channel. It interposes a co-domain funnel at the boundary, keeping `chi` composition additive where it would otherwise be multiplicative.

**The computation channel angle.** blq also drops the computation channel level:

| | Computation level | Dynamics |
|---|---|---|
| Raw Bash | Level 4+ (universal machine) | Self-amplifying |
| blq tools | Level 0-2 (structured queries) | Convergent |

This is the qualitative shift from the computation channel taxonomy (formal companion section 9): not a linear improvement but a change in the kind of system. The agent with Bash needs sandbox regulation to bound its trajectory. The agent with blq tools has convergent dynamics by construction.

---

## Connecting the studies

The three studies form a progression:

1. **Study 1** establishes that the context window creates a ceiling on `I(w)`, making tool restriction maximally effective in the regime where systems are hardest to regulate.

2. **Study 2** shows that inter-agent delegation creates emergent computation channels — two sub-Turing agents compose into a system with Turing-like capability at the delegation boundary. The growth rate shifts from linear to polynomial in total token budget. Co-domain funnels prevent this emergence by decoupling the agents' context windows.

3. **Study 3** demonstrates the concrete pattern: a structured intermediary (blq) acts as a co-domain funnel that drops both axes of `chi` simultaneously, preserves linear growth, and prevents computation channel emergence.

The common thread: **characterization difficulty is the quantity that system architecture manages**. The context window bounds it. Delegation amplifies it (quadratically per agent added). Structured intermediaries restore linear growth. The Harness's job, at every scale, is `chi` management.

An observation that cuts across all three: the framework's claims about dynamics are bounded by token windows. "Divergence" means reaching the regulatory budget before the window is consumed. "Convergence" means the budget holds. The practical question is always about rates within finite bounds, not about infinity.

---

*These studies accompany the [formal companion](formal-companion.md) and the blog series [The Ma of Multi-Agent Systems](00-intro.md).*
