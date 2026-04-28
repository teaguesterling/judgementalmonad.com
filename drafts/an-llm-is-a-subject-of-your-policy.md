# An LLM Is a Subject of Your Policy

*...and so are the files it touches. And the tools it reaches for. And the principal who commissioned it.*

---

## The disconnect

When you want to restrict what a user can do in a system, you write a policy. Roles. Permissions. Who can read what. Who can edit what. Who can approve what. This is a forty-year-old problem. The formalism is Datalog. The production languages are OPA/Rego, Cedar, Oso/Polar. The deployments are at scale — Netflix, Pinterest, half of CNCF.

When you want to restrict what an LLM can do, you... add it to a CLAUDE.md? Wire up a hook? Wrap tools in a sandbox? The answer is never "write a policy" — it's always a *different* answer depending on which restriction you mean.

- "The agent inherits the user's permissions." (principal side)
- "The tool is restricted to these operations." (action side)
- "The file system is mounted read-only." (resource side)

Three separate discussions. Three separate mechanisms. None of them unified.

Meanwhile the operation itself is fully coupled. An LLM agent editing a file is one thing that involves all three simultaneously: the user who commissioned it, the tool that executed it, the file that received the change. When you ask "can this happen?" you mean all three at once. But no single policy language in the agent space can express all three at once, because we never saw them as one question.

---

## The four subjects we need but don't name

Try to express the policy "the Opus agent, in test mode, using Edit, may modify src/auth.py." Notice what has to be named:

1. **Intelligence** — Opus. The LLM making the decision.
2. **Operation** — Edit. The tool performing the action.
3. **Use** — src/auth.py. The specific resource being touched.
4. **Principal** — the user who commissioned the agent. (Or another agent, with inheritance rules that don't match RBAC at all.)

Every existing policy language handles some subset. None handle all four. OPA and Cedar do principal/action/resource beautifully — three of the four. Oso's Polar does principal/resource with action composition. Claude Code's hooks do operations in isolation. nsjail and bwrap do resources in isolation.

These four subjects aren't a novelty claim. They're what every policy conversation is already implicitly about. We just don't notice, because we never have all four in view at once.

---

## Where the principal/action/resource trio runs out

Cedar's principal/action/resource is a real achievement — a formally-verified Datalog-based language with clean three-axis conjunction. For human-authored policies over service APIs, it's the state of the art.

For agent-authored policies over stochastic delegation, it runs out at two places.

**There's no coordination axis.** Where does the harness fit? Claude Code is a harness. Cursor is a harness. MCP servers are harnesses. LangGraph, AutoGPT, and agent-riggs are all harnesses. They mediate between the LLM and the tools — they're coordination, not operation, and they're not the principal. Cedar has no slot for them. Neither does OPA. But the harness is the place where the Opus-plus-Edit conjunction actually gets resolved; writing a policy that can't name it is writing around the problem.

**There's no intelligence axis.** The LLM isn't the principal (the user is) and isn't the operation (the tool is). It's a new kind of subject — the one that *decides which operation to invoke on which resource*. Cedar's principal is deterministic, identity-bound, and stable over time. An LLM is stochastic, context-bound, and different on every call. Different axis, different behavior, different enforcement requirements.

Without coordination and intelligence as their own axes, "the Opus agent, under Claude Code harness, in test mode, using Edit, on /src/auth.py" is five assertions spread across five systems. It can't be a single rule, because no language gives you a syntax for five-axis conjunction.

---

## Why a new schema is forced

Stafford Beer's Viable System Model gives you seven roles for a viable system: environment (S0), operations (S1), coordination (S2), control (S3), audit (S3*), intelligence (S4), identity (S5). Beer wasn't thinking about LLM authorization. He was thinking about whether an organization can survive.

What the [Ma series](../blog/ma/index) has been building toward is this: a bounded-delegation system is a viable system in Beer's sense. It has operations, it needs coordination, it has control ("what mode am I in right now"), it has intelligence ("what should I do next"), it has identity ("who commissioned me and why"), and it needs audit ("why did I do that?"). Miss any of these and the system fails to capture something real agent deployments already have.

The seven axes aren't arbitrary. They're what falls out when you treat agent delegation as a system in Beer's sense. Every one of them corresponds to a role-kind that production systems already have but don't name systematically:

| VSM | Role | Corresponds to |
|---|---|---|
| S5 | Principal | The user in RBAC. Commissioning authority. |
| S0 | World | Filesystem, network, available tools, env vars. |
| S3* | Audit | Logs, traces, observation feeds. Cross-cutting observer. |
| S3 | Control | Mode — debug, test, implement. Current stance. |
| S2 | Coordination | The harness — Claude Code, MCP, the orchestrator. |
| S4 | Intelligence | The LLM itself. The stochastic decider. |
| S1 | Operation | The tool — Edit, Read, Bash, search. |

Seven axes. A policy is a cascade conjoined across them.

---

## What CSS gives you that a new DSL doesn't

If you're going to have seven axes, you need a syntax where conjunction across axes is natural. CSS already does this. `#sidebar article.featured p.highlight` joins four selectors across axes with one combinator that doesn't require you to name each axis explicitly. The reader resolves the meaning from which axes get crossed.

The translation to policy is direct:

```css
principal#Teague
  mode#test
  harness#claude-code
  inferencer#opus
  tool#Edit
  use[of="file#/src/auth.py"]
  { editable: true; }
```

Six axes. One descendant combinator, repeated. Reads naturally as a sentence: "Teague's delegate, in test mode, under Claude Code, running Opus, via Edit, use of auth.py — editable."

Every LLM already reads CSS fluently. It's the most over-represented syntax in training data. A 3B model parses and writes this without fine-tuning; a frontier model reasons about cascade specificity. You aren't teaching the agent a new DSL, because the agent learned CSS by osmosis years ago. [The specialization lives in the language](../blog/tools/lackey/03-the-specialization-lives-in-the-language), not in the model.

This isn't a logic bet. The logic underneath is Datalog — same as OPA, same as Cedar, same as Oso. The bet is on *syntax*. Every prior policy language invented its own DSL (Rego, Cedar, Polar, XACML). Each one cost its users cognitive load on day one. CSS costs nothing, because it's already there.

---

## The capability becomes visible

Capability theory is forty years old. Levy's *Capability-Based Computer Systems* (1984) made the distinction formal: a capability is an unforgeable reference to a resource that carries permission with it. Operating systems use capabilities at runtime (file descriptors). Policy languages historically handle them as derived facts — the policy describes permissions; the runtime derives capabilities from those permissions.

The move: **the capability becomes a first-class syntactic construct.** `use[of="file#/src/auth.py"]` *is* the capability. It names a specific use of a specific resource, carrying its own permissions.

```css
/* world axis — existence only */
file#/src/auth.py { language: python; }

/* action axis — permissions via use */
use[of="file#/src/auth.py"] { editable: false; }             /* default read-only */
mode#implement use[of-like="file#/src/**/*.py"] { editable: true; }  /* mode-scoped */
inferencer#opus tool#Edit use[of="file#/src/auth.py"]        /* specific triple */
  { editable: true; }
```

The file in the world axis just exists. Whether a delegate can edit it depends on which `use` they hold. Same file, different modes, different permissions. This matches OS reality — the process holds an fd, the permissions are on the fd, not the inode — except the OS version is a runtime concept, whereas in this syntax the capability is visible in the policy source.

Audit becomes trivial. "The delegate edited auth.py because rule R₁ granted a `use` of it." Proof tree, from Datalog, directly. The Ma series' [specified band](../blog/ma/08-the-specified-band) requires that every decision be traceable to declared rules. Datalog gives you SLD resolution for free. Proof trees are not an add-on feature; they're the byproduct of evaluation.

### The world file as capability prerequisite

But where do the entities that `use[of=...]` references actually come from? The capability chain has a prerequisite the view can't satisfy alone: the entity has to *exist* before it can be used.

This is the role of the **world file** — a YAML declaration of what concretely exists in a delegate's reality. The world file is the DOM to umwelt's CSS, the environment to its policy:

```yaml
# delegate.world.yml
entities:
  - type: tool
    id: Edit
  - type: mode
    id: implement
    classes: [edit, test]

discover:
  - matcher: filesystem
    root: "src/"

fixed:
  "tool#Bash":
    available: false
  "network":
    deny: "*"
```

The capability chain becomes:

```
world file → entity exists → use[of=entity] → policy resolves → permission
```

Cut the first link — the entity doesn't appear in the world file — and no CSS rule produces the permission. The world file is the unforgeable capability token that the delegate holds. `use[of=...]` is the projection of that token into the policy layer. Fixed constraints in the world file are hard boundaries that policy cannot override — they're physics, not rules.

This maps each VSM axis to a concrete section of the world file:

| VSM | Role | World file section |
|---|---|---|
| S0 | Environment | `discover:` — filesystem, git-tracked sources |
| S1 | Operations | `entities:` with `type: tool` |
| S2 | Coordination | implicit — the harness itself |
| S3 | Control | `entities:` with `type: mode` |
| S3* | Audit | *materialization* — the audit snapshot |
| S4 | Intelligence | `inferencer:` declaration |
| S5 | Identity | `principal:` declaration |

The world file isn't just infrastructure. It's the **instantiation of the viable system** for a specific delegation. Each delegate gets its own VSM, specified declaratively, auditable via materialization. The materialized world — `umwelt materialize --world delegate.world.yml` — is the S3* artifact: a complete inventory of what the delegate could see, with provenance tracking for how each entity entered the world.

Three layers, three formats, three rates of change:
- **Vocabulary** (CSS at-rules in `.umw` files) — what *kinds* of things can exist. Changes rarely. Authored by tool developers.
- **World state** (`.world.yml`) — what things *actually exist*. Changes per-delegation. Authored by operators.
- **Policy** (CSS in `.umw` files) — what *rules apply* to existing things. Changes per-task. Authored by principals or the ratchet.

The web platform got this separation right in 1996 (DTD + DOM + CSS). umwelt follows the same architecture for the same reason: each layer has a different author, a different change rate, and a different reason to exist. Mixing them produces the same pathology as inline styles in HTML — policy entangled with state, neither reusable independently.

---

## The ratchet has been specified ILP the whole time

Inductive Logic Programming is a thirty-year tradition. Muggleton's "Inductive Logic Programming" (1991). FOIL. Progol. Aleph. Modern Metagol and Popper. Given positive and negative examples, induce a logic program that covers the positives and excludes the negatives.

The [configuration ratchet](../blog/ma/the-configuration-ratchet) — ratchet-detect analyzing failed tool calls, kibitzer observing patterns, agent-riggs promoting templates — has been doing specified ILP the whole time. Rule induction from examples. Without a neural oracle in the loop. The "specified" qualifier means: no learned component in the mining pipeline. Just structural pattern matching over observation traces.

Classical pre-neural ILP (Progol, Aleph) is in principle sufficient for this. The ratchet has been reinventing a lineage it didn't know it was in. Naming it puts the work on a forty-year formal footing — and makes the ratchet's output *pasteable* into a view, because both speak the same Datalog.

---

## And the principal may itself be an LLM

So far the principal has been a human. It isn't, always. Agents commission other agents. LangGraph orchestration, the manager pattern where a frontier model delegates to cheap models for specific subtasks, agent-riggs promoting templates that run other agents — the principal at the top is human, but the principal *of the delegate* may itself be another agent with its own policy.

This breaks RBAC's inheritance model. In RBAC, if Alice has role R and delegates to Bob, Bob inherits R (or some prefix of it). Identity-based transitive inheritance. In agent delegation, if Opus commissions Haiku for a subtask, Haiku doesn't inherit Opus's capability vector — it receives a *narrower* vector that Opus chose to grant. Capability-based delegation, not role-based.

This is exactly what capability theory handles and RBAC doesn't. It's also why S5 (principal) has to be its own axis rather than collapsing into S4 (intelligence). The principal *of* a delegate can be an agent; the agent carrying out the delegate is a different subject. Two axes, not one.

The delegate inherits nothing by default. What it holds is what its principal granted it — explicitly, narrowly, auditably. That's the policy, not an emergent property.

---

## The lineage, honestly

OPA/Rego. Cedar. Oso/Polar. Zanzibar. SpiceDB. Permify. Soufflé. Binder. SD3. These are real. They work. They deploy at scale. They have formal semantics. Cedar has machine-checked soundness proofs.

Picking Datalog as the formalism isn't novelty. It's rejoining a forty-year tradition that's still alive. Every production authorization language of the last twenty years converged on the same shape: a restricted logic core (Datalog or near-Datalog), a readable surface syntax that isn't the logic directly, a compiler that lowers to an executable form, and separation between authoring and enforcement.

What's novel about what we've been describing isn't structural. It's six specific moves, each defensible on its own:

1. **CSS as the surface syntax.** A UX bet. The syntax is already saturated in training data.
2. **VSM as the schema.** Seven axes, derived from Beer's systems, not invented from scratch.
3. **`use[of=...]` as capability-in-syntax.** The capability is visible, not runtime-derived.
4. **LLM as one of the subject kinds.** The stochastic subject. And it's joined by the others, not replacing them.
5. **Specified ILP as the authoring loop.** Rule induction from observed behavior. The ratchet.
6. **Proof trees as the audit artifact.** Not new in isolation (Lampson 1999), but newly relevant now that "why did the agent do that?" is a live question.

Each move sits on established formal work. None is reinvention. What's new is their combination — and the subject they're combined in service of.

---

## Where this lands

The blog has been building toward this for a while. The [specified band](../blog/ma/08-the-specified-band). Bounded delegation. The ratchet. The three-layer regulation strategy. CSS as coordination medium. pluckit's [jQuery for source code](../blog/tools/pluckit/01-code-as-queryable-material). lackpy's [restricted dialect](../blog/tools/lackey/03-the-specialization-lives-in-the-language). [Views as sandboxes](views-are-sandboxes). [The sandbox tower](the-sandbox-tower). [Umwelt as Layer 3](umwelt-the-layer-we-found).

All of that has a unifying frame now. The frame is: your policy language has multiple subjects, the LLM is one of them, Beer's VSM names the rest, the syntax is CSS, and the logic underneath is Datalog.

And the logic isn't just a claim anymore. umwelt's built-in SQLite compiler turns views into queryable databases — policy as materialized tables, world state as live views provided by per-tool plugins, resolution as derived SQL. The [Rosetta Stone](https://github.com/teaguesterling/umwelt/blob/main/docs/rosetta-stone.md) shows the same seven policies in CSS, SQL, and Datalog side by side. "Views are Datalog" went from thesis to seven worked examples. Every consumer — kibitzer, nsjail, blq, lackpy — defines its own world-state plugin and reads policy with plain SQL. No CSS knowledge required. No standalone compiler to install. The policy compilation lives where the policy language lives.

Forty years of formalism. Thirty years of CSS. One new subject kind. Enough to build something that hasn't existed yet — a policy language whose first-class subject is an agent, and whose other subjects already have forty years of machinery behind them.

---

```{seealso}
- [Umwelt: The Layer We Found](umwelt-the-layer-we-found) — The architectural companion; where this policy language lives.
- [The Sandbox Tower](the-sandbox-tower) — The altitudes at which grade specifications stack.
- [The Specified Band](../blog/ma/08-the-specified-band) — The theoretical foundation for bounded delegation.
- [The Specialization Lives in the Language](../blog/tools/lackey/03-the-specialization-lives-in-the-language) — Why CSS, and why training-data saturation matters.
- [Closing the Channel](../blog/fuel/05-closing-the-channel) — Why structured tools over bash.
- [The Configuration Ratchet](../blog/ma/the-configuration-ratchet) — The mechanism; this post names its logic-programming form.
```
