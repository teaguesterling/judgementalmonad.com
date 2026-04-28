# The Missing Layer

*Agent security has hooks, guardrails, permission prompts, and sandboxes. It doesn't have a policy. That's the gap — and the authorization community closed it twenty years ago for everything except agents.*

---

## Five mechanisms that aren't a policy

Here's what agent security looks like in practice, right now, across the major frameworks:

**System-prompt instructions.** "Don't modify files outside the src/ directory." "Always ask before running destructive commands." "You are a helpful assistant that follows safety guidelines." These are natural-language rules with natural-language enforcement — which is to say, no enforcement. The agent reads them, usually follows them, sometimes doesn't, and nobody can prove which rules were active during a given session.

**Permission prompts.** "Allow Edit on src/auth.py? [y/n]." The user approves or denies each tool call. This is real enforcement — if you deny, the call doesn't happen. But it's per-action, in-the-moment, unrecorded, and unsystematic. There's no artifact that says "here are all the permissions this session had." There's a human clicking yes or no, accumulating decision fatigue, rubber-stamping by the fiftieth prompt.

**Hooks.** Pre-tool and post-tool scripts that run before or after each tool call. Claude Code hooks can block a tool call, log it, or modify it. This is the closest thing to enforcement in the current stack — it's code, it runs, it can say no. But hooks are imperative, per-tool, per-project, and don't compose. You can't write a hook that says "in review mode, all files are read-only except tests." You write a hook that checks the current mode, checks the file path, and returns allow or deny. The policy is embedded in the hook's control flow, not declared anywhere a human or a machine can audit.

**Sandbox configurations.** nsjail textproto files. Docker security profiles. seccomp-BPF filters. These are real, battle-tested, decades-old enforcement mechanisms at the OS level. They bound what a *process* can physically do — which files it can open, which syscalls it can make, whether it can reach the network. But they don't know about *agents*. They don't know what a "tool" is, what a "mode" is, or who commissioned the delegation. They operate on PIDs and file descriptors, not on principals and capabilities.

**Guardrails.** NeMo Guardrails, Guardrails AI, various prompt-injection defenses. These detect and block bad *outputs* — the wrong kind of content, the wrong kind of tool call, responses that look like jailbreaks. They're reactive: they watch the stream and intervene when something looks wrong. They're also, typically, trained classifiers — which means they have false positives, false negatives, and they're opaque to the person deploying them. You can't read a guardrail configuration and know, with certainty, what it will and won't allow.

Each of these addresses a real symptom. None of them is a policy.

---

## What a policy actually is

The authorization community has a forty-year answer to "how do you declare what's allowed in a system?" The answer has a specific shape, and every production system converges on it:

1. **A declarative language** for writing rules. Not imperative code. Not natural language. A restricted formal language where every rule is readable, parseable, and decidable.

2. **A schema** that names the subjects. Who is acting, what they're acting on, what action they're performing. The subjects have types, attributes, and relationships.

3. **An evaluation engine** that takes a request and a policy and produces a decision — allow, deny, or conditional. The evaluation is deterministic. Given the same policy and the same request, you always get the same answer.

4. **An audit trail** that records which rules produced each decision. The trail is a proof tree: "this request was allowed because rule R₁ matched subject S with action A on resource R, and R₁'s conditions were satisfied by facts F₁, F₂, F₃."

5. **Compilation to enforcement points.** The policy is authored once and enforced at multiple points in the system — the API gateway, the service mesh, the database, the filesystem. Each enforcement point reads the policy (or a compiled form of it) and applies it to its own request stream.

OPA/Rego does this. Cedar does this. Oso/Polar does this. SpiceDB does this. They disagree on syntax, on schema, on evaluation strategy. They agree on the architecture. It's the same architecture every time because the problem has the same shape every time.

The agent stack doesn't have this architecture. Not because it doesn't apply — it applies more urgently here, because one of the subjects is stochastic and the decisions are harder to trace. The gap exists because agent security grew up in a different tradition.

---

## Two traditions, talking past each other

**The ML safety tradition** asks: "How do we prevent the model from producing harmful outputs?" The answers are alignment training, RLHF, constitutional AI, output classifiers, prompt-injection detection. The mental model is: the model is dangerous, the safety system constrains it, and the constraint operates on the model's behavior — its inputs, its weights, its outputs.

**The authorization tradition** asks: "How do we declare what actions are allowed in a system?" The answers are RBAC, ABAC, capability systems, Datalog-based policy languages. The mental model is: the system has subjects, resources, and actions; a policy declares which combinations are permitted; enforcement mechanisms make everything else impossible.

These traditions don't talk to each other. ML safety people don't cite Lampson or Cedar. Authorization people don't cite RLHF or constitutional AI. The agent security space lives in the ML safety tradition — guardrails, prompt defenses, output classifiers — and largely ignores the authorization tradition.

But the agent authorization question isn't "is this output safe?" It's "can this subject, using this tool, in this mode, modify this file?" That's an authorization question. It has the same shape as "can this user, in this role, perform this action, on this resource?" — which is the question Cedar and OPA answer every day at Netflix and AWS scale.

The structural mismatch: ML safety operates on the *model*. Authorization operates on the *system*. An agent is both — a model embedded in a system. You need both traditions. But you need the authorization tradition *first*, because it provides the declarative structure that ML safety mechanisms can be embedded within. A guardrail is more useful when it's one enforcement point in a declared policy than when it's a standalone detector hoping to catch everything.

---

## Why existing policy languages don't fit

If the authorization architecture is right, why not just use OPA or Cedar?

Because the agent case introduces subjects, relationships, and enforcement patterns that existing languages weren't designed for.

**The LLM is a new kind of subject.** Cedar's `principal` is an identity — stable, deterministic, bound to an account. An LLM is stochastic, context-dependent, and different on every call. It's not the principal (the user is). It's not the action (the tool is). It's the thing that *decides which action to invoke on which resource*. That's a new subject kind that doesn't map to principal, action, or resource.

**The harness is a new kind of mediator.** Claude Code, Cursor, MCP servers, LangGraph — these are orchestration layers that mediate between the LLM and the tools. They're not principals, not actions, not resources. They're coordination infrastructure. Cedar has no slot for them. Neither does OPA. But the harness is where the policy actually gets enforced — writing a policy that can't name it is writing around the problem.

**Modes are a new kind of state.** "Review mode," "implement mode," "test mode" — these are stances that change what the agent can do, but they're not roles (they're session-level, not identity-level) and they're not resources (they're state, not things). They need their own axis.

**Enforcement spans multiple altitudes.** A single policy decision — "can the agent edit auth.py?" — might need enforcement at the OS level (nsjail mount flags), the language level (lackpy namespace restrictions), the semantic level (hook that checks file paths), and the conversational level (retrieval that includes or excludes the file). No existing policy language compiles to all four. They compile to one enforcement point (the API gateway, the database, the service mesh) and assume the enforcement is sufficient. In the agent stack, no single enforcement point is sufficient — you need the tower.

**The world isn't given.** In traditional authorization, the resources exist — they're database rows, API endpoints, files on disk. In agent delegation, the world is *constructed* — you decide what the agent can see, what tools are available, what files exist in its reality. The world itself is a security decision. No existing policy language has a concept of "the world the subject operates in" as a first-class artifact.

---

## The gap, precisely

Here is the gap in one sentence: **nobody treats the agent's environment as a declarative, auditable artifact.**

The MCP spec declares tool *interfaces* — name, description, input schema. It doesn't declare tool *environments* — whether the tool can reach the network, write to the filesystem, spawn processes, or outlive the call.

CLAUDE.md declares *guidance* — natural language instructions that the agent usually follows. It doesn't declare *policy* — machine-enforceable rules with deterministic evaluation and audit trails.

Docker declares *container* environments — what's mounted, what's running, what resources are available. It doesn't declare *agent* environments — which tools are available, what mode is active, who commissioned the delegation, what computation level is permitted.

Each system declares part of the picture. Nobody declares the whole picture in one artifact that every enforcement tool can read.

---

## What a fitted policy language needs

Given the landscape and the gap, here's what a policy language designed for agent authorization would need. These aren't hypothetical requirements — they fall out of the constraints above:

**A world declaration layer.** Not just "what rules apply" but "what exists." The world the agent operates in — tools, files, modes, resources, principals — must be a first-class artifact, declared before policy is evaluated. This is the capability model: you declare what the agent *holds*, then policy decides what it can *do with* what it holds. No holding, no doing.

**More than three axes.** Principal, action, resource handles human-service authorization. Agent authorization needs the LLM (intelligence), the harness (coordination), the mode (control), the computation level (effect bound), and audit (observation). The schema needs seven subject kinds, not three.

**Multi-altitude compilation.** One policy, compiled to OS enforcement (nsjail, bwrap), language enforcement (lackpy), semantic enforcement (hooks, tool restrictions), and conversational enforcement (retrieval, prompt construction). The compilation is per-altitude, not per-enforcement-point.

**A syntax the subjects can read.** The agent is one of the policy's subjects, and the agent performs better when it can read its own constraints. This rules out custom DSLs that require fine-tuning (Rego, Cedar, Polar). The syntax needs to be something LLMs already know — which, practically, means borrowing from the most over-represented structured language in training data.

**Materialization for audit.** The resolved world + applied policy must be snapshotable as a concrete artifact. "What could this agent see and do?" needs a deterministic answer, producible before the agent runs, diffable across sessions.

**A ratchet-compatible authoring loop.** Policies shouldn't require manual authoring from scratch. The system should observe what the agent actually does (which tools it calls, which files it touches, which resources it uses), propose a tighter policy consistent with the observations, and present the proposal for human review. The authoring loop is: observe → propose → review → commit. Each turn tightens. Each turn is reversible.

---

## The architecture, then

The policy language that meets these requirements has three layers:

| Layer | What it declares | Format | Web analogy |
|---|---|---|---|
| **Vocabulary** | What *kinds* of things can exist | CSS at-rules | The DTD |
| **World State** | What *actually* exists right now | YAML | The DOM |
| **Policy** | What *rules* apply to existing things | CSS | The stylesheet |

The vocabulary declares entity types, attribute schemas, and property semantics. The world state declares the concrete entities — tools, files, modes, principals — that a specific delegation contains. The policy declares rules over those entities using selectors and cascade.

Three layers. Three formats. Three rates of change. Three different authors. The web platform got this separation right in the 1990s for the same structural reason: each layer has a different *job*, and mixing them produces the same pathology as inline styles — policy entangled with state, neither reusable independently.

The policy syntax is CSS because every LLM already reads CSS fluently. The formalism underneath is Datalog because every production authorization language converges on Datalog. The world file is YAML because YAML can't express conditionals, which means policy logic *can't* leak into the world declaration — the format enforces the separation.

The rest of this series develops each layer, its formal grounding, and its relationship to the forty-year tradition it inherits from. The next post starts with the world — because the world is what makes this approach fundamentally different from existing policy languages.

---

## Where this sits

This series describes the policy layer of a larger regulatory architecture:

- **[The Ma of Multi-Agent Systems](../ma/00-intro)** develops the theory: the grade lattice, the specified band, the four actors, the three-layer regulation strategy that the OS existence proof demonstrates. The policy layer is Layer 3 of that strategy.
- **[Ratchet Fuel](../fuel/index)** develops the practice: how friction becomes signal, how signal crystallizes into infrastructure, how the ratchet tightens over time. The policy ratchet is one application.
- **[The Tools](../tools/index)** are the instruments: pluckit, blq, kibitzer, jetsam. Each consumes the policy layer through its own compiler — reading its slice of the policy with plain SQL.
- **[umwelt](https://github.com/teaguesterling/umwelt)** is the implementation: the CSS-syntax policy language with Datalog semantics, a built-in SQLite compiler, and a plugin system for vocabulary registration.

The theory asks *what should the regulatory architecture look like?* The practice asks *how do you bootstrap it from friction?* This series asks *what should the policy language look like, and why?* — with proper citations, honest lineage, and clear boundaries between what's novel and what's borrowed.

---

## The lineage

This series builds on forty years of formal work. The individual pieces aren't novel — they're the authorization community's existing answers, applied to a new subject kind. Naming the lineage is how we avoid reinventing it badly.

**The Datalog tradition.** Every production authorization language of the last twenty years converges on restricted logic programming: OPA/Rego (Styra/CNCF, deployed at Netflix, Pinterest, Goldman Sachs), Amazon Cedar (Cutler et al. 2024, formally verified in Lean, deployed across AWS), Oso/Polar (application-embedded authorization), Google Zanzibar (Pang et al. 2019, 10M+ checks/sec across Gmail/Drive/YouTube) and its open-source offspring SpiceDB and OpenFGA. Earlier: Binder (DeTreville 2002, signed Datalog certificates), SD3 (Jim 2001, distributed Datalog evaluation). The formal foundation: Abadi, Burrows, Lampson & Plotkin's "A Calculus for Access Control in Distributed Systems" (1993) established the `says` logic that all subsequent work builds on.

**Capability-based security.** Dennis & Van Horn (1966) introduced capabilities: unforgeable tokens that simultaneously designate a resource and authorize access. Levy (1984) surveyed the hardware and software implementations. Miller (2006) established the object-capability model and demolished three common objections. WASI (Bytecode Alliance, 2024–25) is the most significant modern deployment — WebAssembly modules receive explicit capabilities rather than ambient authority. The world file is a capability grant in this tradition: the agent holds what the world file declares, and nothing else.

**Defeasible logic.** García & Simari (2004) formalized defeasible logic programming: rules can be defeated by more specific rules, without classical contradiction. CSS's cascade is exactly this pattern — and Nute demonstrated that propositional defeasible logic has linear complexity, which is what makes cascade practical at both rendering and policy-evaluation scale.

**CSS selectors outside the DOM.** ESQuery (estools, ~58M weekly npm downloads via ESLint) applies CSS selectors to JavaScript ASTs. TSQuery extends it to TypeScript. JSONSelect applied selectors to JSON documents. CSS Houdini's `@property` at-rule uses CSS syntax for schema declarations — type constraints in the stylesheet's own grammar. Content Security Policy uses a rudimentary selector-like syntax for policy directives. The pattern is established: CSS selectors work well when the target data is tree-shaped and has typed nodes.

**Declarative environments.** Docker made containers declarative. Nix made builds reproducible via content-addressed derivations. Terraform's plan step previews changes before application. The object-capability model (Miller) frames environment specification as capability granting — the set of capabilities a process holds *defines* its environment. In agent frameworks, MCP declares tool *interfaces* but not tool *environments*. The world file closes this gap.

**Agent authorization specifically.** The literature is moving: SEAgent (Qi et al. 2026) proposes MAC monitoring for agent-tool interactions. PCAS (2026) uses a Datalog-derived language with a reference monitor — the closest existing work to the thesis that agent security is a policy compilation problem. But notably, neither cites Cedar, Binder, or the Abadi calculus. The agent-safety community and the authorization community are working on the same problem without cross-pollination. This series is an attempt to bridge them.

**What's genuinely novel.** Not the individual pieces — those are borrowed. What's novel: (1) a seven-axis schema derived from Beer's VSM, where no published work frames authorization as a 5+ axis conjunction problem; (2) CSS as the policy syntax, which no authorization language has tried; (3) cross-taxon compound selectors, where the descendant combinator bridges entity types from different taxonomies; (4) the world file as a first-class materializable artifact for agent environments, which no agent framework provides; (5) the ratchet as specified ILP (Muggleton 1991) — policy induction from observed behavior without trained components.

---

### Industry and standards

The gap is not just academic. The **MCP Authorization Spec** (2025-2026) uses OAuth 2.1 with PKCE — pure web-standards lineage, no formal policy. **NIST's AI Agent Standards Initiative** (Feb 2026) emphasizes least privilege and task-scoped access but specifies no formal policy language. **OWASP's Agentic Top 10** (Dec 2025) identifies the "principle of least agency" as a practitioner threat model without a formal framework. The **Microsoft Agent Governance Toolkit** (Apr 2026) is the sole production system bridging agent frameworks to established policy languages — supporting Cedar, OPA Rego, and YAML rules.

Anthropic's own agent framework identifies four components: model, harness, tools, environment. Permission control at the tool level. Claude Code defaults to read-only with human approval for writes. No declarative policy language exposed. The architecture is right; the policy layer is missing.

---

*Next: [The World as Capability](01-world-as-capability) — Why declaring what exists is different from declaring what's allowed, and why that distinction is the foundation of the whole approach.*
