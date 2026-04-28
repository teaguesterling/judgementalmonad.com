# The World as Capability

*The agent's world isn't given — it's constructed. The world file declares what exists in the delegate's reality: tools, files, modes, resources, principals. What's not in the world file doesn't exist. That's not a policy decision — it's ontology. And it's the foundation the rest of the policy layer builds on.*

---

## The distinction that matters

When you restrict what an agent can do, you have two choices. You can say "this is not allowed." Or you can say "this does not exist."

These are different in kind, not degree. "Not allowed" is a policy statement — a rule that can be overridden by a more specific rule, relaxed by a different policy layer, or circumvented by confused-deputy attacks where a trusted component acts on behalf of an untrusted one. "Does not exist" is an ontological statement — there is no entity for a rule to address, no reference for a confused deputy to follow, no capability to delegate.

The capability-security literature has been making this distinction for sixty years. Dennis and Van Horn's 1966 paper "Programming Semantics for Multiprogrammed Computations" introduced the C-list: a process holds a list of capabilities — unforgeable references to objects it can access. What's not on the list is unreachable. Not forbidden. Unreachable.

Miller (2006) sharpened this into the object-capability (ocap) model: "an object's authority is exactly the transitive closure of objects reachable from it." The capability graph *is* the environment. You don't enumerate what's dangerous and block it. You construct exactly the environment the agent needs and grant nothing else. Miller calls this *constructive security* — build the right thing rather than forbid the wrong things.

The world file is constructive security applied to agent delegation. It declares the reality — what tools exist, what files are visible, what modes are available, what network endpoints are reachable. The entity graph it defines is the delegate's entire universe. Policy (CSS) operates *within* that universe, governing what the delegate may do with what exists. But policy cannot conjure entities into existence. The world file is the prerequisite.

---

## What a world file looks like

```yaml
# delegate.world.yml
entities:
  - type: tool
    id: Read
  - type: tool
    id: Edit
  - type: mode
    id: implement

discover:
  - matcher: filesystem
    root: "src/"
    include: ["**/*.py"]

fixed:
  "tool#Bash":
    available: false
  "network":
    deny: "*"
```

Three sections, three different mechanisms:

**`entities:`** declares what explicitly exists. These are hand-authored, specific, auditable. The delegate has two tools (Read and Edit) and one mode (implement). No Bash. No Grep. No review mode. Not because those are denied — because they aren't in the world.

**`discover:`** names what to scan. The filesystem matcher walks `src/` and creates file entities for every `.py` file it finds. Discovery is how the world file connects to the real environment without requiring every entity to be hand-declared.

**`fixed:`** sets constraints that policy cannot override. Bash doesn't just not exist in the entity list — it's pinned as unavailable. Network access is denied unconditionally. These are physics, not rules. The screen is 1920px wide regardless of what the stylesheet says. Fixed constraints apply after cascade resolution as a final clamp.

---

## The Docker analogy, precisely

This isn't a metaphor. It's structural correspondence:

| Container concept | World file concept |
|---|---|
| Base image | `include:` of a shared base world |
| `COPY` / `ADD` | `discover:` — recipes that populate entities |
| `docker run` args | `entities:` — explicit declarations |
| Bind mounts | `projections:` — external data without full enumeration |
| Read-only mounts | `fixed:` — immutable constraints |
| `docker inspect` | `umwelt materialize` — snapshot of the resolved world |
| Multi-stage builds | Multiple `include:` layers |

Both systems solve the same problem: declaring an isolated environment with specific contents and constraints, in a composable way that separates the environment definition from what runs inside it. Docker made this mainstream for processes. The world file does it for agents.

The precedent chain is deeper than Docker. Nix derivations (Dolstra 2006) made environment construction purely functional — the derivation *determines* the artifact, content-addressed and reproducible. Terraform's plan step made it previewable — `terraform plan` shows you what will exist before you create it. The world file inherits from all of these: it's a declarative recipe that can be materialized into a concrete snapshot, diffed between versions, and audited before execution.

---

## The capability chain

Permission in umwelt requires three things in sequence:

```
world file → entity exists → policy resolves → permission
```

Cut the first link — the entity doesn't appear in the world file — and no CSS rule produces the permission. No selector can match an entity that doesn't exist. No cascade can resolve a property on an unaddressable target. The world file is the unforgeable capability token that the delegate holds.

The `use[of=...]` primitive makes this explicit. `use[of="file#/src/auth.py"]` names a specific use of a specific resource, carrying its own permissions:

```css
/* The file exists in the world (world axis) */
file#/src/auth.py { language: python; }

/* The delegate's use of it (action axis) */
use[of="file#/src/auth.py"] { editable: false; }              /* default: read-only */
mode#implement use[of-like="file#/src/**/*.py"] { editable: true; } /* mode-scoped */
```

The file in the world axis just exists — it's an entity with attributes. Whether a delegate can edit it depends on which `use` they hold. Same file, different modes, different permissions. This matches OS reality: a process holds a file descriptor, the permissions are on the descriptor, not the inode.

---

## Modern capability implementations

The world file isn't theoretical. Every principle it applies has shipping implementations that prove the model works:

**Capsicum** (Watson et al. 2010). FreeBSD's capability mode permanently strips ambient authority from a process. After `cap_enter()`, the process operates only through file descriptors it already holds — it cannot open new paths, create sockets, or reach anything not in its pre-granted set. The world file does the same thing declaratively: instead of imperative capability manipulation, you declare the entity set and let materialization construct the C-list.

**WASI** (Bytecode Alliance, 2024–25). WebAssembly modules start with zero ambient authority. The host passes handle types through imports — file handles, socket handles, clock handles. A module cannot traverse outside the handles it was granted. World files follow the same principle: the delegate's authority is exactly what the world file provides.

**seL4** (Klein et al. 2009). The formally verified microkernel guarantees, with machine-checked proof, that no authority leaks through the capability system. If a thread doesn't hold a capability, it provably cannot access the resource. seL4 demonstrates that the "doesn't exist" guarantee can be absolute, not probabilistic.

**Deno**. `--allow-read=/tmp`, `--allow-net=api.example.com`. Permissions are non-expandable at runtime. A Deno process cannot grant itself new capabilities. The runtime enforces what the startup flags declared.

Each of these implements the same insight: authority should follow from what you hold, not from who you are. The world file is the holding.

---

## Delegation narrows, never amplifies

In pure capability systems, each delegation step can only reduce authority (Miller 2006, Stiegler 2004). You can wrap a capability to attenuate — a read-write file descriptor can be wrapped to produce a read-only one — but you cannot forge new authority from nothing.

The `include:` mechanism in world files has this property. An included world file can restrict or specialize but cannot grant capabilities the parent didn't hold:

```yaml
# base.world.yml — the shared foundation
entities:
  - type: tool
    id: Read
  - type: tool
    id: Edit
  - type: tool
    id: Bash
discover:
  - matcher: filesystem
    root: "."
```

```yaml
# restricted.world.yml — a delegation that narrows
include:
  - base.world.yml

fixed:
  "tool#Bash":
    available: false

discover:
  - matcher: filesystem
    root: "src/"        # narrower than parent's "."
    include: ["**/*.py"]  # only Python files
```

The restricted world starts from the base and removes. Bash is fixed-unavailable. The filesystem scope shrinks from "everything" to "Python files under src/." The delegate who receives this world has strictly less authority than the delegate who received the base. The narrowing is structural — enforced by the format, not by a policy rule that could be overridden.

This is the property CaMeL (Debenedetti et al. 2025) proves formally for capability-safe languages: in their "capability safety theorem," the reachability graph of object references is the only mechanism for authority propagation. Authority cannot be manufactured. It can only flow from what was granted. The world file makes the same structural guarantee declaratively.

---

## Three purposes, one artifact

The world file serves three purposes simultaneously, and collapsing them into one artifact is deliberate:

**Discovery.** The `discover:` section names what to scan. The filesystem matcher walks directories and creates file entities. Future matchers might scan git history, query a package registry, or enumerate network services. Discovery connects the declared world to the real environment.

**Definition.** The `entities:` section declares what explicitly exists. Hand-authored, version-controlled, reviewable in a PR. The auditor can read the entity list and know exactly what the delegate was given.

**Audit.** Materialization — `umwelt materialize` — executes the recipe and produces a snapshot: every entity in the world, with provenance tracking for how it entered (explicit, discovered, projected, included). The materialized world is the answer to "what could this agent see?" Diffable. Replayable. Version-controllable. Two materializations from different sessions produce a diff that shows exactly what changed in the delegate's reality.

Three detail levels serve different audiences:

| Level | Contents | Use case |
|---|---|---|
| Summary | Entity counts, projection boundaries | Quick audit, CI checks |
| Outline | Types + IDs + classes, directory trees | Session recovery, diff |
| Full | Every entity, all attributes | SQL compilation, deep audit |

A full materialization *is* the S3* (audit) artifact from Beer's Viable System Model — the cross-cutting observer that sits outside the system it observes. Post 7 develops the audit story in full.

---

## YAML because no conditionals

The world file is deliberately not CSS. YAML is a data format, not a rule language. You can't write `if mode == "implement" then add tool X` in YAML. For configuration files this is a limitation. For the three-layer architecture, it's the enforcement mechanism.

Policy logic *cannot leak into the world declaration* because the format can't express it. Conditionals belong in CSS (policy), not in YAML (world state). This is format-level enforcement, not convention — stronger than a linting rule, which can be disabled. [Post 3](03-the-pair) develops the full argument for why the YAML/CSS pairing works and what each format's specific properties contribute to the safety envelope.

The enforcement is real but not absolute. People add templating layers on top of YAML — Helm, Ansible, Kustomize. The world file spec's own `vars:` and `include:` create composition points. The format prevents inline conditionals; it doesn't prevent a preprocessing step from generating conditional world files. The [cross-format linter](03-the-pair#the-linter-catching-what-the-formats-cant) catches that gap.

---

## The "doesn't exist" guarantee

The world file's safety contribution is concentrated in one property: entities that aren't in the world file can't be addressed by policy. This is stronger than it sounds. Consider the difference:

**Without a world file** (policy-only): `tool#Bash { allow: false; }` denies Bash. But what if a new rule says `principal#Admin tool#Bash { allow: true; }`? The more-specific rule wins. The denial was a policy preference, overridable by design.

**With a world file**: Bash isn't in the entity set. `tool#Bash { allow: false; }` matches nothing — there's no entity to deny. `principal#Admin tool#Bash { allow: true; }` also matches nothing. The principal can't grant what the world doesn't contain. The absence is structural, not preferential.

Fixed constraints go further: `fixed: { "tool#Bash": { available: false } }` means that even if Bash *is* in the entity set (perhaps via an included base world), the constraint pins it as unavailable after cascade resolution. Policy says `tool#Bash { allow: true; }` — the cascade resolves to `true` — and then the fixed constraint clamps it back to `false`. Physics wins.

This is constructive security in practice. You don't say "the agent may not use Bash." You construct a world that doesn't contain Bash. The agent never encounters the question.

---

## Key citations

- Dennis & Van Horn (1966), "Programming Semantics for Multiprogrammed Computations"
- Lampson (1971), "Protection" (access matrix model, capability/ACL duality)
- Miller (2006), "Robust Composition" (object-capability model, POLA, constructive security)
- Miller, Yee & Shapiro (2003), "Capability Myths Demolished"
- Watson et al. (2010), "Capsicum: Practical Capabilities for UNIX" (USENIX Security)
- Debenedetti et al. (2025), "CaMeL: Defeating Prompt Injections by Design" (arXiv:2503.18813)
- Klein et al. (2009), "seL4: Formal Verification of an OS Kernel" (SOSP)
- Dolstra (2006), "The Purely Functional Software Deployment Model" (Nix)
- WASI capability model (Bytecode Alliance, 2024–25)
- Morris (1973), "Protection in Programming Languages"
- Stiegler (2004), "The E Language in a Walnut" (attenuation, no-authority-amplification)

## Connection to the spec

The full technical design is in [`docs/vision/world-state.md`](https://github.com/teaguesterling/umwelt/blob/main/docs/vision/world-state.md) in the umwelt repo.

---

*Next: [CSS as Policy Syntax](02-css-as-policy-syntax) — Why CSS, and not Rego, Cedar, or Polar. The training-data-saturation argument for policy syntax.*
