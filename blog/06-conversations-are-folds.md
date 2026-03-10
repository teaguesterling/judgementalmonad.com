# Conversations Are Folds

*The conversation is not a growing computation. It's a sequence of stateless computations over managed state.*

---

## The illusion

From the inside, a conversation feels like a continuous, growing thing. Each turn builds on the last. Context accumulates. The model "remembers" what was said. It feels like a single computation with expanding state — a program that runs for hours, getting richer and more capable with every exchange.

It isn't.

Every inference call is stateless. The model receives a token window — constructed fresh by the Harness — performs a single forward pass through fixed weights, and produces a response. It has no memory of the previous turn. It has no persistent state. The "memory" is tokens in the input that the Harness chose to include. The "continuity" is an artifact of the Harness copying previous outputs into the next input.

Post 4 made this precise: the Harness simulates continuations through context reconstruction. Each "continuation" is a fresh call with an augmented input. The observable behavior matches a continuous computation with effects — effect raised, result provided, computation continues — but the mechanism is reconstruction, not resumption.

The conversation is a **fold**.

```
Conv_State₀ →[extract]→ view₀ →[infer]→ response₀ →[inject]→ Conv_State₁
Conv_State₁ →[H]→ Conv_State₁' →[extract]→ view₁ →[infer]→ response₁ →[inject]→ Conv_State₂
...
```

Each arrow through the Inferencer is a pure function of its input. The state lives entirely in `Conv_State`, managed by the Harness. Between steps, the Harness may transform the state — adding tools, removing tools, compacting history, restructuring scope. The `[H]` step is where the Harness exercises its full agency: reshaping the substrate before the next extraction.

Post 3 observed that each agent is a closure — a function bundled with the context it captured. The fold makes this temporal: each step creates a fresh closure over the updated `Conv_State`. The conversation is a sequence of closures, each capturing from the state the previous one left behind.

The Harness IS the conversation. The Inferencer is the step function.

---

## What this means for the grade

Posts 2 through 5 built a static framework: grade, preorder, handler structure, interface/internal distinction. All of it described actors with fixed properties, measured at a single moment. The fold model doesn't replace that framework — it reveals that the static picture was always a description of one step. The conversation is what happens when you iterate.

Ma is the space between what an actor receives and what it produces. That's a property of a single computation. It was always a property of a single computation. The fold model doesn't change the definition — it reveals that the definition was already correct.

The question "what's the ma of a conversation?" was badly posed. The conversation isn't a computation. It's a fold. Ma applies to the step function (a single inference call), not to the fold. The Inferencer has the same ma every time it's invoked — same weights, same architecture, same path space. What changes between invocations is the *input*, which the Harness constructs from scratch.

The three components hold at every turn:

**World coupling**: for the Inferencer alone, always sealed. It reads its token window and nothing else. World coupling enters through tool composition, controlled by the Harness.

**Decision surface**: the weights. Fixed. Turn 1 and turn 100, identical.

**Interface restriction**: the available tools and output constraints. Harness-controlled, can change per turn.

The Inferencer's own grade is a constant: `(sealed, trained)`. The *compound* grade of a turn varies because the Harness varies the configuration — granting or revoking tools, constructing different scopes. But that's not the Inferencer's ma changing. That's composition with a changing tool set.

"Ma determines role" gets *stronger*, not weaker. The Inferencer's role is stable across the conversation because its ma is stable. The Harness's role is stable because its ma is stable. Roles are consequences of fixed properties, not negotiations. The only thing that changes per-turn is the Harness's configuration, which determines the compound grade of each step in the fold.

---

## Context is input, not decision surface

Post 2 defined the decision surface as the log of distinguishable input-dependent execution paths. For a deep network, the number of those paths grows exponentially with depth. A natural worry: doesn't the decision surface grow at runtime, as context accumulates? Doesn't the conversation violate the "fixed grade" claim we just made?

No. But the reason is subtler than "the weights don't change."

A transformer's weights are fixed, but the number of pairwise attention interactions grows quadratically with context length. At 1,000 tokens, there are roughly 500,000 attention pairs per layer per head. At 100,000 tokens, roughly 5 billion. Same Q/K/V matrices, but vastly more *applications* of those matrices, with each application's output influencing downstream computations.

This means the number of distinguishable execution paths through the fixed weights grows with context length. Not because the weights changed, but because the attention mechanism creates an interaction graph whose size depends on input length. More context, more interactions, more reachable paths, more distinguishable behaviors from the same weights.

The right framing distinguishes two quantities:

```
d_total     = const                    (the weights — fixed)
d_reachable = f(d_total, |context|)    (monotone in context length)
```

`d_total` is the decision surface — the full path space of the weights. It's the grade component, and it's constant. `d_reachable` is the portion of that path space that the current input can actually activate. It grows with context length, but it's bounded above by `d_total`.

The distinction matters because the Harness controls context length. Scope construction, compaction, what to include in the token window — these determine `|context|`, which determines `d_reachable`. The Harness controls not just what the actor sees (world coupling) but how many paths through the weights are reachable (effective decision surface).

Compaction reduces both simultaneously. It shrinks the context (reducing `d_reachable`) and discards accumulated world state (reducing effective world coupling). Both axes of the grade move down. Both move up as the conversation grows. Context management is the single most leveraged Harness operation because it simultaneously controls world coupling AND effective decision surface.

---

## The composite entity

The fold decomposition was necessary surgery. But the patient is real.

From the Principal's perspective, there's an entity that receives messages and produces responses, accumulating context across turns. Call it the Conversational Agent. It's made of stateless parts, but *it* is stateful. The state is `Conv_State`, managed by its Harness component.

Its type signature: `StateT Conv_State IO` — which is the Harness's own type. This is backwards from naive expectation. The Inferencer — the entity that seems like the brain — is just a function called inside the state machine. The Harness — the entity that seems like plumbing — is the persistent identity. The composite's type is the Harness's type because the Harness IS the persistent entity; the Inferencer is invoked and discarded each turn.

And `IO` at the bottom of the stack is the same `IO` that post 5 flagged as under-refined — the catchall that collapses "reads a file" and "executes arbitrary code" into one type. The composite entity's formal foundation is the type we're least satisfied with. That's honest, not a flaw — it marks exactly where the framework needs the refinement that a later post provides.

This is post 4's handler framing seen from the outside: the fold step IS the handler processing one turn. The composite entity is the handler viewed over time.

The composite's ma — the space between receiving a Principal message and producing a response — includes everything mediating that relationship. And its grade evolves over the course of the conversation.

### Accumulated world coupling

At turn 1, the composite has whatever tools are configured. By turn 50, `Conv_State` contains the *results* of dozens of past tool calls — frozen world state from the time of those calls. The composite's response is conditioned on all of it. Past tool results aren't live world coupling (the file may have changed since), but they're information that entered through the world coupling channel and now sits in state.

The composite's effective world coupling is the integral of past world interactions, not just the current tool configuration.

### Fixed decision surface, growing reach

The composite's decision surface — `d_total` — is the Inferencer's weights, constant across the conversation. But `d_reachable` grows with each turn as context accumulates. The chain of dependencies through `Conv_State` means the composite's response at turn 50 depends on what the Inferencer said at turn 3, which depended on a tool result from the filesystem at that time. The paths through the weights are the same, but the inputs navigating those paths carry accumulated structure — and longer, more structured inputs activate more of those paths.

### The composite IS a co-domain funnel

Vast internal ma: Conv_State + trained weights + tool IO. Bounded interface ma: rendered responses to the Principal. The composite is a co-domain funnel (post 2) at the conversation level. The entire multi-turn conversation, viewed from outside, compresses its rich internal dynamics into a sequence of bounded outputs.

---

## The grade as a coupled recurrence

At turn n, the composite has effective grade `g(n) = (w(n), d_reachable(n))` — accumulated world coupling and the portion of the decision surface the current context activates. What determines `g(n+1)`?

**World coupling at n+1** depends on what tools were called at turn n — which the decision surface chose. And what results came back — which the world coupling determined. And what the Harness permits.

**Reachable decision surface at n+1** depends on what context accumulated — determined by tool results (world coupling) and previous inference outputs (decision surface). More tokens, more attention interactions, more reachable paths.

Both components of `g(n+1)` depend on both components of `g(n)`:

```
g(n+1) = F(g(n), config(n))

w(n+1)           = W(w(n), d_reachable(n), config(n))
d_reachable(n+1) = D(w(n), d_reachable(n), config(n))
```

This is a discrete dynamical system on the grade lattice, parameterized by Harness configuration.

The Harness's role is now precisely that of a **controller** for this dynamical system. It observes `g(n)` (to the extent it can — it can characterize `w` but not fully characterize `d_reachable`), applies `config(n)` (tool grants, scope construction, compaction), and tries to keep the trajectory within regulatory bounds.

### The trajectory

The composite's grade over a conversation is a trajectory through the grade lattice:

```
γ(C) = (g(0), g(1), ..., g(n))
```

Between meta-operations, the trajectory is monotonically non-decreasing: tool grants raise `w`, context accumulation raises `d_reachable`. Compaction is a downward step — a phase boundary where the Harness pushes the trajectory to a lower point on BOTH axes simultaneously.

The one-shot join `g_A ∨ g_B` from post 2 was always the right composition operation — it measures one step. The fold composes the steps. The conversation's overall grade is the supremum of the per-turn grades:

```
g_conv = ∨_t  g_turn(t)
```

The grade at the turn with the most tools granted and the longest context. This is what the Harness needs to regulate for.

### What the Harness controls

Every Harness decision is a move in the trajectory. Crucially, the two axes are independently controllable — some operations move w without touching d_reachable, and vice versa:

| Harness action | Effect on w | Effect on d_reachable | Axis moved |
|---|---|---|---|
| Sandbox restriction | Decreases (world surface shrinks) | — | w only |
| Scope restriction | — | Decreases (fewer tokens, fewer attention paths) | d_reachable only |
| Grant tool | Increases (new world surface reachable) | — (until results arrive) | w only |
| Revoke tool | Decreases (world surface removed) | — | w only |
| Tool result injection | Increases (world state enters Conv_State) | Increases (context grows) | Both |
| Compaction | Decreases (accumulated state compressed) | Decreases (shorter context, fewer interactions) | Both |

The independence matters. The Harness can tighten the sandbox without losing context — reducing what world the agent can reach while preserving the reasoning built up so far. It can compact the context without changing the tool set — reducing d_reachable while leaving w_config intact. Only tool result injection inherently moves both axes, because it's the act of feeding world data into the context window.

The Harness's control problem: keep the grade high enough for useful inference, low enough for regulation. Too aggressive with restriction and the Inferencer can't do useful work. Too permissive and the composite becomes uncharacterizable. Compaction is the reset button — it trades information for regulatory headroom.

---

## The dynamics that matter

The fold model resolves the "conversation composition problem." It seemed like iterated, bidirectional exchanges needed a new composition operator. They don't. Each turn is one-shot composition: `g_turn = g_inferencer ∨ g_tools(config)`. The conversation is a sequence of one-shot compositions under varying configuration. No new algebra needed.

What IS new — and what the static framework couldn't see — is the coupled recurrence. The grade trajectory is not a fixed property of the system. It evolves, and its evolution is self-referential: the decision surface's choices at turn n determine what world state enters, which determines what context the decision surface encounters at turn n+1. The feedback loop doesn't create a new kind of composition, but it does create a new kind of regulatory challenge.

Specifically: does the trajectory converge, diverge, or cycle? If the Harness only adds tools and never compacts, the trajectory is monotonically non-decreasing — the composite becomes progressively harder to regulate. If the Harness compacts aggressively, it loses information the Inferencer needs. The trajectory's behavior depends critically on what the tools can *do* — not just whether they grant world coupling, but whether the computation they enable can itself specify further computation.

This is where the bare/agentic distinction from post 5 becomes dynamic. A bare Inferencer — no tools, `(sealed, trained)` — has a bounded trajectory: `d_reachable` grows with context but `w` stays sealed. The trajectory converges. An agentic Inferencer has tools that grant world coupling, and the trajectory can self-amplify: tool results widen the context, which activates more paths, which generate more tool calls, which widen the context further.

A tool that reads a file adds world coupling. A tool that executes arbitrary code adds something qualitatively different: the ability for the Inferencer's output to *become* a computation that acts on the world. The Inferencer isn't just proposing effects for the Harness to handle — it's writing programs for an Executor to run, and those programs can do things the permission configuration never explicitly addressed. The grade trajectory isn't just growing; it's potentially self-amplifying.

This is the dimension that `IO` collapsed (post 5): not what enters the computation, and not what exits as output, but what the computation can *do to the world*. The difference between a tool that reads and a tool that executes. Between observation and modification. Between consuming and generating.

That taxonomy — what computations the tools enable, and where the regulatory model survives — is the next question.

---

*Previous: [Predictability as Embeddability](05-predictability-as-embeddability.md)*
*Next: [Computation Channels →](07-computation-channels.md)*
