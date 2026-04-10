# The Worst Model Became the Best

*The 3B model couldn't do the job. Then we changed which examples it saw, and it outperformed the 7B. The capability was in the weights the whole time.*

---

## The setup that wasn't working

[Post 2](02-the-lackpy-gambit) tells a tidy story. Take a restricted DSL. Give it to a 3B local model. The model generates valid lackpy programs, the validator checks them, the executor runs them. The round-trip tax disappears because composition happens inside one tool call. Ma at micro scale. [Post 3](03-the-specialization-lives-in-the-language) names the underlying move: the specialization lives in the language, not the model. The dialect is designed to borrow pre-trained familiarity from adjacent domains (CSS selectors, Jupyter cells) so that the 3B model can recognize the grammar rather than learn it under pressure.

That's the argument. The tidy version left out a week of frustration where the argument kept failing in practice.

When we first wired up Qwen 2.5 Coder 3B to generate `ast_select` calls — the [pluckit](../pluckit/index) CSS-style selector DSL for querying code — it didn't work. The model produced syntactically valid Python that parsed fine, but the *selectors* were wrong. It would drop `:not(...)` predicates. It would omit `:has(...)` children. It would confuse `.class` (type) with `#name` (identifier). A selector that should have been `.class .func#__init__:not(:has(.call#super))` came out as `.class .func#__init__`.

And it wasn't random. It was *deterministic*. The same intent produced the same wrong selector, three runs in a row, every time.

We had 20 carefully-crafted examples in the prompt. The constructor case was literally one of them:

```
constructors that don't call super →
  ast_select('src/**/*.py', '.class .func#__init__:not(:has(.call#super))')
```

The model looked at the example and produced a broken version of it.

Worse was the ranking. We benchmarked four models on eight queries:

| Model | Correct |
|---|---|
| qwen2.5-coder:3b | **2/8** |
| qwen2.5:3b | 5/8 |
| qwen2.5:7b | 5/8 |
| qwen2.5-coder:7b | 7/8 |

Qwen 2.5 **Coder** 3B was the *worst* model in the lineup. Worse than the generic 3B. The model specifically trained on code — the one we chose for this task — was the least able to generate valid selectors. That's a confusing result. Code-specialized training should help, not hurt.

We had a choice: escalate to the 7B (doubled parameter count, doubled RAM, slower on laptops), engineer better guidance text, build a multi-stage pipeline, or find out why the 3B-coder was failing so badly.

---

## The diagnosis

The thing that cracked it open was shrinking the prompt.

We took the 20-example prompt and stripped it down to three examples. Just three. One of them was the constructor pattern, exactly as before — same text, same target selector. The other two were loosely related cases demonstrating `:not(:has(...))`.

The 3B-coder produced the correct selector. First try. Three runs in a row.

We ran the full eight-query benchmark with six retrieved examples instead of twenty stuffed ones:

| Model | 20 examples (stuffed) | 6 examples (retrieved) | Delta |
|---|---|---|---|
| qwen2.5:3b | 5/8 | 6/8 | +1 |
| **qwen2.5-coder:3b** | **2/8** | **7/8** | **+5** |
| qwen2.5:7b | 5/8 | 7/8 | +2 |
| qwen2.5-coder:7b | 7/8 | 8/8 | +1 |

Qwen 2.5 Coder 3B went from 2/8 to 7/8. The worst model became tied with the best model. The same weights. The same eight queries. The only difference was which examples accompanied each request.

And the ranking reversed. 3B-coder was the worst model with stuffed prompts. It was the *best* 3B model with retrieved prompts. The model that couldn't do the job was suddenly the right one for it — once the input was shaped correctly.

The capability was in the weights the whole time. It just couldn't reach it.

---

## Why the coder variants suffered most

The bigger the model, the less the retrieval mattered. The smaller and more specialized the model, the more it mattered. The coder variants are the interesting case because they inverted relative to their generalist counterparts.

Here's the mechanism. Code models over-attend to recent token patterns. They're trained to produce syntactically plausible continuations of code, which means they weight the local context heavily — the last few lines of the prompt dominate the next generation. When you stuff twenty examples into a prompt, the last two or three examples disproportionately shape the output. If those trailing examples happen to demonstrate different selector patterns than the one the user wants, the model generates the trailing patterns rather than the relevant one.

The 3B-coder isn't dumb. It's *focused* — aggressively focused on pattern-matching against recent tokens. That focus is a strength when the recent tokens are relevant. It's a liability when the recent tokens are twenty competing examples of which only one matters.

The generic 3B model has more diffuse attention. It's worse at matching any single pattern, but better at averaging across many. That's why generic-3B went from 5/8 to 6/8 with retrieval — a small improvement, because pattern competition wasn't hurting it as much to begin with. It wasn't over-attending to anything.

The 7B models sit in between. More parameters means more capacity to track multiple patterns simultaneously. 7B-coder still gained from retrieval (7/8 → 8/8) but the gain was small because it could mostly handle the twenty-example prompt.

**The model size that benefits most from retrieval is the size that's just barely capable of the task.** The 3B-coder was failing because attention couldn't route to the right pattern. Retrieval routed attention for it. The 7B-coder was succeeding despite attention competition. The 7B-generic wasn't failing hard enough to benefit much.

This means retrieval's value scales inversely with model capability. It's most important exactly where cloud models make least sense — the laptop-scale, privacy-sensitive, self-hosted tier where every optimization matters because there's no option to escalate.

---

## The retrieval itself is boring

The fix doesn't need embeddings, vector databases, or semantic similarity. Keyword matching with synonym expansion worked.

Each example in the bank is tagged with keywords describing what it teaches:

```yaml
- intent: "constructors that don't call super"
  selector: ".class .func#__init__:not(:has(.call#super))"
  tags: [not, has, negation, constructor, init, super, call]

- intent: "functions calling execute without try"
  selector: ".func:has(.call#execute):not(:has(.try))"
  tags: [not, has, negation, call, try, without]

- intent: "functions without returns"
  selector: ".func:named:not(:has(.return))"
  tags: [not, has, negation, return, without, named]
```

At query time, the user's intent gets tokenized and expanded: "constructors that don't call super" → {constructor, init, not, without, no, super, call}. The synonyms are hand-curated. "Without" maps to {not, without, no}. "Static" maps to {static, self, method}. Twenty-odd mappings total.

Score each example by keyword overlap. Take the top N (we use 6). Build the prompt with only those N examples. Send to the model.

That's the entire implementation. It's about 80 lines of Python. No learning, no training, no external services. The synonym table lives in a YAML file and gets updated by hand when new patterns emerge.

It doesn't have to be smart. It has to be *selective*.

---

## What this is (and isn't) at the framework level

This finding slots into the Ma framework cleanly, but in a way that took us a while to see.

Post 6 of the main series defines two quantities:

```
d_total     = const                    (the weights — fixed)
d_reachable = f(d_total, context)      (depends on what enters)
```

The model's total decision surface is fixed. Reachable paths through that surface depend on what the context activates. We [updated that definition](../../ma/06-conversations-are-folds) to note that content matters more than length — a short instruction can prune exploration paths that a full context window of irrelevant content can't.

The retrieval finding is a mechanism-level explanation of that claim. Attention allocation is zero-sum across tokens. More content doesn't expand reachable paths — it *reshuffles* them, and most of the reshuffling is noise for the current query. The 3B-coder's catastrophic failure on stuffed prompts is `d_reachable` collapsing under attention dilution. The recovery with retrieval is `d_reachable` re-concentrating on the relevant patterns.

The gap between `d_total` and `d_reachable` is the Harness's leverage. For frontier models, the gap is small — Opus can route attention to the relevant pattern even amid noise. For small specialized models, the gap is enormous. The 3B-coder had the capability in its weights (2/8 → 7/8 proves it) but couldn't reach it without help. The Harness's job — picking which examples accompany the request — closed the gap.

What this *isn't*: a new framework claim. It's a mechanism for one we already had. The contribution is the demonstration that the leverage is measurable, the fix is cheap, and the effect is dramatic exactly where the framework predicts it should be — at the constrained tier where every other optimization is expensive.

And what this *is*: the first experimental result where the framework's prediction about restriction returned a ranking inversion. Previous experiments showed [cost and reliability differences](../../patterns/01-experimental-foundations) from strategy instructions — the 50-token principle saved 20% for Sonnet and turned Haiku from 40% reliability to 100%. This one showed a capability reversal — the model that was worst became the best. The effect isn't subtle. It's the whole ballgame.

---

## The text-to-DSL twist

Here's what makes this specific to lackpy, and why the finding matters for the gambit.

Lackpy's micro-inferencer isn't generating general-purpose code. It's generating a *DSL call* — `ast_select(...)`, or a lackpy cell that calls `find_definitions(...)`, `read(...)`, etc. The target is narrow. The grammar is strict. The output either parses or it doesn't, either executes or it doesn't.

In code generation terms, this is a hard target. There's no "close enough" — a dropped `:not(...)` predicate produces a *different query*, not a slightly-wrong version of the right query. The `ast_select('.class .func#__init__')` that the 3B-coder produced when it should have generated `.class .func#__init__:not(:has(.call#super))` is a perfectly valid selector. It just returns all constructors, not the ones without super calls. The validator can't catch it. The executor runs it. The outer agent gets a plausible-looking result that answers the wrong question.

This is why retrieval matters *more* for DSL generation than for general code. With general code, a model that produces 90% of the right solution can often be fixed by the next iteration — the remaining 10% is obvious from the error message or the test failure. With DSL generation, 90% of the right selector is a selector that works but returns wrong data. The failure is silent and hard to detect.

Retrieval is the mechanism that gets the model to the *exact* right pattern, not a nearby one. It's the difference between the DSL being useful and being dangerous.

There's a second twist. In lackpy, the DSL call is generated **for use by another agent**. The outer agent (Opus, Sonnet, whatever) calls `delegate("find callers of validate_token")`. The 3B model generates the lackpy cell. The cell runs. The result comes back. From the outer agent's perspective, this is *one tool call* that it's using *as a principle* — "when you want to compose tool calls, use delegate instead."

The outer agent doesn't know the 3B model exists. It doesn't know about retrieval. It doesn't know about the AST validator. From its perspective, `delegate` is a structured tool that takes natural language and returns structured results. The fact that the tool is backed by a retrieval-augmented small model is an implementation detail.

This is the stack:
- The 3B model is inside lackpy
- Lackpy is inside the outer agent's tool set
- Retrieval is inside lackpy's inference pipeline
- The outer agent is outside all of it, calling `delegate(...)` as a principle

Each layer is specified. Each layer has known bounds. The outer agent's trust gap includes lackpy's trust gap, but lackpy's trust gap is tiny because the AST validator is strict and the retrieval-augmented 3B model is reliable (once we fixed the prompt).

This is the ratchet all the way down. The outer agent is a frontier model that the Harness regulates. The outer agent's principle — "use delegate for composition" — is a strategy artifact produced by the ratchet at the outer scale. Lackpy itself is a tool artifact produced by the ratchet. Inside lackpy, the retrieval-augmented 3B model is a *sub*-artifact: it's what makes the lackpy tool actually work at 3B scale instead of requiring a 7B or an API call. Each ratchet turn enables the next level of the hierarchy.

---

## The cascade

Once retrieval works, a deployment pattern becomes cheap: **try the small model first, escalate on failure**. With retrieval:

- qwen2.5-coder:3b hits 7/8 (88%) at 3-5 seconds per query on laptop CPU
- qwen2.5-coder:7b hits 8/8 (100%) at 5-6 seconds per query

If you validate the small model's output against your DSL grammar — for ast_select, parse the selector and check it against the grammar — you can catch the 12% failure rate. Fall back to the 7B only when the 3B's output fails validation. Average latency stays near the small model's; correctness stays near the large model's.

This is the [dispatch hierarchy from post 4](05-the-tool-that-teaches-itself-to-disappear) applied to model selection instead of template selection. The lowest tier runs first. The higher tier runs only on failure. The ratchet promotes successful patterns downward — and in this case, promotes entire model sizes downward. Over time, templates crystallize out of the successful small-model outputs, and even the 3B stops being needed for those patterns. The system eats its own tail.

The 7B exists for the long-tail novel queries. The 3B + retrieval handles the bulk of requests. Templates handle the repeat requests. The model is a vestigial organ — but the retrieval that made the 3B viable is the reason templates ever accumulated enough successful outputs to crystallize in the first place. Without retrieval, the 3B generates too much bad output to produce useful training data, and the ratchet stalls.

---

## What we got wrong

Going in, we thought the fix would be *more* examples, or *better* guidance text, or *structured* planning stages (Plan → Solve → Pick → Restrict). We tried all three:

- **More examples** plateaued at 5/8 around 25 examples, then degraded
- **Better DO/DON'T guidance** fixed some patterns but broke others — telling the model not to drop `:not` predicates made it drop `:has` predicates instead
- **PSPR planning stages** didn't work because the small model couldn't plan, and the plans poisoned the solver

None of those addressed the core problem, which was that the prompt was competing with itself. The fix was to *remove* content, not add it.

The lesson generalizes. When a small model is failing, ask whether the prompt has too much in it before asking whether the model is too dumb. The constraint on tool use at the 3B tier is almost never "the model can't do this." It's "the model can't find the right pattern amid the noise of everything you told it about."

The ratchet applied to *prompt construction* is the same shape as the ratchet applied to tool construction. Start broad. Observe what works. Crystallize the pattern. Remove everything else. Repeat.

Example curation is Harness work. The Harness isn't just deciding which tools to grant and which scope to construct — it's deciding which demonstrations accompany each request. At the frontier-model scale, this matters less because attention is diffuse enough to tolerate noise. At the 3B tier, it's the whole game.

---

## Where this leaves lackpy

The lackpy gambit from [post 2](02-the-lackpy-gambit) depended on the 3B model being able to generate valid programs. For a week, it couldn't. We nearly escalated to 7B as the default and wrote off laptop-scale deployment as "nice in theory."

Retrieval saved the gambit. The 3B is now the primary inference tier. The 7B is a fallback for cases retrieval can't resolve. Templates are the next tier down, promoting successful patterns out of the inference loop entirely. The [disappearing tool architecture in post 4](05-the-tool-that-teaches-itself-to-disappear) is viable because retrieval made the bottom tier work.

The framework claim was "Ma applies at micro scale." The test case was lackpy. The test case almost failed because we didn't yet understand that example curation is part of the Harness's job. Now we do, and the test case holds.

---

*Next: [The Tool That Teaches Itself to Disappear](05-the-tool-that-teaches-itself-to-disappear) — What happens once retrieval makes the 3B reliable: templates crystallize, the ratchet turns, and the model becomes vestigial.*

```{seealso}
- [The Lackpy Gambit](02-the-lackpy-gambit) — The small-model architecture this unblocks
- [The Specialization Lives in the Language](03-the-specialization-lives-in-the-language) — The design claim this post demonstrates empirically: dialect design borrows familiarity, retrieval cues it
- [The Tool That Teaches Itself to Disappear](05-the-tool-that-teaches-itself-to-disappear) — What happens once retrieval makes the 3B reliable: templates crystallize and the model becomes vestigial
- [CSS Selectors for Code](../pluckit/06-css-selectors-for-code) — The ast_select DSL this retrieval work made viable
- [Conversations Are Folds](../../ma/06-conversations-are-folds) — d_reachable as a function of context content, not just length
- [Experimental Foundations](../../patterns/01-experimental-foundations) — Strategy instructions as d_reachable constraints for frontier models; the model-dependent findings
- [Teaching Without Theory](../../fuel/08-teaching-without-theory) — Example curation as Harness work
```
