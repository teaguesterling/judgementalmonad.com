# External Evidence: Crandall, "Same Model, 78% vs 42%"

*Reference document for citing Nate Crandall's harness comparison across the Ma series and Ratchet Fuel.*

**Source:** [Claude Code and Codex Bet on Different Harnesses](https://natesnewsletter.substack.com/p/same-model-78-vs-42-the-harness-made), Nate's Newsletter, March 2026.

---

## Key claims from the article

1. **The same model scored 78% in one harness and 42% in another.** The architectural infrastructure — not the model — determined the outcome. Evaluation processes that compare models without controlling for harness miss the dominant variable.

2. **Five architectural decisions create compounding lock-in:** execution environment (local vs sandbox), memory persistence, tool access, multi-task management, and team dependency accumulation. Each decision builds on the previous, making the choice increasingly irreversible.

3. **A developer built six workflow automation layers over months, each depending on the previous.** Switching harnesses would reset all layers to zero — multiplied across entire engineering teams. This is the switching cost of accumulated configuration.

4. **Claude Code operates within user environments with full machine access, building project memory over time.** Codex works in isolated containers, thinks privately, delivers finished results. Different architectural philosophies with different lock-in profiles.

5. **Hidden economics:** "A $2 billion company spending 100% of its revenue on API costs" — the cost structure of harness selection is often ignored.

---

## How this connects to the Ma framework

### The harness IS the grade

The article's five architectural decisions map directly to the grade lattice:

| Crandall's dimension | Framework concept | Grade axis |
|---|---|---|
| Execution environment (local vs sandbox) | World coupling | W axis |
| Tool access and permissions | Configuration lattice | W + D via tool grants |
| Memory persistence | Conv_State management | Fold model (post 6) |
| Multi-task management | Scope construction | Comonadic extraction (post 3-4) |
| Team dependency accumulation | Configuration ratchet | Specified base growth |

The article is describing the grade lattice in practitioner terms. "Different harness" = different position on the lattice. "78% vs 42%" = the quality consequences of grade differences. "Lock-in" = the monotonically growing specified base.

### The reconciliation: open today, specified tomorrow

The article reads as "open harness beats closed harness." Our pilot reads as "fewer tools can beat more tools." These are not contradictory:

- **Crandall compares harness designs.** Claude Code's specified-but-broad harness beats Codex's specified-but-scoped harness. The framework predicts this: within the specified band, more world coupling is more capability at linear (not superlinear) cost. Claude Code is `(broad, specified)`. Codex is `(scoped, specified)`. Both are characterizable. The broader one gives the model more to work with.

- **Our pilot compares tool configurations within a fixed harness design.** Same permission model, same scope construction. Just: does the agent get bash? For small, well-defined tasks, fewer tools → fewer turns → same outcome → lower cost. The supermodularity cross-term doesn't activate at low W because there isn't much world to interact with.

- **The ratchet connects them.** The open harness (Claude Code) is how you *discover* what tools and configurations work. The accumulated configuration layers (the six workflow layers) are what the ratchet produces. Today's open harness is tomorrow's specified harness. The openness was necessary for exploration; the specification is what made it reliable. You can't skip to the specified version because you don't know what to specify yet.

### The cost question

Crandall mentions "100% of revenue on API costs." Our pilot measured this directly:

| Condition | Outcome | Cost |
|---|---|---|
| A (data channels only) | 48/48 tests passed | $0.67 |
| B (readonly bash) | 48/48 tests passed | $1.63 |
| C (computation channel) | 48/48 tests passed | $1.00 |

Same outcome, 2.4x cost difference. The cost comes from exploration induced by tool availability — the agent explores *because it can*, not because it needs to. This is a concrete operationalization of the supermodularity argument: the cross-term between world coupling and decision surface adds cost even when it doesn't add quality.

The framework predicts that as the ratchet turns (bash patterns → structured tools), both the quality gap between harnesses and the cost gap will change:
- Quality gap narrows (the specified tools handle common cases)
- Cost gap reverses (specified tools are cheaper to operate)
- Lock-in grows (more specified base = more to abandon)

---

## Where to cite in the series

### Already cited (as of 2026-03-21)

| Location | What's cited | Context |
|---|---|---|
| `blog/ma/00-intro.md` | 78% vs 42% finding | Alongside LangChain result as practitioner evidence that harness > model |
| `blog/ma/08-the-specified-band.md` | Claude Code vs Codex as specified band instances | Both in the band; difference is W axis, not D axis |
| `blog/ma/the-configuration-ratchet.md` | Six-layer lock-in | Ratchet consequence: specified base grows monotonically |
| `experiments/pilot-findings.md` | Framing section | Complementary to our pilot: harness design vs tool configuration |

### Recommended for Ratchet Fuel

| Fuel post | What to cite | Why |
|---|---|---|
| **Post 0 (Ratchet Review)** | The 78% vs 42% headline | Opens with practitioner evidence. "Your harness determines your system's grade. Different grade, different outcomes." |
| **Post 1 (Fuel)** | The five architectural decisions as the dimensions the ratchet operates on | Each decision is a point where the system can accumulate specified behavior |
| **Post 2 (Two-Stage Turn)** | The six workflow layers as six turns of the ratchet | Concrete example of the ratchet at team scale. Each layer = explore → crystallize |
| **Post 5 (Closing the Channel)** | Cost comparison from our pilot | "The structured tool costs 60% less per run than the bash equivalent. Same outcome. The channel closure paid for itself on the first day." |
| **Post 8 (Teaching Without Theory)** | Lock-in as feature not bug | The accumulated configuration IS the teaching. "The best documentation makes itself unnecessary" because the ratchet encoded the knowledge into the tool set. |
| **Post 10 (Ratchet Metrics)** | Cost per run as a ratchet health metric | Track cost/outcome ratio over time. If the ratchet is working, cost decreases as the specified base grows. Crandall's "100% revenue on API costs" is what happens when the ratchet isn't turning. |

### Recommended for experimental program

| Experiment | Connection | How to cite |
|---|---|---|
| **Experiment 3 (Phase Transition)** | The article's harness contrast is a natural experiment across computation levels | "Crandall's comparison is an uncontrolled instance of our Experiment 3: different tool configurations, different outcomes. Our experiment controls for model, task, and evaluation method." |
| **Experiment 1 (Supermodularity)** | The cost data from our pilot | "Even at n=1, the cost ratio (2.4x) is consistent with supermodularity: the cross-term between world coupling (file access) and decision surface (bash availability) adds cost beyond the sum of individual contributions." |
| **Hypothesis 5 (Test Detail)** | Not directly relevant | — |

---

## Key quotes for direct citation

> "The same model scored 78% in one harness and 42% in another. Your evaluation process wouldn't catch the difference."

> "One developer built six workflow automation layers over months, each depending on the previous. Switching harnesses would reset all layers to zero — multiplied across entire engineering teams."

> "A $2 billion company spending 100% of its revenue on API costs."

---

*This document is a reference for consistent citation across the project. The article supports the framework's central claims from practitioner evidence. Use it where the series needs grounding in production experience, not just theory.*
