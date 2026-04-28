# Retrieval Beats Stuffing

*When you give a small model twenty examples, it attends to none of them.*

---

## The observation

We were teaching `qwen2.5-coder:7b` to write CSS-style AST selectors — a compact DSL for querying code structure. The task: given a natural language intent ("find constructors that don't call super"), produce a correct `ast_select` call.

Small models handle simple patterns but struggle with combinations. The usual remedy is more examples — show the model every pattern it might need and let it pick. We built a prompt with 20 examples covering property selectors, descendant combinators, containment checks, negation, attribute chaining, and scoped queries. Accuracy plateaued at **7/8** on our test set. No matter how we reordered or reworded, one case kept failing: constructors that don't call super.

The pattern was exactly in the prompt:

```
constructors that don't call super →
  ast_select('src/**/*.py', '.class .func#__init__:not(:has(.call#super))')
```

But the model produced:

```
ast_select('src/**/*.py', '.class .func#__init__')
```

It dropped the `:not(:has(.call#super))` part — the exact thing the example demonstrated. Not once, but deterministically across three runs. When we ran the same query with a short prompt containing only three examples (one of which was the constructor pattern), the model got it right every time.

**The model wasn't lacking information. It was drowning in it.**

## The fix

Instead of stuffing every example into the prompt, retrieve only the relevant ones. For each query:

1. Tag each example in the bank with keywords describing what it teaches.
2. Expand the user's intent into a keyword set (with synonym substitution — "without" → {"not", "without"}, "static" → {"static", "self", "method"}).
3. Score each example by keyword overlap and take the top N.
4. Build the prompt with only those N examples.

For the constructor case, the retrieval surfaced exactly the right examples in the right order:

```
constructors that don't call super → .class .func#__init__:not(:has(.call#super))
functions calling execute without try → .func:has(.call#execute):not(:has(.try))
functions without returns → .func:named:not(:has(.return))
constructors → .class .func#__init__
```

The first three all demonstrate `:not(:has(...))` — the pattern the model was dropping. With 20 examples, most of them involve other patterns (attributes, descendants, properties) that compete for the model's attention. With 6 examples all loosely related to negation and constructors, the model has no competing patterns to over-generalize from.

The result: **8/8, deterministic across three runs.**

## The bigger pattern

The interesting effect wasn't just the jump from 7/8 to 8/8 on the best model. It was what happened across the full model lineup:

| Model | 20 examples (stuffed) | 6 examples (retrieved) | Delta |
|---|---|---|---|
| qwen2.5:3b | 5/8 | 6/8 | +1 |
| qwen2.5-coder:3b | 2/8 | 7/8 | **+5** |
| qwen2.5:7b | 5/8 | 7/8 | +2 |
| qwen2.5-coder:7b | 7/8 | 8/8 | +1 |

The biggest winner was `qwen2.5-coder:3b` — jumping from 2/8 to 7/8 with the same examples, just filtered. That model was catastrophically bad at the stuffed prompt; with retrieval it nearly matched the 7b model.

The coder variants benefit most from focused prompts. They over-attend to recent tokens and are more susceptible to pattern competition. Non-coder models are more evenly distributed but still lose accuracy in long prompts. At every size, retrieval helped. At the size where it mattered most (the small, specialized model), it was transformative.

## Why this matters for ma

The framework we've been building treats the Inferencer as a function with fixed grade — same weights, same decision surface, regardless of context. What changes turn-to-turn is what the Harness constructs as input: the tools granted, the context provided, the history included.

Context management is the most leveraged thing the Harness does. The naive interpretation is "more context = more capability." That's true up to a point and then it isn't. A transformer's decision surface `d_total` is fixed, but `d_reachable` depends on what activates, and activation has limited budget. Too much input doesn't expand what the model can do — it reshuffles which paths activate, and most of the new activations are noise for the current query.

The conventional wisdom about few-shot prompting is "show the model the pattern you want." That's correct. What gets underspecified is how many patterns you can show at once before the attention budget dilutes. The answer, empirically, is: fewer than you'd think. Somewhere between 3 and 10 for tasks requiring precise combinatorial output. More than that and accuracy peaks early then degrades.

The corollary is that **example curation is a form of Harness work**. The Harness isn't just deciding which tools to grant; it's deciding which demonstrations accompany the request. The composite entity's effective grade at turn N depends not just on the tool set but on what the tool set is illustrated with. Retrieval-augmented prompting is the Harness doing its job — constructing the token window deliberately rather than stuffing it.

This reframes few-shot prompting. It's not "show the model N examples and hope it picks the right one." It's "predict which examples will be load-bearing for this query, and show only those." The prediction step doesn't need to be fancy — keyword overlap with synonym expansion worked for us. The key is that it runs *before* the model sees the prompt, not *inside* the model's attention.

## The cascade strategy

Once retrieval is in place, a new deployment pattern becomes cheap: **try the small model first, escalate on failure**. With retrieval:

- `qwen2.5-coder:3b` hits 7/8 (~88%) at 3-5 seconds per query
- `qwen2.5-coder:7b` hits 8/8 (100%) at 5-6 seconds per query

If you validate the small model's output against your domain (for ast_select, that means parsing the generated selector and checking it against the grammar), you can catch the ~12% failure rate and fall back to the larger model. Average latency stays near the small model's; correctness stays near the large model's.

This is the shape of tool-composition work at the small-model tier: not "make the model smarter" but "make the Harness more deliberate." The interesting question isn't how big the model needs to be. It's how focused you can make its input.

## What we got wrong

Going in, we thought the fix would be *more* examples, or *better* guidance text, or *structured* planning stages (Plan → Solve → Pick → Restrict). We tried all three:

- **More examples**: plateaued at 5/8 around 25 examples, then degraded
- **Better DO/DON'T guidance**: fixed some patterns but broke others
- **PSPR planning stages**: the small model couldn't plan, and the plans poisoned the solver

None of those addressed the core problem, which was that the prompt was competing with itself. The fix was to *remove* content, not add it.

The lesson generalizes: when a small model is failing, ask whether the prompt has too much in it before asking whether the model is too dumb. The constraint on tool use at the 3b-7b tier is almost never "the model can't do this." It's "the model can't find the right pattern amid the noise of everything you told it about."

---

*From [lackpy](https://github.com/teaguesterling/lackpy) experiments, April 2026.*
