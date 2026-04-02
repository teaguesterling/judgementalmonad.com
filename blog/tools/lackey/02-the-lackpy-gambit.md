# The Lackpy Gambit

*Take Python, subtract the dangerous parts. Then subtract the model.*

---

## The subtraction

Start with Python. All of it. Every construct in the language, every builtin, every import path. Now remove things.

Remove `import`. No module loading, no access to the standard library, no reaching out to the filesystem through `pathlib` or the network through `urllib`. The program's universe is what you give it.

Remove `def`, `class`, `lambda`. No function definitions, no closures, no objects. The program can *call* functions — but only the ones you provide. It can't create new ones.

Remove `while`. No unbounded iteration. `for` stays — but it can only iterate over finite collections returned by tool calls or builtins like `range`. The loop's iteration count is bounded by data that exists before execution starts.

Remove `try`/`except`. No exception swallowing. If a tool call fails, the failure propagates. The outer system sees it. The program can't hide errors from the Harness.

Remove `eval`, `exec`, `open`, `__import__`, `getattr`, `setattr`. No runtime code generation, no file handles, no reflection, no attribute introspection.

What's left?

```python
# Assignment
results = find_definitions("validate")

# Tool calls
content = read("src/parser.py")

# For-each over finite results
for defn in results:
    source = read(defn["file"])

# Conditionals
if len(results) > 0:
    first = results[0]

# F-strings
summary = f"Found {len(results)} definitions"

# Comprehensions
names = [d["name"] for d in results if d["type"] == "function"]

# The last expression is the output
names
```

That's a program. It composes tool calls with data flow between them. It iterates. It filters. It builds structured output. And it parses with `ast.parse()` — it's valid Python, because it *is* Python. Just less of it.

Here are the concrete sets from the implementation:

```python
ALLOWED_NODES = {
    # Structural
    ast.Module, ast.Expr, ast.Assign, ast.AugAssign,
    ast.For, ast.If, ast.With,

    # Expressions
    ast.Call, ast.Name, ast.Attribute, ast.Subscript,
    ast.List, ast.Dict, ast.Tuple, ast.Set,
    ast.ListComp, ast.DictComp, ast.SetComp,
    ast.Compare, ast.BoolOp, ast.UnaryOp, ast.BinOp,
    ast.JoinedStr, ast.FormattedValue,  # f-strings
    ast.Constant, ast.Starred, ast.Slice,
    ast.Lambda,                          # restricted: key= argument only

    # Comprehension internals
    ast.comprehension, ast.IfExp,

    # Function call internals
    ast.keyword, ast.arguments, ast.arg,

    # Context + operators
    ast.Load, ast.Store, ast.Del,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.FloorDiv,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
    ast.And, ast.Or, ast.Not, ast.USub, ast.UAdd,
}

FORBIDDEN_NODES = {
    ast.Import, ast.ImportFrom,           # no module loading
    ast.FunctionDef, ast.AsyncFunctionDef, # no function creation
    ast.ClassDef,                          # no class creation
    ast.While,                             # no unbounded iteration
    ast.Try, ast.ExceptHandler,            # no exception swallowing
    ast.Raise,                             # no exception raising
    ast.Global, ast.Nonlocal,              # no scope escape
    ast.Yield, ast.YieldFrom,              # no generators
    ast.Await, ast.AsyncFor, ast.AsyncWith, # no async
    ast.Assert,                            # outer agent evaluates
    ast.Delete,                            # no del statements
    ast.Match,                             # no structural pattern matching
}
```

The `ALLOWED_NODES` set is a whitelist — anything not in it is rejected. The `FORBIDDEN_NODES` set exists for documentation and error messages. The whitelist is the authority.

One design decision emerged during implementation: `Lambda` is allowed but *only* as a `key=` keyword argument — `sorted(items, key=lambda x: x["name"])`. The validator enforces this with a custom rule that rejects lambdas appearing anywhere else in the AST. Without this, the 1.5B model's most common failure mode was generating `sorted()` calls without a way to specify sort keys. We also added a `sort_by` builtin as a lambda-free alternative: `sort_by(items, "name")`. Both solve the same problem — the lambda restriction is for models that reach for it, `sort_by` is for models that don't.

---

## The grade argument

Why does this matter? Because the language's properties are decidable at parse time.

A general Python program can do anything a Turing machine can do. You can't decide whether it halts, whether it's safe, whether it accesses the network, whether it spawns processes — Rice's theorem says you can't decide any non-trivial semantic property of a Turing-complete language in general.

Lackpy isn't Turing-complete. Here's why:

**No unbounded iteration.** `while` is forbidden. `for` iterates over a finite collection — either a tool result (bounded by the tool's output) or a `range()` call (bounded by its argument). Every loop terminates. The program's execution trace is finite by construction.

**No function definitions.** `def` and `lambda` are forbidden. You can't write recursive functions. You can't build a Y combinator out of assignments and for-loops. The program is a straight-line sequence with bounded loops — a finite unfolding.

**No code generation.** `eval`, `exec`, `compile`, and `__import__` are all excluded from the namespace. The program can't generate new programs at runtime. What you see in the AST is what runs.

This is the same structural argument that makes SQL decidable for query planning. SQL has `SELECT`, `JOIN`, `WHERE`, `GROUP BY` — but no general recursion, no unbounded loops, no function definitions. (Recursive CTEs exist but are bounded in practice by optimizer limits.) The query planner can analyze any SQL query and determine its execution plan before running it. Lackpy's AST validator can analyze any lackpy program and determine its grade before running it.

The grade computation is straightforward: walk the AST, collect every `ast.Call` node where the function is an `ast.Name`, look up each name in the resolved kit, take the join (max) of all tool grades. The composite grade is the highest grade of any tool the program calls.

```python
# This program's grade = max(grade(read), grade(find_definitions))
results = find_definitions("validate")
for defn in results:
    content = read(defn["file"])
    if "TODO" in content:
        print(f"TODO found in {defn['file']}")
```

If `read` is Level 1 (pinhole filesystem read) and `find_definitions` is Level 0 (AST query), the program's grade is Level 1. The `for` loop, the `if`, the f-string — none of these add grade. They're structural. The grade flows through the tool calls, and the tool calls are enumerable from the AST.

This is what the [formal companion](../../ma/formal-companion) calls decidable composition: the composite's properties follow from the components' properties by a rule the Harness can apply mechanically. No inference required. No judgment. Just a walk and a join.

---

## Three layers

The validation pipeline has three independent safety layers. Each catches what the others miss.

**Layer 1: AST whitelist.** Parse the program with `ast.parse()`. Walk every node. If any node's type isn't in `ALLOWED_NODES`, reject. This catches structural violations — an `import` statement, a function definition, a `while` loop. It's purely syntactic. Fast. No false negatives for structural checks.

**Layer 2: Namespace restriction.** Every `ast.Call` where the function is an `ast.Name` must resolve to either a tool in the current kit or an allowed builtin (`len`, `sorted`, `range`, `str`, `int`, `print`, etc.). Every `ast.Name` is checked against a forbidden set (`__import__`, `open`, `globals`, `getattr`, etc.). This catches semantic violations — calling a function that isn't in the namespace, accessing a forbidden name. It's the difference between "syntactically valid Python" and "a program that only does what we intended."

**Layer 3: Sandbox.** The program runs with `{"__builtins__": {}}` — an empty builtins dict. The only names available at runtime are the tool callables and the allowed builtins, injected explicitly. Even if layers 1 and 2 miss something, the runtime namespace doesn't contain the primitives needed for escape. In v2, nsjail adds OS-level isolation: no network, restricted filesystem, PID namespace, memory limits.

HuggingFace's smolagents library takes a similar approach for their `local_python_executor` — an AST interpreter that walks allowed operations and raises errors on anything unauthorized {cite}`smolagents`. Lackpy differs in one important way: smolagents *interprets* the AST node by node, while lackpy *compiles and executes* the validated AST as a code object. Interpretation is safer (no compiled code escapes) but slower. Compilation is faster but relies on the AST validation being complete. The sandbox is the backstop that makes compilation safe enough.

The combination matters. The AST whitelist alone doesn't prevent calling arbitrary functions (a `Name` node is syntactically fine). The namespace restriction alone doesn't prevent structural escapes (attribute chains like `"".__class__.__mro__` are semantically opaque to name-level checks — though the string-contains-`__` check addresses this specific vector). The sandbox alone doesn't prevent information leakage through tool call arguments. Together, they form a defense in depth where each layer's blind spots are covered by the others.

---

## The MCP problem

There's a practical obstacle. Lackpy is exposed as an MCP server. The outer agent calls `delegate("find callers of validate_token", kit="debug")`. Inside, the generated program calls `find_definitions(...)`, `read(...)`, etc.

But MCP tools can't call other MCP tools. The protocol doesn't support it — an MCP server handles requests from a client, it doesn't make requests to other servers. If `find_definitions` is a Fledgling MCP tool, the lackpy server can't invoke it during program execution.

The solution: bypass MCP for internal tool calls. Lackpy's toolbox resolves tools to Python callables — not MCP calls. Fledgling's `find_definitions` becomes a Python import: `from fledgling.api import find_definitions`. Blq's `run_tests` becomes another import. Built-in tools like `read` and `glob` are implemented directly in lackpy using `pathlib`.

One MCP call in (from the outer agent), N Python function calls inside (from the generated program), one structured result out (back to the outer agent). The outer agent sees a single tool call. Inside, an entire workflow executed — with full tracing of every step.

This is architecturally important. The generated program runs in lackpy's process, calling Python functions directly. It never touches MCP, never crosses a network boundary, never serializes to JSON between steps. The overhead per internal tool call is a function call, not a protocol round trip. The round-trip tax is eliminated entirely within the composition boundary.

---

## The twist

So we have a restricted Python language, a validation pipeline, and an execution model. The outer agent states its intent — "find callers of validate_token and show which files import it" — and *something* translates that intent into a lackpy program.

The obvious answer: the outer agent writes the program. It's a frontier model. It writes Python all day. Give it the namespace description and it'll produce valid lackpy.

We tried this. It works. It also misses the point.

The program generation task is *too simple* for a frontier model. Not "too simple" as in beneath it — "too simple" as in wasteful. It's intent → tool sequence with data flow. The namespace is small (5-15 functions). The output is short (3-20 lines). The patterns are repetitive — read files, search definitions, filter results, format output. This is pattern matching, not reasoning.

Using Opus or Sonnet to generate a lackpy program is like using a frontier model to format a string. It works, but the model's full decision surface — its capacity for nuance, planning, revision — is wasted on a task that has maybe a dozen valid solutions, all structurally similar.

Worse, frontier models fight the restrictions. They want to define helper functions. They wrap everything in `async def main()`. They add error handling with `try/except`. Their training pushes them toward "good Python" — and good Python uses exactly the constructs we removed. You end up spending tokens talking the model *out of* its best habits.

What if the generator didn't have those habits?

---

## The micro-inferencer

A small parameter model doesn't have habits. It has reflexes.

Qwen 2.5 Coder 3B {cite}`qwen25coder` is a code generation model small enough to run on a laptop CPU. It doesn't plan. It doesn't deliberate. It doesn't reason about architecture. Given a prompt that says "here's a namespace, write a Jupyter cell," it produces the cell. The output is short, syntactically competent, and structurally simple — because the model isn't capable of the complex flourishes that make frontier models fight the restrictions.

```{note}
An earlier version of this post specified 1.5B as the target size. In practice, 1.5B models struggle to respect the restriction instructions — they generate valid Python but not valid *lackpy*, because they can't reliably internalize the AST whitelist constraints from the prompt alone. 3B models can. 7B models do it comfortably. The sandbox remains the backstop — the AST validator catches what the model misses — but the retry rate at 1.5B made it impractical as a default.

We're also exploring a multi-stage approach: generate unrestricted Python, identify violations via the AST validator, then ask the model to revise only the violation points. Three calls, each simpler than one shot at restricted generation. The validation stage is fully specified (level 0). This echoes a finding from the [experimental program](../../drafts/the-experiment-that-proved-us-wrong): model capability determines which tool abstraction is effective. The 1.5B/3B boundary for lackpy parallels the Haiku/Sonnet boundary for structured tools.
```

The prompt uses Jupyter cell framing:

```
You are a Jupyter notebook cell generator. Write a single cell
using ONLY the pre-loaded kernel namespace below.

Output ONLY the cell contents — no markdown, no explanation, no code fences.

Assign tool results to variables and reuse them. Never call the same
function twice when you can reuse a variable.

You orchestrate tools to find and modify existing code.
Use read(path) to get file contents.

Kernel namespace:
  read(path) -> str: Read file contents
  find_definitions(name) -> list[dict]: Find definitions by name
  find_callers(name) -> list[dict]: Find callers of a function
  glob(pattern) -> list[str]: Find files matching pattern

Builtins: len, sorted, range, str, int, print, enumerate, any, all

The cell's last expression is displayed as output.
```

Two things to notice. First, the prompt doesn't list what's forbidden. An early version included "Not available: import, def, class, while, try/except, lambda, open" — we removed it. Telling a small model what it can't do is like telling someone not to think about elephants. The model's job is to use the namespace it's given, not to reason about restrictions. The validator handles enforcement.

Second, the `read(path)` nudge: "You orchestrate tools to find and modify existing code. Use read(path) to get file contents." Without it, the 1.5B model would occasionally hallucinate tools or skip the file-reading step. A small nudge toward the most common operation stabilizes the output.

The Jupyter framing itself is deliberate. The model has seen millions of notebook cells during training. A notebook cell is *already* a restricted program: no imports (those go in earlier cells), no function definitions (those go in library code), just calls to pre-loaded functions and data manipulation. The framing aligns the restriction with a pattern the model already knows.

The 1.5B model doesn't need to understand *why* it can't use `import`. It just needs to generate a cell that uses the provided namespace. That's exactly the kind of task small models handle — constrained generation from a fixed vocabulary.

When the model fails validation, it gets one retry with error feedback. The feedback includes targeted hints — if the model tried `open()`, the hint says "use read() instead"; if it wrote a `lambda` outside a `key=` argument, the hint says "use sort_by() instead." These hints are deterministic (no model in the error-correction loop) and were derived from the most common failure patterns during testing.

---

## What this looks like

Here's the architecture at runtime:

```
Outer agent (Opus/Sonnet, $3-15/M tokens)
    │
    │ "find callers of validate_token"
    │
    ▼
lackpy MCP server
    │
    ├─ Kit resolution: "debug" → {read, glob, find_definitions, find_callers, run_tests}
    │
    ├─ Inference pipeline (priority-ordered):
    │   ├─ Templates   → pattern match against known intents
    │   ├─ Rules       → keyword → program (deterministic)
    │   ├─ Ollama      → Qwen 2.5 Coder 3B (local, $0)
    │   └─ Anthropic   → Haiku fallback (API, ~$0.001)
    │
    ├─ Validation: AST whitelist → namespace check → grade computation
    │
    ├─ Execution: compile(validated_ast) + traced namespace
    │
    └─ Return structured trace to outer agent
```

The outer agent makes one MCP call. Inside, the inference pipeline generates a program. The program is validated. The program runs, calling tools directly as Python functions. Every tool call is traced — tool name, arguments, result, duration, success/failure. The trace goes back to the outer agent as a structured result.

The inference pipeline is itself a ratchet. Templates (Level 1, zero cost) are checked first. Rules (Level 1, zero cost) are checked second. The local model (Level 3, $0) is tried third. The API model (Level 3, ~$0.001) is the fallback. The system prefers the lowest computation level that produces a valid program.

---

## The isolation

One thing deserves emphasis, because it's easy to miss.

The 1.5B model generates text. That's all. It never sees the execution. It doesn't know whether its program ran, whether it succeeded, whether the tool calls returned useful results. It receives a prompt, produces a string, and the string either passes validation or doesn't. If it doesn't, the model gets one retry with the validation error — and then the system moves to the next inference provider.

This is Write/Execute Separation {cite}`cemcp` at micro scale. The inferencer writes. A completely separate system validates and executes. The inferencer can't observe the execution results unless the outer agent explicitly feeds them back in a new request. The model is fire-and-forget.

The inferencer's world coupling is zero. It has no tools. It reads no files. It makes no network calls. It runs in an isolated process with nothing but a text prompt and a text response. Its entire contribution to the system is a string that gets parsed into an AST — and the AST is what the Harness trusts, not the model.

This matters for the trust argument. The question isn't "do we trust the 1.5B model?" The question is "can an untrusted string pass through three validation layers and produce only authorized effects?" The answer is structural, not statistical. It doesn't depend on the model's alignment, its training data, or its capability profile. It depends on the AST whitelist being complete and the namespace being correctly restricted.

---

## The Ma at micro scale

This is where the framework becomes interesting.

Lackpy is a complete star topology:

| Component | In lackpy | In the outer agent |
|---|---|---|
| **Principal** | Outer agent (states intent) | Human (states task) |
| **Inferencer** | 1.5B model (generates program) | Frontier model (reasons about task) |
| **Harness** | AST validator + namespace | Claude Code + MCP protocol |
| **Executor** | Compiled program + traced namespace | Tool implementations |

The same architecture at two scales. But the parameters are radically different.

The 1.5B inferencer has **zero world coupling**. It doesn't call tools. It doesn't read files. It doesn't see execution results. It receives a text prompt and produces text output. Its W is 0 — it's a pure function from prompt to string.

Its **decision surface** is constrained to the AST subset. Even if the model generates something dangerous, the validator rejects it before execution. The reachable decision surface is bounded by the whitelist, not by the model's capabilities. The model can barely reach the edges of the specified band.

The **trust gap** inverts. For a frontier model with bash access, the trust gap is large — the model can reach far beyond what we expect, and the gap is where risk lives. For the 1.5B model generating lackpy, the trust gap is tiny. Not because we trust the model more, but because it *can barely do anything*. The constraints aren't a cage — they're scaffolding. The model needs them to produce useful output at all.

And the **ratchet turns faster**. A smaller trust gap means less need for observation before crystallization. A successful program can promote to a template after fewer confirmations. The steady state — where most calls are served by templates rather than model inference — arrives sooner because there's less uncertainty to resolve.

The framework predicts this: lower Ma systems ratchet faster than higher Ma systems. The micro-agent's ratchet cycle is measured in requests, not sessions. The templates accumulate in hours, not weeks. The tool teaches itself to need less model with every successful call.

That prediction is structural, not empirical. We'll test it in [the next post](03-the-tool-that-teaches-itself-to-disappear).

---

*Next: [The Tool That Teaches Itself to Disappear](03-the-tool-that-teaches-itself-to-disappear) — The ratchet applied to lackpy itself.*

```{seealso}
- [The Round-Trip Tax](01-the-round-trip-tax) — The cost problem this solves
- [Write/Execute Separation](../../patterns/04-write-execute-separation) — The pattern at the structural level
- [The Specified Band](../../ma/08-the-specified-band) — Why decidability matters for composition
- [The Configuration Ratchet](../../ma/the-configuration-ratchet) — The mechanism that makes this self-improving
- [The Quartermaster](../../patterns/01-the-quartermaster) — Kit selection as model-aware tool dispatch
```

## References

```{bibliography}
:filter: key in {"smolagents", "codeact", "cemcp", "qwen25coder"}
```

<!-- Citation keys:
smolagents: HuggingFace. "smolagents: agents that think in code." https://huggingface.co/blog/smolagents
codeact: Wang et al. "Executable Code Actions Elicit Better LLM Agents." ICML 2024. arXiv:2402.01030. https://arxiv.org/abs/2402.01030
cemcp: Felendler et al. "From Tool Orchestration to Code Execution." arXiv:2602.15945, 2026. https://arxiv.org/abs/2602.15945
qwen25coder: Hui et al. "Qwen2.5-Coder Technical Report." arXiv:2409.12186, 2024. https://arxiv.org/abs/2409.12186
-->
