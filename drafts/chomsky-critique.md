# Critique: Chomsky Hierarchy as Tool Classification in the Formal Companion

## The core claim and where it breaks

The central machinery is Definition 9.1 (line 698):

```
grade(t) = (effects(t), chomsky(input_lang(t)))
```

The paper uses the **Chomsky hierarchy** to classify tools' input languages and then derives decidability results (Proposition 9.7) about whether the configuration invariant holds. The critical phase transition is placed at CF → RE (context-free to recursively enumerable), which is where the paper says the system goes from "decidable and safe" to "undecidable and breakable."

**There is a fundamental category error that undermines the entire tool classification.**

### 1. Chomsky hierarchy classifies recognition, not computational expressiveness

The Chomsky hierarchy classifies *sets of strings* by the automaton needed to *recognize membership*. It does NOT classify what computations an interpreter for that language can perform. These are independent axes:

- **Lambda calculus**: syntax is CF (`term ::= var | (term term) | λvar.term`). A pushdown automaton can parse it. But a lambda calculus evaluator is **Turing-complete**.
- **Most programming languages**: Python, Haskell, C — their syntaxes are CF (or at most CS for name binding). You parse them with a CFG + some context-sensitive passes. But they are all Turing-complete.
- **Bash**: The *syntactic* grammar of bash is roughly CS (because of parameter expansion, brace expansion, etc.). It is NOT RE. You do not need a Turing machine to *parse* a bash command — you need one to *execute* it.

So `chomsky(input_lang(Bash))` is CS or CF, **not RE**. The set of syntactically valid bash strings is decidable. What's undecidable is the *semantic* question of what a given bash program will do — but that's Rice's theorem applied to the interpreter, not a property of the input language's Chomsky level.

### 2. Proposition 9.7 has a direct counterexample

Consider a tool:

```
LambdaEval(expr: string) → result
```

that parses and evaluates untyped lambda calculus. The input language is **context-free** — a PDA can recognize well-formed lambda terms. By Definition 9.3, this is a **data channel** (`chomsky ≤ CF`). By Proposition 9.7, the configuration invariant should **hold**.

But lambda calculus is Turing-complete. `LambdaEval` can compute anything a Turing machine can. If the tool has any effects (writes results to a file, allocates memory), it can break the configuration invariant exactly as Bash can. The proposition is false for this tool — CF syntax, TC semantics, invariant violated.

### 3. The paper's own examples are inconsistent

The paper classifies `SQL SELECT` as CF (line 733). But:

- **SQL:1999 added recursive CTEs** (`WITH RECURSIVE`), which make SQL SELECT **Turing-complete**. This is standard SQL, not an extension. A `SELECT` with recursive CTEs can simulate a Turing machine.
- Even without CTEs, SQL with window functions and lateral joins can express computations well beyond what a PDA can model.

So SQL SELECT is simultaneously CF (the paper's claim) and Turing-complete (via recursive CTEs). Under the paper's own framework, it should be RE (computation channel), but it's classified as CF (data channel). The classification is wrong.

### 4. The LangSec bridge doesn't span this gap

The paper invokes LangSec (Bratus et al. 2011) at line 718: "every tool that accepts input is implicitly an interpreter, and the input IS a program for that interpreter." This is the LangSec insight that parser complexity determines vulnerability surface.

But the LangSec insight works when **parsing IS the computation** — when the parser itself is the attack surface (e.g., a network protocol parser that's accidentally Turing-complete because parsing requires evaluating expressions). It does NOT work when parsing is trivially CF but a separate execution engine provides the computational power.

For Bash, there's a partial bridge: you can't fully parse Bash without executing parts of it (`eval`, `$(...)`, parameter expansion). Parsing and execution are entangled. So LangSec's "parser complexity = vulnerability" has some purchase.

For lambda calculus (or Python, or SQL with CTEs), the parser is a clean CFG pass. The TC power comes entirely from the *evaluator*, which is a separate phase. LangSec's insight about parser complexity says nothing about evaluator complexity. The bridge from Chomsky level to decidability collapses.

### 5. The sandbox paradox

Proposition 9.9 (line 789) claims sandboxing restores the configuration invariant while keeping `chomsky = RE`. But the paper's own remark (line 800) notes that cgroups connect to **bounded Turing machines** — and a bounded TM is equivalent to a finite automaton (it has finitely many configurations and must halt or loop).

So either:
- The sandbox keeps the tool genuinely RE → the invariant can still break (timing channels, resource exhaustion within bounds, information leakage via computation patterns)
- The sandbox effectively bounds the computation → the tool is no longer RE, it's a bounded automaton → calling it RE is misleading

The paper wants both: "still RE" (to preserve the theoretical framework) and "invariant restored" (to make the sandbox claim work). These are in tension. A truly RE tool with effect restrictions can still mount pure-computation attacks (infinite loops within resource bounds, side-channel leakage via timing).

### 6. What the paper actually needs

The real distinction the paper is reaching for is not Chomsky level but something like:

**"Does the tool interpret its input as executable specification?"**

This is a *semantic* property of the tool's interpreter, not a *syntactic* property of the input grammar. The correct formalization would be something closer to:

```
computational_power(t) ∈ {finite, polynomial, decidable, RE}
```

where `computational_power(t)` measures the class of functions the tool can compute as a function of its input — which is what computability theory already provides.

The Chomsky hierarchy gives you clean decidability results about *languages*. Computability/complexity theory gives you clean results about *computation*. The paper tries to use the former to get results about the latter, and the bridge only works in special cases (when parsing ≈ execution), not in general.

---

## Summary

The phase transition at CF → RE is an artifact of conflating syntactic classification (Chomsky) with computational expressiveness (computability). Lambda calculus is the clean counterexample: CF syntax, Turing-complete semantics, and it breaks Proposition 9.7. The entire tool classification framework in Section 9 inherits this error. The results aren't wrong in spirit — Turing-complete tools really are harder to regulate — but the formalism doesn't deliver what it promises. You need a different axis than Chomsky level to ground the argument.
