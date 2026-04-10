# The Tool That Teaches Itself to Disappear

*The ratchet applied to lackpy itself. The success metric is how often it doesn't need a model.*

---

## Two ratchets

There are two learning cycles running simultaneously. They operate at different timescales, different costs, and different computation levels. Each one's product is the other's input.

**The macro ratchet** is the outer agent — Opus or Sonnet, working across sessions, learning which tools to use, which strategies work, which patterns recur. Its cycle time is minutes to hours. Its cost is dollars. Its observations come from tool call traces, test results, and conversation history. Agent Riggs sits across sessions, ingesting data from kibitzer, blq, jetsam, and fledgling into a DuckDB store, surfacing ratchet candidates when patterns stabilize. This is the ratchet the rest of the series has been about.

**The micro ratchet** is lackpy's inference pipeline — the 3B model generating programs, the validator accepting or rejecting them, the executor tracing their behavior. Its cycle time is seconds. Its cost is zero (local inference) or fractions of a cent (API fallback). Its observations come from (intent, program, success) triples that accumulate with every `delegate` call.

The macro ratchet discovers that `find_callers` followed by `read` on each result is a useful workflow. It calls `delegate("find callers of validate_token and show the source")` three times in a session. Each time, the micro ratchet generates a program, executes it, and records the trace.

The micro ratchet notices that the same intent pattern produced the same program structure three times, and all three succeeded. It promotes the pattern to a template. Next time the macro ratchet makes the same request, the micro ratchet skips the model entirely.

The macro ratchet's discovery became the micro ratchet's template. The micro ratchet's template became the macro ratchet's reliable tool. Each scale's output feeds the other's input.

---

## The dispatch hierarchy as ratchet prediction

Lackpy's inference pipeline isn't an arbitrary priority list. It's a prediction the framework makes about any system with a learning cycle: **use the lowest computation level that works.**

| Tier | Provider | Computation level | Cost | What it does |
|------|----------|-------------------|------|-------------|
| 0 | Templates | Level 1 (pattern match) | $0, <1ms | Regex match on intent, instantiate stored program |
| 1 | Rules | Level 1 (deterministic) | $0, <1ms | Keyword → program mapping |
| 2 | Ollama | Level 3 (local inference) | $0, ~3-8s | 3B model generates program |
| 3 | Anthropic | Level 3 (API inference) | ~$0.001, ~1-2s | Haiku fallback |

The system tries Tier 0 first. If it matches, no model runs. If it doesn't, Tier 1. Then Tier 2. Then Tier 3. The progression is a ratchet: entries arrive at Tier 3 (expensive, slow, uncertain), get validated through use, and promote toward Tier 0 (free, instant, certain).

The framework predicts this ordering because it follows from the grade lattice. A Tier 0 template match is Level 1 — specified rules over structured data. A Tier 2 model call is Level 3 — an inferencer making decisions from a prompt. Lower levels are cheaper, faster, and more characterizable. The system should always prefer them when they work.

This isn't unique to lackpy. Any system with a learning cycle should develop the same hierarchy. Caches, memoization tables, compiled queries, materialized views — these are all instances of the same pattern: observations at high computation levels crystallize into infrastructure at low computation levels. The ratchet only turns one way — toward more structure, less inference.

---

## Template crystallization

Every successful `delegate` call produces a trace. The trace contains the intent, the generated program, the kit, and a success flag. These traces are the raw material for template promotion.

A template is a (pattern, program) pair:

```yaml
---
name: find-callers
pattern: "find (all )?(callers|usages|references) of {name}"
success_count: 12
fail_count: 1
---
results = find_callers("{name}")
[f"{r['file']}:{r['line']}" for r in results]
```

The pattern is a regex with `{placeholder}` captures. The program is a lackpy program with the same placeholders. When the intent matches the pattern, the template instantiates the program with the captured values. No model. No inference. Just a regex match and a string substitution.

Template promotion has two paths:

**Explicit creation.** The outer agent or the human calls `create(program, kit, name, pattern)` directly. "This program works. Save it." This is the fast path — one successful observation is enough when a human is in the loop.

**Automatic promotion.** [Agent Riggs](https://github.com/teague/agent-riggs) — the cross-session auditor in the Rigged suite — identifies recurring patterns from its DuckDB store. Riggs ingests execution traces from lackpy alongside data from kibitzer, blq, jetsam, and fledgling. Its ratchet candidate identification uses SQL with configurable thresholds:

```sql
SELECT
    intent_normalized,
    program_template,
    count(*) AS successes,
    count(*) FILTER (WHERE NOT success) AS failures,
    count(DISTINCT session_id) AS across_sessions
FROM lackpy_traces
WHERE success = true
GROUP BY intent_normalized, program_template
HAVING successes >= 5 AND across_sessions >= 3
    AND (successes::float / (successes + failures)) >= 0.8
ORDER BY successes DESC
```

The thresholds — frequency ≥ 5, sessions ≥ 3, success rate ≥ 0.8 — require a pattern to be validated across multiple contexts before promotion. The `intent_normalized` field strips specific names and paths, leaving the structural pattern. The `program_template` field replaces the specific values with `{placeholder}` markers. `agent-riggs ratchet candidates` surfaces these; `agent-riggs ratchet promote` registers them as lackpy templates. A human reviews before promotion — Riggs recommends, it doesn't enforce.

Riggs also feeds back into kibitzer through trust-informed mode transitions. It tracks three EWMA windows — immediate (last 2-3 turns), session (~50 turns), and baseline (project lifetime) — and recommends tightening or loosening based on sustained trust trends. This is the cross-session memory the ratchet needs to know when a pattern is genuinely stable versus a fluke.

---

## The convergence

What happens to the fraction of model-generated vs template-served programs over time?

Day 1, every `delegate` call hits the model. There are no templates, no rules. The dispatch hierarchy tries Tier 0 (no matches), Tier 1 (no matches), and falls through to Tier 2 (Ollama) or Tier 3 (API). Every call costs inference time.

But day 1 also produces traces. If the team runs 50 `delegate` calls on day 1, and 30 of them follow 8 distinct patterns, those 8 patterns each have 3-4 successes by end of day.

Day 2, those patterns are approaching the promotion threshold. A few more successful calls and they promote to templates. New patterns still hit the model. But the most common patterns — the ones the team reaches for repeatedly — start serving from Tier 0.

The dynamics follow a power law. A small number of intent patterns account for the majority of calls. The Pareto distribution of tool usage means the top 20% of patterns serve 80% of requests. Once those top patterns crystallize into templates, the model handles only the long tail — genuinely novel requests that don't match any known pattern.

We predict — but haven't yet measured — that the crossover point (where more than half of calls are template-served) arrives within the first week of regular use, assuming 20-50 delegate calls per day. The steady state has 80-90% of calls served by templates, with the model handling only genuinely novel compositions.

This is an empirical prediction. We'll measure it.

---

## The fine-tuning loop

Templates are the fast path. But there's a slower, deeper path available to teams with GPU access.

Every successful trace is a training example: (prompt, program) pair where the prompt is the system prompt + intent and the program is the validated, successfully-executed output. These pairs accumulate in the trace log. They are, by construction, examples of correct lackpy programs — programs that passed validation and produced useful results.

Fine-tune the 3B model on your own composition patterns. The model learns *your* tools, *your* naming conventions, *your* common workflows. The base model writes generic cells. The fine-tuned model writes cells that look like they came from your team.

This is the ratchet eating its own tail. The system produces training data as a byproduct of normal operation. The training data improves the model. The improved model produces better programs. The better programs produce better training data.

The fine-tuning loop is optional. Most teams won't need it — templates handle the common patterns, and the base 3B model handles the rest well enough. But for teams with high volume and diverse tools, fine-tuning closes the gap between "generic code model" and "your team's composition patterns." And the training data is free — it's already being generated.

---

## The disappearing tool

Follow the progression to its conclusion.

Week 1: Every call hits the model. The dispatch hierarchy is a straight pipe to Tier 2. Cost per call: ~3-8 seconds of local inference, or fractions of a cent via API. The tool is useful but slow.

Month 1: The top patterns have promoted to templates. 60-70% of calls serve from Tier 0 in under a millisecond. The model handles the remaining 30-40%. Average cost per call has dropped by more than half. The tool is fast for common operations, slow for novel ones.

Month 3: Template coverage stabilizes at 80-90%. The rules engine handles another 5% (simple keyword patterns that don't need regex). The model runs on maybe 5-10% of calls — the genuinely novel compositions that don't match any known pattern. Average cost per call is dominated by the template lookup.

Steady state: The model is a vestigial organ. It exists for the rare case where someone composes tools in a way nobody has before. For everything else, the dispatch hierarchy resolves at Tier 0 or Tier 1. The Ollama instance sits idle. The tool has taught itself to not need the thing that created it.

This is what the name means. *Lackpy*: Python that lacks. A tool named after what's missing from it. Its roadmap is to lack more — to need less model, less computation, less everything. The ultimate success state is a template lookup table with a forgotten Ollama dependency gathering dust in the optional extras.

---

## The framework prediction

Here's the thing we didn't expect when we started.

The Ma framework was developed to understand multi-agent systems at production scale. Frontier models coordinating through MCP. Organizational structures mapped to Viable System Model components. The scale was teams, sessions, days.

But the framework doesn't say anything about scale. The star topology is substrate-independent. The grade lattice is substrate-independent. The ratchet is substrate-independent. If the architecture applies to any actor, it applies at any *scale* of actor.

Lackpy is the test of that claim. The 3B micro-inferencer is the smallest actor we've applied the framework to. It has zero world coupling. Its decision surface is bounded by an AST whitelist. Its trust gap is tiny. Its ratchet cycle is seconds.

And the framework's predictions hold:
- **Lower Ma → faster ratchet.** The micro-agent crystallizes patterns in hours, not weeks.
- **Lower trust gap → less observation needed.** Five successes is enough for template promotion because the space of possible failures is small.
- **The dispatch hierarchy is the ratchet in code.** Tier 0 < Tier 1 < Tier 2 < Tier 3 maps directly to computation levels 1 < 1 < 3 < 3. The system prefers lower levels. Successful patterns descend.

The most interesting predictions aren't about frontier models on clusters. They're about what happens when you apply the same architecture to the cheapest, smallest, most constrained actors. Where the ratchet cycle is measured in seconds. Where the steady state is templates all the way down. Where the tool teaches itself to disappear.

---

*This concludes The Lackey Papers. The tools are open source — [lackpy](https://github.com/teague/lackpy), [agent-riggs](https://github.com/teague/agent-riggs), [kibitzer](https://github.com/teague/kibitzer), [fledgling](https://github.com/teague/source-sextant), [blq](https://github.com/teague/lq), [jetsam](https://github.com/teague/jetsam). The framework is in [The Ma of Multi-Agent Systems](../../ma/00-intro).*

```{seealso}
- [The Lackpy Gambit](02-the-lackpy-gambit) — The language design and the small-model twist
- [The Worst Model Became the Best](03-the-worst-model-became-the-best) — Why the 3B model was unreliable until we fixed example curation; the prerequisite for the ratchet described here
- [The Configuration Ratchet](../../ma/the-configuration-ratchet) — The ratchet mechanism in full
- [Experimental Foundations](../../patterns/01-experimental-foundations) — Model-aware dispatch and experimental data
- [Ratchet Metrics](../../fuel/10-ratchet-metrics) — Measuring the turn
- [The Organizational Star](../../fuel/09-the-organizational-star) — The star topology in Beer's VSM
```

<!-- No additional references beyond what Posts 1 and 2 established. -->
