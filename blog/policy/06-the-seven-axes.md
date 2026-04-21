# The Seven Axes

*Cedar has three: principal, action, resource. XACML has four (adding environment). Agent authorization needs seven — and the number isn't arbitrary. It falls out of treating bounded delegation as a viable system in Beer's sense.*

---

## Why three axes aren't enough

Cedar's principal/action/resource is the state of the art for human-service authorization. It handles "can user X do action Y on resource Z?" with formally verified evaluation and machine-checked soundness proofs. For service APIs where a deterministic principal invokes a well-typed action on a known resource, three axes are sufficient.

For agent authorization, three subjects are missing:

**The LLM (intelligence).** The model isn't the principal — the user is. It isn't the action — the tool is. It's the entity that *decides which action to invoke on which resource*. It's stochastic, context-dependent, and different on every call. The same user, same tool, same file, but Opus versus Haiku — that's a policy-relevant distinction that three-axis models can't express.

**The harness (coordination).** Claude Code, Cursor, MCP servers, LangGraph, AutoGPT — these mediate between the LLM and the tools. They're not principals (they don't commission the work), not actions (they don't perform operations), not resources (they're not operated on). They determine what mediation the operation receives. A tool call through Claude Code gets hooks, permissions checks, and user confirmation. The same tool call through a raw API gets nothing. The harness matters.

**The mode (control).** Review, implement, test, explore. Session-level stance, not identity-level role, not a resource. When a delegate is in review mode, certain tools are denied and certain files are read-only — not because the principal changed, but because the *stance* changed. Modes are orthogonal to identity and to resources.

Without these three, "the Opus agent, under Claude Code, in test mode, using Edit, on /src/auth.py" is five assertions spread across five systems. It can't be a single rule because no language gives you a syntax for five-axis conjunction.

---

## The prior art on multi-axis authorization

The history of authorization models is a history of adding axes:

**Lampson (1971)** defined the access matrix: subjects × objects × rights. The original three-axis model. Every subsequent authorization system is a refinement of this matrix, adding structure to one or more of its dimensions.

**Harrison, Ruzzo, and Ullman (1976)** showed the safety problem is undecidable for the general access matrix — you can't determine whether a given configuration is safe without simulating all possible state transitions. This result drives every subsequent restriction: RBAC, ABAC, Datalog — each constrains the matrix to make safety decidable again.

**XACML (2003)** added a fourth category: environment. But XACML's "environment" means timestamps, IP addresses, and situational context. `environment:current-time < 17:00:00` is a condition, not an authorization dimension. The execution environment — *which software mediator processes this request* — is not what XACML means by "environment."

**NGAC (Ferraiolo et al. 2016)** at NIST provides arbitrary "policy classes" that can combine multiple attribute types. NGAC has the machinery for seven or more axes. Nobody has used it beyond four. The standard demonstrates that multi-axis authorization is formally sound; the gap is that no one has populated the axes with agent-specific subjects.

**Context-aware access control (Kayes et al. 2020 survey)** treats "environmental context" as physical environment — temperature, location, network conditions. IoT-flavored. Execution environment as "which software mediator processes this request" does not appear as a recognized context type in any surveyed framework.

The gap: no published work frames authorization as a five-or-more axis conjunction problem. No VSM-inspired security framework exists in the literature.

---

## The S0/S2 deconvolution

A critical refinement that the stub hinted at and that requires careful unpacking.

The naive reading of Beer's environment (S0) maps it to "environment" in the XACML sense. But consider: a command executed via Bash runs in the environment Bash provides — process isolation, shell expansion, file system access. The same command executed via nsjail runs in a different environment — namespace isolation, seccomp filters, read-only mounts. The same file, under different execution environments, has a different security posture.

"Environment" conflates two things:

- **S0 = Resources.** What things can be addressed. Files, directories, network endpoints. The addressable world. What the world file's `entities:` and `discover:` sections populate. This is the "what exists" question.

- **S2 = Execution Environment.** Where operations run. What mediation they receive. Bash, nsjail, Claude Code's harness, a Docker container. This is the "how is it mediated" question.

The distinction matters because the same resource under different S2 has different security properties. `file#/src/auth.py` is one entity regardless of S2. But the *operation on it* — reading, writing, executing — goes through different mediators depending on whether the harness is Claude Code (with hooks and permission checks) or a raw subprocess (with nothing).

### SELinux as precedent

SELinux type enforcement is the strongest prior art for this deconvolution. Every SELinux process runs in a *domain* — a type label. Policy rules are triples: `allow source_domain target_type : permissions`. Domain transitions happen on exec — when a new program runs, the execution environment changes. The domain determines what the process can do, independently of who launched it.

This is exactly the S2 axis. The process identity (who launched it) is one dimension. The domain (what mediation it receives) is another. SELinux composes them: the same user in different domains has different permissions.

AppArmor makes it even more explicit: profiles bind to programs, not to users. Same user plus different program equals different permissions. The execution environment — which program is running — is the policy axis.

But the security literature frames SELinux domains as mandatory access control, not as a general authorization dimension. The conceptual move — naming execution environment as a distinct, queryable, composable axis in authorization policy — does not appear to have been stated explicitly.

### Ambient authority and parameterization

Miller's capability work (2003) identifies ambient authority — authority exercised by virtue of where you are rather than what you hold. The execution environment *determines* the ambient authority profile. Capsicum's capability mode strips ambient authority entirely: after `cap_enter()`, the process has only what it was explicitly granted.

The capability literature frames this as binary: ambient versus explicit. You either have ambient authority or you don't. Nobody asks "which *kind* of ambient authority does this environment provide?" But that's exactly the question agent authorization needs to answer. Claude Code provides one kind. A raw subprocess provides another. nsjail provides a third. The S2 axis parameterizes what the binary model leaves undifferentiated.

---

## The VSM derivation

Beer's Viable System Model gives seven roles for a viable organization. Each maps to an authorization axis — not by analogy but by structural correspondence. Each role names something that agent delegation systems already have but don't make addressable in policy:

| VSM | Role | Authorization axis | Entity types |
|---|---|---|---|
| S5 | Identity | Principal | principal, user, agent |
| S4 | Intelligence | Inferencer | inferencer, model |
| S3 | Control | Mode | mode, stance |
| S3* | Audit | Observation | log, trace, metric |
| S2 | Coordination | Execution Environment | harness, orchestrator, sandbox, container |
| S1 | Operations | Action | tool, kit, effect |
| S0 | Environment | Resources | file, dir, mount, network, resource |

The derivation isn't "Beer said seven, so we have seven." The derivation is: each of these seven roles names something real in agent delegation. Remove any one and there's something you can't express:

- Without S5 (Principal): can't distinguish who commissioned the work.
- Without S4 (Intelligence): can't distinguish which model is deciding.
- Without S3 (Mode): can't distinguish review from implement.
- Without S3* (Audit): can't cross-cut observation feeds across the system.
- Without S2 (Coordination): can't distinguish Claude Code from a raw subprocess.
- Without S1 (Operations): can't distinguish Read from Edit from Bash.
- Without S0 (Resources): can't distinguish `/src/auth.py` from `/etc/passwd`.

The question isn't whether seven is the right number. It's whether removing any axis leaves a real policy inexpressible. The answer, in every case examined, is yes.

---

## How the axes compose via CSS combinators

The descendant combinator crosses axes:

```css
principal#Teague
  mode#implement
  harness#claude-code
  inferencer#opus
  tool#Edit
  use[of="file#/src/auth.py"]
  { editable: true; }
```

Six axes. One combinator, repeated. Reads as a sentence: "Teague's delegate, in implement mode, under Claude Code, running Opus, via Edit, use of auth.py — editable."

Specificity uses an axis-count-first model. This rule names six axes, so it's more specific than any rule naming five or fewer — regardless of the CSS3 specificity weight within each axis. The tuple is:

```
(axis_count, principal_weight, world_weight, state_weight, actor_weight, capability_weight, audit_weight)
```

More axes = more specific = wins. The security intuition: a more narrowly scoped rule should override a broader one. A rule that names the principal, mode, harness, model, tool, *and* file is narrower than one that names just the file. The specificity order matches the security order.

The cascade handles partial matches gracefully. A rule qualifying fewer axes applies more broadly:

```css
/* Applies to all files (1 axis) */
file { editable: false; }

/* Applies to files in implement mode (2 axes) */
mode#implement file[path^="src/"] { editable: true; }

/* Applies to files via Edit in implement mode (3 axes) */
mode#implement tool#Edit file[path^="src/"] { editable: true; }
```

Each rule is valid. Each applies where it matches. The cascade composes them by specificity — the most qualified rule wins where it applies, the less qualified rules cover the rest.

---

## Comparison to Cedar

Cedar's three axes with entity hierarchies handle the common case well. The extension to seven axes is needed specifically when the same subject appears in multiple configurations:

- **S4 matters** when the same principal delegates to different models. Opus gets more authority than Haiku — not because of identity, but because of capability.
- **S2 matters** when the same model operates under different harnesses. Claude Code versus raw API. The mediation layer changes what the model can reach.
- **S3 matters** when the same harness runs in different modes. Review mode versus implement mode. The stance changes what's permitted.
- **S3* matters** when audit requirements differ by any of the above. Different observation feeds for different contexts.

Cedar could encode these as entity attributes and use conditions. `when { context.model == "opus" && context.harness == "claude-code" && context.mode == "implement" }` — but conditions aren't axes. They don't participate in specificity. They don't compose via cascade. They don't have their own vocabulary declarations. They're ad-hoc, not structural.

The seven-axis model makes these dimensions first-class: named, queryable, vocabulary-registered, cascade-composable. The cost is complexity — seven axes is more than three. The benefit is expressiveness — policy rules can address combinations that three-axis models can only approximate with conditions.

---

## The world file populates the axes

Each section of the world file instantiates a specific axis:

```yaml
# delegate.world.yml
principal: Teague           # S5 — identity
inferencer: opus            # S4 — intelligence
modes: [implement]          # S3 — control

entities:                   # S1 (tools) + S0 (resources)
  - type: tool
    id: Read
  - type: tool
    id: Edit

discover:                   # S0 — resources
  - matcher: filesystem
    root: "src/"
    include: ["**/*.py"]

harness: claude-code        # S2 — coordination (implicit)
```

The world file is where the abstract axes become concrete. "The delegate has seven axes" is a schema claim. "This delegate has principal=Teague, inferencer=opus, mode=implement, tools={Read, Edit}, resources={src/**/*.py}, harness=claude-code" is a specific instantiation. The policy (CSS) operates within the instantiated world. The materialized world (S3*) records it for audit.

---

## Key citations

- Lampson (1971), "Protection"
- Harrison, Ruzzo & Ullman (1976), "Protection in Operating Systems"
- XACML 3.0 (OASIS, 2013)
- Ferraiolo et al. (2016), NGAC (NIST)
- Beer, *Brain of the Firm* (1972), *Heart of Enterprise* (1979)
- Cutler et al. (2024), "Cedar" (OOPSLA)
- Anderson (1972), "Computer Security Technology Planning Study" (reference monitor)
- Miller, Yee & Shapiro (2003), "Capability Myths Demolished"
- Watson et al. (2010), "Capsicum" (USENIX Security)
- Kayes et al. (2020), Context-aware access control survey
- SELinux type enforcement
- AppArmor profiles

---

*Next: [Materialization and Audit](07-materialization-and-audit) — The world snapshot as security artifact. How materialization, proof trees, and the ratchet close the loop between policy and practice.*
