# The Specialization Lives in the Language

*Fine-tuning specializes the model. Dialect design specializes the target. The second is cheaper, inspectable, and — at small scale — actually works.*

---

## The move we keep making

[Post 1](01-the-round-trip-tax) showed the protocol overhead that makes structured tools expensive. [Post 2](02-the-lackpy-gambit) showed a way out: restrict Python to a decidable subset, hand it to a 3B model, let a validator and compiler do the safety work. The result is a composite tool that takes natural language and returns structured data, running on a laptop for free.

But that description glosses a move. Why does the 3B model produce lackpy at all? It wasn't trained on lackpy. There's no lackpy corpus. We didn't fine-tune. We sent the model a prompt describing a restricted namespace and asked it to write a Jupyter cell, and it did.

This works because of something the series hasn't named explicitly yet. We're not asking the model to learn a new language. We're asking it to produce a *dialect of something it already knows*. And we're doing that deliberately — the dialect is designed, the restrictions are chosen, and the framing is picked to surface pre-trained familiarity that's already sitting in the weights.

The specialization we want — "produce valid lackpy programs on demand" — doesn't live in the model. It lives in the *language* the model is asked to produce. The model stays general. The language does the specializing.

This is the move that makes the whole small-model thesis viable. Without it, you're back to either using a frontier model for a task that's beneath it, or fine-tuning a small model at considerable cost. With it, you get a free-on-laptop inferencer producing validated output on day one.

---

## The two paths to specialization

When you want a model to do a specific thing reliably, there are two design surfaces you can push on.

**Path A: Specialize the model.** Fine-tune on domain data. Update the weights to encode the patterns you want. This is how `qwen2.5-coder` was built — Qwen 2.5 trained on additional code data until code generation became a first-class capability. Done well, it produces models that are dramatically better than the base at the target task.

The cost is real. You need training data (thousands to millions of examples). You need compute (GPU hours to weeks). You need iteration (the first fine-tune is almost never the last). You need evaluation (does the fine-tune degrade anything else). And you need to redo it every time the base model updates, or every time your domain shifts, or every time you discover a new pattern the fine-tune should handle.

Fine-tuning is appropriate when the target task is too far from anything in the base distribution, or when the domain is stable enough to amortize the cost, or when the baseline is so bad that any improvement justifies the effort. It's not appropriate when you're trying to get a 3B model to generate a DSL you designed last week.

**Path B: Specialize the target.** Instead of changing the model, design the language the model is asked to produce. Choose the grammar to match patterns the model already knows. Choose the framing to borrow familiarity from adjacent domains. Choose the restrictions to eliminate the failure modes you've observed. Build a validator to enforce the contract. The model stays general. The work is done at the language level.

The cost is bounded. You need to design the dialect (thought, not data). You need a validator (tens to hundreds of lines of code). You need retrieval or example curation (small). You iterate on the dialect until the model produces it reliably, which usually takes hours or days, not weeks. And the dialect is a text artifact you can read — no GPU required to understand what it does.

Path B is cheaper, inspectable, and transferable. It's also the path that *fine-tuning depends on*. The `coder` in qwen2.5-coder wasn't fine-tuned to produce Lackpy. It was fine-tuned to produce Python — a language that already existed, with a known grammar, known conventions, and a massive training corpus. The fine-tuning specialized the model to a pre-existing target language. Someone else did the language design work long before the fine-tune started.

If you're going to build on that, you can build at the language level too.

---

## Borrowing pre-trained familiarity

Here's the specific move that makes Path B work at 3B scale.

A well-designed dialect doesn't introduce new patterns. It *surfaces* patterns the model has already seen millions of times in training and channels them toward a new purpose.

**Pluckit's CSS selectors.** The target language is `.class .func#__init__:not(:has(.call#super))`. Nothing in any training corpus contains this exact string — it's querying Python code, not HTML — but every piece of web dev documentation, every Stack Overflow CSS question, every JavaScript DOM manipulation example, every framework styling guide contains the grammar: dot for class, hash for id, descendant combinator, `:not()`, `:has()`, attribute brackets. The grammar is familiar down to the punctuation. What's unfamiliar is the domain.

Asking a 3B model to produce `.func` when it means "a function definition" is not teaching it CSS. It's inviting it to use CSS grammar it already knows for a new purpose. The dialect borrows familiarity.

**Lackpy's Jupyter cells.** A Jupyter cell is a restricted Python program: no imports (those go in earlier cells), no function definitions (those go in library code), just calls to pre-loaded functions and data manipulation. Every data science tutorial, every machine learning notebook, every research paper's supplementary material contains cells of exactly this shape. The model has seen more Jupyter cells than it has seen anything else about Python in a restricted form.

Asking a 3B model to produce a lackpy program isn't teaching it a new subset of Python. It's framing the task as "write a Jupyter cell using this namespace" — a task the model has seen in its training data thousands of times. The framing borrows familiarity.

**The general principle.** If you're designing a dialect for a small model to produce, pick a surface syntax the model has deep exposure to. CSS selectors work because every web developer's code has been scraped. SQL-style queries work because every database tutorial has been scraped. S-expressions work for Lisp-trained models. JSON structures work for anything. Jupyter cells, markdown tables, regular expressions — all of these are patterns the model has seen at volume, with consistent structure, in varied contexts.

The dialect's *domain* can be new. The dialect's *shape* must be old.

This is why pluckit selects `ast_select('.class .func#__init__')` instead of `find_node(type='class', has_child=dict(type='function', name='__init__'))`. Both are structured DSLs. Both parse to the same AST. Both are equally decidable. But the first one borrows from CSS — a grammar the model has seen millions of times — and the second one invents structure the model has to learn from the prompt. At 3B scale, the difference determines whether the model can produce valid output at all.

---

## The dialect's job is to be recognized

There's a deeper reason borrowing works.

A small model has limited capacity for in-context learning. When you show it a new grammar in the prompt — "here's the syntax, here are five examples, now produce something similar" — the model has to use working memory (attention over the prompt) to hold the grammar while it generates. Every token spent on grammar is a token not spent on the problem.

When the dialect borrows familiarity, the grammar doesn't need to be held in attention. The model has already seen it millions of times during training. The patterns are encoded in weights, waiting to be activated. The prompt's job is to *cue* the encoded patterns, not *introduce* new ones. Attention stays free for the actual query.

This is why the [retrieval finding in post 4](04-the-worst-model-became-the-best) is so dramatic at the 3B tier. The 3B-coder's problem wasn't that it couldn't do the task — the capability was in the weights. It was that twenty competing examples diluted attention, and the model couldn't route activation to the right pattern. With six retrieved examples, all reinforcing the same cue, attention concentrated and the right pattern fired. Retrieval works because it sharpens the cue. The cue works because the pattern it points at is already there.

Fine-tuning would solve the same problem by baking the pattern more deeply into the weights. Retrieval solves it by shaping the context to surface the weakly-encoded pattern. Dialect design solves it one level up, by choosing a pattern that's already strongly encoded so retrieval has something to surface.

Each level is a different grade of solution:

- **Fine-tuning**: change `d_total` (the weights). Expensive. Permanent. Requires training infrastructure.
- **Retrieval**: shape the context to change `d_reachable` (which paths activate). Cheap. Per-query. Requires an example bank.
- **Dialect design**: pick a target language where `d_reachable` is already high for the patterns you want. Cheapest. Design-time decision. Requires taste and domain knowledge.

Dialect design is the cheapest because it happens before the model runs. The work is done in the language definition, not in the inference pipeline.

---

## What this buys you

Path B gives you several things that Path A doesn't.

**Inspectability.** The dialect is text. The grammar is a file. The restrictions are documented. You can read them, reason about them, change them. You cannot read weights; you can only test them. When pluckit's grammar changes, every collaborator can see what changed and why. When a fine-tune changes, you have to run benchmarks to find out.

**Transferability.** A well-designed dialect works across models. Pluckit's CSS selectors should work on any code-trained model because every code model has seen CSS. Qwen 2.5 Coder 3B, Llama 3 8B, Mistral 7B, Gemini Nano — they've all seen CSS selectors in training. The dialect is a contract that any model capable of producing valid CSS can participate in. Fine-tuning produces a specialized model that only works if that specific model is deployed.

**Cheap iteration.** When the dialect doesn't work, you edit the grammar. You add a keyword, remove a failure-prone construct, tighten the validator. You redeploy and test. The cycle is minutes to hours. When fine-tuning doesn't work, you collect more data, retrain, evaluate. The cycle is days to weeks.

**Decidability.** The dialect is designed, so its properties are designable. Lackpy is decidable because we chose to forbid `while` and `def`. A general fine-tuned Python model produces Turing-complete programs — the model's fluency doesn't tell you anything about the program's properties. With dialect design, you can build decidability into the target. The validator can analyze any program before execution. Rice's theorem doesn't apply because the language isn't Turing-complete.

**Composability with the Harness.** The validator is a Harness component. It checks programs against the grammar before execution. It reports specific errors. It can be extended. This means the Harness can make guarantees about what the model produces — not statistical guarantees ("the model usually writes safe code") but structural guarantees ("this program cannot access the network because the namespace doesn't contain a network tool"). Fine-tuning never gives you this. You can fine-tune a model to be safer, but you can't prove it is.

---

## When Path B doesn't work

Two cases where dialect design fails.

**The task has no grammatical target.** Some tasks are "write a correct answer in natural language" or "summarize this document" or "respond appropriately to this conversation." There's no dialect to design — the output is free-form text, judged by criteria that aren't grammatical. For these tasks, Path A (better model, possibly fine-tuned) is the only path. Dialect design has nothing to bite on.

**The target is genuinely novel.** If you're asking the model to produce a language that resembles nothing in its training corpus — a new formal notation, an obscure DSL, a made-up grammar — then there's no familiarity to borrow. The model has to learn the dialect from the prompt, which is expensive in attention and unreliable at small scale. You're either fine-tuning or using a bigger model.

Both failure modes share a shape: the model isn't being asked to re-use something it already knows. When that's the situation, the dialect-design move doesn't help and you have to go back to specializing the model.

Most code tool use doesn't live in either failure mode. The tasks are "query code for structural patterns," "compose tool calls with data flow," "transform one structured format to another." These are all expressible in dialects that borrow familiar grammar from training corpora. Path B applies to most of them.

---

## Beer's variety attenuation, applied to language

The framework's cybernetics strand gives this a name.

Beer's *variety engineering* says a regulator's work is to manage the variety (the count of distinguishable states) of the system it controls. Too much variety overwhelms the regulator. Not enough variety makes the system useless. The regulator's job is to attenuate incoming variety to a manageable level without destroying the system's ability to do its job.

Dialect design is variety attenuation applied to language. The outer agent receives natural language from the human — maximally varied. It produces a structured tool call — already attenuated, because the tool schema restricts what calls are valid. The inner model receives the tool call and produces a dialect program — attenuated further, because the dialect's grammar restricts what programs are valid. The executor receives the program and produces structured data — attenuated again, because the execution produces typed output.

Each tier attenuates. Each tier's output is narrower than its input. The narrowing is chosen, not accidental. The Harness designs each narrowing step to keep the regulator's job tractable at that tier.

The insight that made this whole series possible: **the designed dialects are the attenuation steps**. Without them, each tier would receive the previous tier's full variety, and the regulator would have to handle more than it can. With them, each tier's input variety is bounded, and the regulator's work at that tier is proportional to the designed dialect's complexity, not to the full space of possible inputs.

This is why dialect design is load-bearing for lackey. The 3B model couldn't handle full Python. Nobody could design a regulator for arbitrary Python that runs on a laptop. But the 3B model can handle lackpy, because lackpy is designed to be exactly as varied as the 3B model can reliably produce — and the validator is designed to be exactly as complex as the regulator can handle. The variety budget is distributed across the stack intentionally.

---

## The ratchet target

Pulling this together: **dialect design is how you choose the target for the ratchet to converge on**.

The ratchet moves behavior from high-ma exploration to low-ma infrastructure. It needs something to converge toward. For frontier models, the target is structured tool calls — the ratchet moves bash patterns into MCP tools. For the small-model tier, the target is a dialect — the ratchet moves natural language into dialect programs, and dialect programs into templates.

Without the dialect design move, the ratchet at small scale has no target. There's no language that the 3B model is reliably capable of producing. Every attempt to crystallize a pattern runs into the model's unreliability. The templates never accumulate because the initial inferences are too noisy.

With the dialect design move, the ratchet has a target the 3B model can hit. Programs accumulate. Successful patterns promote to templates. The model's role shrinks. Eventually, the model is a backup for the long tail of novel requests while templates handle the common cases.

This is why the ratchet works at the small-model tier: not because small models got better, but because the Harness learned to design targets they could hit. The specialization that would have to live in a fine-tuned model lives instead in the language the model is asked to produce. The language is cheaper to iterate on, cheaper to inspect, and cheaper to deploy.

At frontier scale, dialect design is an optimization. At 3B scale, it's the thing that makes the whole approach viable.

---

*Next: [The Worst Model Became the Best](04-the-worst-model-became-the-best) — The empirical demonstration: dialect design plus retrieval inverted the model ranking. The 3B-coder that couldn't produce valid selectors became the best 3B model in our lineup once we shaped the prompt to surface the right patterns.*

```{seealso}
- [The Lackpy Gambit](02-the-lackpy-gambit) — The concrete implementation: restricted Python + Jupyter framing + 3B model
- [CSS Selectors for Code](../pluckit/06-css-selectors-for-code) — The pluckit dialect: CSS grammar for code structure
- [The Space Between](../../ma/02-the-space-between) — Ma as the space between input and output; dialect design is narrowing the output space
- [The Specified Band](../../ma/08-the-specified-band) — Why decidability matters; dialect design is how you get it at small scale
- [The Configuration Ratchet](../../ma/the-configuration-ratchet) — The mechanism that needs a target to converge on
```
