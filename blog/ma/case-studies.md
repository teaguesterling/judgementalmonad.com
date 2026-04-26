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

## Study 3: Structured build tools as decision surface reduction

**Setup.** An agentic Inferencer needs to build code and diagnose failures. Two architectures:

- **Architecture 1:** Agent has Bash, runs `make -j8 2>&1`, parses raw output.
- **Architecture 2:** Agent uses [blq](https://github.com/teaguesterling/blq-cli) MCP tools (`build`, `test`, `errors`, `inspect`, `diff`).

**What blq is not.** blq is not technically "safer" in the computation channel sense. Underneath, `build` still invokes a universal machine — a compiler, a linker, arbitrary build scripts. The code the agent wrote *is* the specification that gets executed. If the agent has written malicious code, `build` will faithfully compile it. blq does not change the computation channel level of the underlying operation.

**What blq actually does.** blq collapses the agent's *decision surface* around the build process. With Bash, the agent faces a combinatorial space of invocation choices:

- `make` or `make -j4` or `make -j$(nproc)` or `cmake --build .`?
- `2>&1` or `2>&1 | tee build.log` or redirect to file?
- Parse with `grep error` or `awk` or read the whole thing?
- Which environment variables? Which working directory?

Each choice is a degree of freedom in `d`. The agent must decide *how* to build, not just *whether* to build. With blq, the decision surface collapses to `build` or `test` — opaque invocations where the mechanism is not the agent's concern.

```
P(d_bash) >> P(d_blq)  -- not because the underlying computation changed,
                        -- but because the agent's choice space shrank
```

**The opacity is the point.** Because the agent cannot see or control *how* builds execute, the infrastructure is free to impose arbitrary constraints without the agent's knowledge or cooperation:

- Run builds in Docker containers with no network access
- Apply `ulimit` constraints on CPU, memory, file descriptors
- Execute on remote build farms with audit logging
- Sandbox with seccomp profiles, read-only filesystem mounts
- Run tests in ephemeral environments that are destroyed after each invocation

None of these require the agent to opt in, configure, or even be aware. The agent says `build`; what happens behind that interface is the infrastructure's decision, not the agent's. **blq removes the decisionality from the agent and places it in the infrastructure**, where it can be governed by policy rather than by prompt.

**The formal content.** This is a reduction in `d`, not in computation channel level. The underlying build is still level 4. But the agent's *interface* to the build is level 0 — a fixed-vocabulary command with no parameters that matter. The chi reduction comes entirely from the decision surface axis:

```
chi_bash = I(w_build_raw) . log P(d_invoke + d_parse + d_task)
chi_blq  = I(w_blq_structured) . log P(d_task)
```

The `d_invoke` term (choosing how to run the build) and `d_parse` term (extracting structure from raw output) both vanish. What remains is `d_task` — the agent's actual job of reasoning about build failures and fixing code.

**Result.** blq reduces `chi` on *both axes simultaneously*:

| | World coupling `I(w)` | Decision surface `P(d)` |
|---|---|---|
| Raw Bash | High (raw output cardinality) | High (invoke + parse + reason) |
| blq tools | Low (structured schema) | Lower (reason only) |

The reduction is superlinear by Prop. 4.7 — reducing both axes together saves more than the sum of reducing each independently. But the mechanism is worth being precise about: the world coupling reduction comes from structured output (co-domain funnel), while the decision surface reduction comes from *removing choices the agent doesn't need to make*.

**The multi-agent case.** When Agent A runs a build and Agent B needs results:

- **Without blq:** A passes raw build output through the Harness. A's contribution to `I(w_B)` is the full cardinality of raw output — unstructured, high `chi` contribution. (Study 2, case 2b.)
- **With blq:** A runs the build, blq captures it, B queries `blq errors`. The communication goes through a structured intermediary with bounded schema `K_blq`. (Study 2, case 2a.)

blq is a Harness-mediation point for the build-system-to-agent communication channel. It interposes a co-domain funnel at the boundary, keeping `chi` composition additive where it would otherwise be multiplicative.

**The governance angle.** The computation channel taxonomy (formal companion section 9) classifies by what the tool *can compute*. By that measure, blq's `build` is still level 4 — it executes arbitrary code. But the taxonomy alone misses something: *who decides what gets computed*. With Bash, the agent decides — it constructs the command, chooses the flags, controls the environment. With blq, the agent merely triggers; the infrastructure decides how. This is not a change in computation channel level but a change in *where the decision surface lives* — shifted from the agent (where it must be regulated by characterization) to the infrastructure (where it can be regulated by conventional engineering).

This distinction matters for system design: you don't need to trust the agent's judgment about build invocation if the agent has no judgment to exercise. The build process can be as dangerous as it needs to be, as long as the danger is managed by infrastructure that doesn't require characterization to govern.

---

## Connecting the studies

The three studies form a progression:

1. **Study 1** establishes that the context window creates a ceiling on `I(w)`, making tool restriction maximally effective in the regime where systems are hardest to regulate.

2. **Study 2** shows that inter-agent delegation creates emergent computation channels — two sub-Turing agents compose into a system with Turing-like capability at the delegation boundary. The growth rate shifts from linear to polynomial in total token budget. Co-domain funnels prevent this emergence by decoupling the agents' context windows.

3. **Study 3** demonstrates the concrete pattern: a structured intermediary (blq) drops both axes of `chi` simultaneously — but through two distinct mechanisms. The *output* side is a co-domain funnel (structured build results replace raw text). The *input* side is a decision surface collapse (the agent triggers opaque operations instead of constructing commands). The computation channel level of the underlying build doesn't change — what changes is that the decision surface moves from the agent to the infrastructure, where it can be governed by engineering rather than characterization.

The common thread: **characterization difficulty is the quantity that system architecture manages**. The context window bounds it. Delegation amplifies it (quadratically per agent added). Structured intermediaries restore linear growth. The Harness's job, at every scale, is `chi` management.

An observation that cuts across all three: the framework's claims about dynamics are bounded by token windows. "Divergence" means reaching the regulatory budget before the window is consumed. "Convergence" means the budget holds. The practical question is always about rates within finite bounds, not about infinity.

---

*These studies accompany the [formal companion](formal-companion.md) and the blog series [The Ma of Multi-Agent Systems](00-intro.md).*
