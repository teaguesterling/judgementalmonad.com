# Conversations Are Folds

*The conversation is not a growing computation. It's a sequence of stateless computations over managed state.*

---

## The illusion

From the inside, a conversation feels like a continuous, growing thing. Each turn builds on the last. Context accumulates. The model "remembers" what was said. It feels like a single computation with expanding state — a program that runs for hours, getting richer and more capable with every exchange.

It isn't.

Every inference call is stateless. The model receives a token window — constructed fresh by the Harness — performs a single forward pass through fixed weights, and produces a response. It has no memory of the previous turn. It has no persistent state. The "memory" is tokens in the input that the Harness chose to include. The "continuity" is an artifact of the Harness copying previous outputs into the next input. The conversation is an illusion created by a stateless function applied repeatedly to managed state.

The conversation is a **fold**.

```
Conv_State₀ →[extract]→ view₀ →[infer]→ response₀ →[inject]→ Conv_State₁
Conv_State₁ →[H]→ Conv_State₁' →[extract]→ view₁ →[infer]→ response₁ →[inject]→ Conv_State₂
...
```

Each arrow through the Inferencer is a pure function of its input. The state lives entirely in `Conv_State`, managed by the Harness. Between steps, the Harness may apply endofunctors to the state — adding tools, removing tools, compacting history, restructuring scope. The `[H]` step is where the Harness exercises its full agency: transforming the substrate before the next extraction.

The Harness IS the conversation. The Inferencer is the step function.

---

## What this means for ma

Ma is "the space between what an actor receives and what it produces." That's a property of a single computation. It was always a property of a single computation. The stateless insight doesn't change the definition — it reveals that the definition was already correct.

We were asking "what's the ma of a conversation?" as if the conversation were a computation. The conversation is a fold. Ma applies to the step function (a single inference call), not to the fold. The Inferencer has the same ma every time it's invoked — same weights, same architecture, same path space. What changes between invocations is the *input*, which the Harness constructs from scratch.

The three components hold at every turn:

**World coupling**: for the Inferencer alone, always sealed. It reads its token window and nothing else. World coupling enters through tool composition, controlled by the Harness.

**Decision surface**: the weights. Fixed. Turn 1 and turn 100, identical.

**Interface restriction**: the available tools and output constraints. Harness-controlled, can change per turn.

The Inferencer's own grade is a constant: `(sealed, trained)`. The *compound* grade of a turn varies because the Harness varies the configuration. But that's not the Inferencer's ma changing — that's composition with a changing tool set.

"Ma determines role" gets *stronger*, not weaker. The Inferencer's role is stable across the conversation because its ma is stable. The Harness's role is stable because its ma is stable. Roles aren't negotiated per-turn — they're consequences of fixed properties of the actors. The only thing that changes per-turn is the Harness's configuration, which determines the compound grade of each step in the fold.

---

## Context is input, not decision surface

The earlier claim that "decision surface grows at runtime via in-context learning" was wrong — or at least, badly stated.

Context accumulation is world coupling growth. More data entering through the input boundary. The weights don't change. A temperature-0 LLM with 1,000 tokens of context and 100,000 tokens of context has the same decision surface. It has different *inputs*. An LLM that "does different things with more context" is just a function doing different things with different inputs. GCC does different things with different source files. That's not GCC's decision surface growing.

But there is a real effect, and it's subtler.

A transformer's weights are fixed, but the number of pairwise attention interactions grows quadratically with context length. At 1,000 tokens, there are roughly 500,000 attention pairs per layer per head. At 100,000 tokens, there are roughly 5 billion. The same fixed Q/K/V matrices, but vastly more *applications* of those matrices, with each application's output influencing downstream computations.

This means the number of *distinguishable execution paths* through the fixed weights grows with context length. Not because the weights changed, but because the attention mechanism creates an interaction graph whose size depends on input length. More context → more interactions → more reachable paths → more distinguishable behaviors from the same weights.

The right framing:

```
d_total     = const                    (the weights — fixed)
d_reachable = f(d_total, |context|)    (monotone in context length)
```

The Harness controls context length. So the Harness indirectly controls `d_reachable` — through scope construction, through compaction, through what it chooses to include in the token window. This is a lever the framework hadn't identified: context management controls not just what the actor sees (world coupling) but how many paths through the weights are reachable (effective decision surface).

Compaction reduces both simultaneously. It shrinks the context (reducing `d_reachable`) and discards accumulated world state (reducing `w_accumulated`). Both axes of the grade move down. Both move up as the conversation grows. Context management is the single most leveraged Harness operation because it simultaneously controls world coupling AND effective decision surface.

---

## The composite entity

The fold decomposition was necessary surgery. But the patient is real. From the Principal's perspective, there's an entity that receives messages and produces responses, accumulating context across turns. Call it the Conversational Agent. It's made of stateless parts, but *it* is stateful. The state is `Conv_State`, managed by its Harness component.

Its type signature: `StateT Conv_State IO` — which is the Harness's own type. The Inferencer is the step function inside the Harness's state machine. The composite's interface type IS the Harness's type because the Harness IS the persistent entity. The Inferencer is invoked and discarded each turn.

The composite's ma — the space between receiving a Principal message and producing a response — includes everything mediating that relationship. And its grade evolves over the course of the conversation.

### Accumulated world coupling

At turn 1, the composite has whatever tools are configured. At turn 50, `Conv_State` contains the *results* of dozens of past tool calls — frozen world state from the time of those calls. The composite's response is conditioned on all of it. Past tool results aren't live world coupling (the file may have changed since), but they're information that entered through the world coupling channel and now sits in state.

The composite's effective world coupling is the integral of past world interactions, not just the current tool configuration.

### Fixed decision surface, growing reach

The composite's decision surface is the Inferencer's weights — constant. But it's exercised over a growing state space. The chain of dependencies through `Conv_State` means the composite's response to a message at turn 50 depends on what the Inferencer said at turn 3, which depended on a tool result from the filesystem at that time. The paths through the weights are the same, but the inputs navigating those paths carry accumulated structure.

### The composite IS a co-domain funnel

Vast internal ma (Conv_State + trained weights + tool IO). Bounded interface ma (rendered responses to the Principal). The composite is the fractal architecture from the formal framework (§14) made concrete: the conversation IS a sub-agent. The Principal is the parent. The composite presents an Executor-like interface. Same structure at every level.

---

## The grade as a coupled recurrence

At turn n, the composite has grade `g(n) = (w(n), d(n))`. What determines `g(n+1)`?

**World coupling at n+1** depends on what tools were called at turn n — which the decision surface chose. And what results came back — which the world coupling determined. And what the Harness permits.

**Reachable decision surface at n+1** depends on what context accumulated — determined by tool results (world coupling) and previous inference outputs. More tokens, more attention interactions, more reachable paths.

Both components of `g(n+1)` depend on both components of `g(n)`:

```
g(n+1) = F(g(n), config(n))

w(n+1) = W(w(n), d(n), config(n))
d(n+1) = D(w(n), d(n), config(n))
```

This is a discrete dynamical system on the grade lattice, parameterized by Harness configuration.

The Harness's role is now precisely that of a **controller** for this dynamical system. It observes `g(n)` (to the extent it can — it can characterize `w` but not fully characterize `d`), applies `config(n)` (tool grants, scope construction, compaction), and tries to keep the trajectory within regulatory bounds.

### The trajectory

The composite's grade over a conversation is a trajectory through the grade lattice:

```
γ(C) = (g(0), g(1), ..., g(n))
```

The trajectory is monotonically non-decreasing between meta-operations (tool grants raise `w`, context accumulation raises `d_reachable`). Compaction is a downward step — a phase boundary where the Harness pushes the trajectory to a lower point on BOTH axes simultaneously.

The one-shot join `g_A ∨ g_B` of the participants' grades is an asymptotic ceiling the trajectory approaches:

```
g(t) ≤ g_conv(∞) ≤ g_A ∨ g_B
```

The first turn's grade may be well below the join (thin context, few tools granted). By turn 100, the effective decision surface approaches the model's total, and tool grants may have maxed out world coupling. The trajectory converges toward the ceiling set by the participants.

### What the Harness controls

Every Harness decision is a step in the trajectory:

| Harness action | Effect on w | Effect on d_reachable | Trajectory effect |
|---|---|---|---|
| Grant tool | Increases (tool's world surface) | Indirect (tool results will grow context) | Moves grade up and right |
| Revoke tool | Decreases (tool's world surface removed) | — | Moves grade left |
| Compaction | Decreases (accumulated state compressed) | Decreases (shorter context, fewer interactions) | Moves grade down on both axes |
| Scope restriction | — | Decreases (less context, fewer paths) | Moves grade down on d |
| Tool result injection | Increases (new world state enters) | Increases (context grows) | Moves grade up on both axes |

The Harness's control problem: keep the grade high enough for useful inference, low enough for regulation. Too aggressive with restriction → the Inferencer can't do useful work. Too permissive → the composite becomes uncharacterizable. Compaction is the reset button — it trades information for regulatory headroom.

---

## The one-shot join was always the right composition

The "conversation composition problem" (Point 9 from the [self-critique](self-critique-formalisms.md)) asked: how does ma compose in iterated, bidirectional exchanges? The answer turns out to be: it doesn't need a new composition operator.

Each turn is one-shot composition: `g_turn = g_inferencer ∨ g_tools(config)`. The conversation's overall grade is the supremum of the per-turn grades. The trajectory is a sequence of one-shot compositions under varying configuration. The Harness controls the configuration. Budget bounds the trajectory length.

What seemed like an open problem — "the grade of a conversation is a trajectory through the lattice, not a single point" — is true but not problematic. The trajectory is generated by iterated application of the same composition operation (join) with the same step function (the Inferencer) under varying parameters (the Harness configuration). No new algebra needed. The conversation's "worst-case grade" for regulatory purposes is:

```
g_conv = ∨_t  g_turn(t) = (max_t w(T_t, accumulated_t), max_t d_reachable(|ctx(t)|))
```

The grade at the turn with the most tools granted and the longest context. This is what the Harness needs to regulate for.

---

## What this resolves

From the self-critique, Point 9 asked: "Tool-call composition (one-shot join) is clean. Conversation-as-iterated-composition (multi-turn with feedback, decision surface growing at runtime) is an open problem."

The resolution: there is no special "conversation composition." There's iterated one-shot composition where the Harness threads state via a fold. The feedback loop that seemed to create a new kind of composition is just the Harness choosing to include previous outputs in the next input. That's a Harness decision, not a property of composition.

What IS new — and what the next posts in this series develop — is the recognition that the *dynamics* of the grade trajectory depend critically on the tool set's properties. Specifically: whether the tools allow the agent to specify computations for execution, and how expressive that specification language is. This creates a taxonomy of **computation channels** that determines whether the grade trajectory is bounded or self-amplifying — and forces a careful analysis of where the Harness's regulatory model breaks down.

That analysis also forces an honest reckoning with the star topology — when it holds, when it breaks, and what the operating system teaches us about regulation at high world coupling.

---

## References

- Katsumata, S. (2014). Parametric effect monads and semantics of effect systems. *POPL*.
- Orchard, D., Wadler, P., & Eades, H. (2019). Unifying graded and parameterised monads. *arXiv:1907.10276*.
- Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.
- Conant, R. C., & Ashby, W. R. (1970). Every good regulator of a system must be a model of that system. *International Journal of Systems Science*, 1(2).

---

*Previous: [The Grade Lattice](the-grade-lattice.md)*
*Next: [Computation Channels](computation-channels.md)*
