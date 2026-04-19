# Training Before Shipping

*How to fine-tune a model on an API that doesn't exist yet.*

---

## The backwards ratchet

Normally the learning cycle is: ship tool → users produce traces → traces become training data → model improves. The tool has to exist before the training starts.

But if the API spec is precise enough — if the type signatures, composition rules, and selector vocabulary fully define the space of valid programs — you can skip ahead. Generate the training data from the spec. Train the model. Ship the tool with a model that already knows its API.

This is the ratchet running in reverse: instead of crystallizing observations into templates, you're crystallizing a *design* into training examples. The spec is the observation. The synthetic data is the template. The fine-tuned model is the result.

It works because the target language — pluckit chains — is *small*. The selector vocabulary has ~20 node types, ~10 pseudo-selectors, and a few combinators. The operations number ~60. The composition rules fit on one page. The space of valid 1-5 line chains is large but enumerable. This isn't "teach a model to program." It's "teach a model a specific API."

---

## The three-stage pipeline

### Stage 1: Chain generation (no model needed)

Sample valid chains from the composition rules.

**Step 1: Choose a chain shape.** The composition rules define which types flow into which operations. Sample a sequence:

```
Shape: select → filter → mutation → delegate → save
Types: Selection → Selection → Selection → Selection → None
```

**Step 2: Fill the selectors.** Sample from the vocabulary:

```python
# Node types × name patterns × attribute filters × pseudo-selectors
selectors = [
    '.fn#validate_token',
    '.fn:exported',
    '.fn[name^="test_"]',
    '.cls#AuthService .fn',
    '.fn:has(.call#print)',
    '.call[name*="query"]',
    # ... combinatorial expansion
]
```

**Step 3: Fill the operations.** Each operation has a signature. Sample valid arguments:

```python
# .addParam() takes a parameter spec string
params = ['timeout: int = 30', 'log_level: str | None = None', 'dry_run: bool = False']

# .guard() takes an exception type and a strategy
guards = [('DatabaseError', 'log and reraise'), ('TimeoutError', 'retry 3 times')]

# .rename() takes a new name
renames = [('validate_input', 'check_input'), ('process', 'transform')]
```

**Step 4: Assemble the chain.**

```python
chain = "select('.fn:exported').addParam('timeout: int = 30').black().test().save('feat: add timeout')"
```

**Step 5: Validate.** Parse the chain, check that each operation's input type matches the previous operation's output type. Reject invalid compositions. This is a type-check, not an execution — no pluckit implementation needed.

This stage is fully deterministic. A Python script generates thousands of valid chains per minute.

### Stage 2: Intent generation (small model or templates)

Each chain needs a natural language intent. This is the one step that benefits from a model — but a small one, because the chain is the source of truth and the intent just describes it.

**Approach A: Template-based (no model)**

```python
INTENT_TEMPLATES = {
    'select.filter': 'find all {node_type}s where {predicate}',
    'select.addParam.save': 'add {param} to all {selector} functions',
    'select.rename': 'rename {old_name} to {new_name} across the codebase',
    'select.similar.refactor': 'extract the common pattern from {selector} functions',
    'select.guard': 'add {exception} handling to all {selector} calls',
    'select.filter(coverage).filter(failures)': 'find undertested code that has failed recently',
    'select.callers.update': 'propagate {change} through call sites',
    # ...
}

def generate_intent(chain_shape, params):
    template = INTENT_TEMPLATES[chain_shape]
    return template.format(**params)
```

This produces mechanical but accurate intents. Good for volume. Lacks natural variation.

**Approach B: Model-paraphrased (Haiku or 3B)**

Take the template-generated intent and ask a small model to paraphrase it:

```
Template: "add timeout: int = 30 to all exported functions"

Paraphrases:
- "add an optional timeout parameter to every public function"
- "all exported functions should accept a timeout"
- "make every public function support a timeout argument, default 30 seconds"
```

This adds natural variation — the kind of variation real users would produce. The model doesn't need to understand pluckit. It needs to rephrase a sentence.

**Approach C: Chain-to-intent (reverse generation)**

Give a model the chain and ask "what would a developer say to produce this?"

```
Chain: select('.fn').filter(fn: fn.callers().count() == 0).filter(fn: fn.history().last_year().count() > 0)
Intent: "find functions that nobody calls anymore but were used within the last year"
```

This is a summarization task. A 3B model can do this — the chain is short, the semantics are readable from the API names. Haiku does it better. Either is cheap.

### Stage 3: Validation and filtering

Not all generated pairs are good training data. Filter:

1. **Type-check the chain.** Does each operation's output type match the next operation's input type? Reject invalid compositions.
2. **Dedup the intents.** If 50 chains produce nearly identical intents, keep the 5 most diverse chains.
3. **Reject trivial chains.** Single-operation chains (`select('.fn').text()`) aren't interesting enough to fine-tune on — the base model already handles these.
4. **Reject implausible intents.** If the intent template produced "find all functions with more than 0 parameters" — that's technically valid but nobody would ask for it.
5. **Balance the dataset.** Ensure representation across operation categories: queries, mutations, delegates, cross-dimensional, history, behavior. Don't over-index on the easy ones.

---

## The training recipe

### Dataset structure

```json
{
    "messages": [
        {
            "role": "system",
            "content": "Generate a pluckit chain. Use the pre-loaded namespace:\n  select(selector), source(glob), blq.event(id), blq.run(id)\n  .find(), .filter(), .containing(), .at_line(), .ancestor()\n  .replaceWith(), .addParam(), .prepend(), .append(), .wrap()\n  .rename(), .extract(), .move_to(), .guard()\n  .test(), .black(), .ruff_fix(), .save()\n  .callers(), .callees(), .similar(), .isolate()\nOutput ONLY the chain, no explanation."
        },
        {
            "role": "user",
            "content": "add an optional timeout parameter to all public functions, default 30 seconds"
        },
        {
            "role": "assistant",
            "content": "select('.fn:exported')\n    .addParam('timeout: int = 30')\n    .test()\n    .save('feat: add timeout parameter')"
        }
    ]
}
```

The system prompt lists the pluckit namespace including the new methods (`.containing()`, `.at_line()`, `.ancestor()`) and blq entry points (`blq.event()`, `blq.run()`). The model generates chains that look like the jQuery it's been trained on millions of times — a ~200-line purpose-built chain DSL parser interprets the JS-style syntax and maps it to Python execution. No Node.js runtime needed.

The user message is the intent. The assistant message is the chain.

### Training configuration

**Base model:** Qwen 2.5 Coder 3B (same model lackpy uses for general code generation).

**Dataset size:** 5,000-10,000 synthetic pairs is likely sufficient for a 3B model learning a small API. The space of valid chains is constrained enough that coverage doesn't require millions of examples.

**Fine-tuning method:** LoRA or QLoRA (fits in consumer GPU memory). Full fine-tuning is overkill for teaching a small API to a model that already understands Python.

**Epochs:** 2-3. Small API, risk of overfitting if you go further.

**Validation set:** 500 held-out pairs, hand-reviewed for quality. Also include 100 "adversarial" pairs — intents that are plausible but require operations outside the API. The model should generate the closest valid chain, not hallucinate operations.

### What the fine-tuned model learns

The base Qwen 2.5 Coder 3B already knows Python syntax, function calls, chaining. Fine-tuning teaches it:

1. **The vocabulary.** `.fn`, `.cls`, `:exported`, `:has()`, `#name` — these are pluckit-specific strings that don't appear in general Python training data.
2. **The composition rules.** `.filter()` chains after `.find()`, `.test()` is terminal, `.addParam()` chains with other mutations. The model learns which sequences are valid.
3. **The mapping from natural language to selectors.** "public functions" → `.fn:exported`. "database calls" → `.call[name*="query"]`. "functions that return None" → `.fn:has(.ret > .none)`.
4. **The idioms.** Common patterns like select → filter → mutate → test → save. The model learns these as units, not as individual operations.

What it does NOT need to learn: Python syntax (already knows it), what ASTs are (irrelevant to generation), how DuckDB works (transparent to the chain), what the operations do internally (the model generates chains, it doesn't execute them).

---

## From synthetic to real

The synthetic dataset bootstraps the model. But the real training data comes from usage — the same fine-tuning loop described in [The Tool That Teaches Itself to Disappear](../lackey/05-the-tool-that-teaches-itself-to-disappear).

Once pluckit ships:

1. Users compose chains interactively or through lackpy delegation.
2. Successful chains produce traces: (intent, chain, success).
3. Agent Riggs identifies high-confidence traces (frequency ≥ 5, sessions ≥ 3, success rate ≥ 0.8).
4. Promoted traces join the training set.
5. Periodic re-fine-tuning incorporates real-world patterns.

The synthetic data teaches the API. Real data teaches the idioms — the patterns your team actually uses, the selectors that matter for your codebase, the mutation sequences that come up in your workflows.

The two sources are complementary:

| Source | What it teaches | Volume | Quality |
|---|---|---|---|
| Synthetic (from spec) | API vocabulary, composition rules, selector language | High (thousands) | Mechanical but correct |
| Real (from traces) | Team idioms, common workflows, natural intent phrasing | Low initially, grows | High — validated by execution |

Over time, the real data dominates. The synthetic data is scaffolding. The model learns your team's dialect of pluckit the same way it would learn any codebase's conventions — from examples.

---

## Error fingerprint training

A new category of training data: error event → fix chain.

```json
{
    "messages": [
        {
            "role": "user",
            "content": "Fix build error: TypeError in validate_token at line 47, expected str got None"
        },
        {
            "role": "assistant",
            "content": "blq.event('build:42:error_123')\n    .select()\n    .replaceWith('return None', 'raise ValueError(\"invalid\")')\n    .test('tests/test_auth.py')\n    .save('fix: validate_token raises')"
        }
    ]
}
```

This is the training data that enables the error-fixes-itself ratchet:

```
Error event (blq/duck_hunt)
    → compound selector (auto from event metadata)
    → pluckit chain (lackpy, 3B, local, $0)
    → execution (select → replace → test → save)
    → trace (event_id + chain + diff + test_result)
    → Riggs fingerprint (error pattern → fix pattern)
    → next occurrence: Tier 0 (no model, no human)
```

The error fingerprint is the trigger. The pluckit chain is the response. The model learns to translate error descriptions into event-selector + fix chains. The second time the same error pattern occurs, it's fixed automatically — the [next post](05-the-error-that-fixes-itself) develops this fully.

---

## What this means for the Retritis suite

The fine-tuning pipeline connects every piece:

```
pluckit API spec                              (this post)
    → synthetic training pairs                (chain generation)
    → fine-tuned Qwen 2.5 Coder 3B          (LoRA)
    → lackpy Tier 2 provider                  (Ollama, local, $0)
    → pluckit chains from intent              (runtime)
    → execution traces                        (observation)
    → Agent Riggs template promotion          (crystallization)
    → lackpy Tier 0 templates                 (zero-cost reuse)
    → back into the training set              (re-fine-tuning)
```

The spec seeds the model. The model generates chains. The chains produce traces. The traces promote to templates AND feed back into training. The model gets better. The templates get more coverage. The model gets called less.

Two convergence forces, pushing in the same direction:
- **Templates** reduce model calls (Tier 0 serves instead of Tier 2)
- **Fine-tuning** improves model calls (fewer validation failures, better chain quality)

Both are ratchets. Both only turn one way. The system gets better at generating pluckit chains whether or not anyone deliberately improves it — the improvement is a byproduct of normal usage.

And it all starts with the spec.

**Update:** This pipeline is now being built concretely. [squackit](https://github.com/teague/squackit) — the MCP server and CLI that wraps pluckit and fledgling — ships 93 curated examples across 45 tools, each tagged with semantic categories for retrieval-aware training. The training data pipeline design documents the path from curated examples → intent generation (larger model) → model attempts (target model) → mechanical validation → preference pairs for DPO fine-tuning. Target: 500-1,000 intents, 1,000-5,000 training pairs. The synthetic-from-spec approach described above is being complemented by curated-from-usage examples — both feeding the same fine-tuning loop.

---

```{seealso}
- [The pluckit API](03-the-api) — The spec this pipeline trains on
- [The Lackpy Gambit](../lackey/02-the-lackpy-gambit) — The micro-inferencer architecture
- [The Tool That Teaches Itself to Disappear](../lackey/05-the-tool-that-teaches-itself-to-disappear) — Template crystallization from traces
- [The Configuration Ratchet](../../ma/the-configuration-ratchet) — The theoretical mechanism
```
