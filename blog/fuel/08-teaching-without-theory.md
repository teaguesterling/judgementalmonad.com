# Teaching Without Theory

*You don't need to explain the ratchet. You need to build the floor it stands on.*

---

## You don't need to teach lattice theory

Seven posts in, I should address the obvious question: how do I get my team to use this?

The honest answer is that you probably don't explain any of it. Not the lattice, not the grade taxonomy, not the supermodularity proof, not the formal companion. You especially don't explain the formal companion. If you walk into a standup and say "we need to ensure our tool interfaces form a monotonically growing specified band within the grade lattice," you will be asked to leave.

This is fine. The framework describes a mechanism. But a mechanism's artifacts can be used without understanding why they work. You don't need to know metallurgy to use a wrench. You don't need to know queueing theory to respect a rate limit. You don't need to know lattice theory to write a good CLAUDE.md file.

The artifacts encode the conclusions. The failure stream teaches the intuitions. The theory is for the rare cases where you need to understand *why* a constraint exists — and in practice, those cases are rare enough that you can handle them one at a time, when they come up, with a person who's already motivated to understand because they just hit a wall.

The question is not "how do I teach the framework?" The question is "what artifacts does the framework tell me to build, and how do I make them self-explanatory?"

---

## Three layers

Every teaching system — for agents, for analysts, for junior engineers, for entire organizations — has three layers. They operate at different frequencies and carry different kinds of knowledge.

### Layer 1: Constraints (always active, non-negotiable)

Sandbox configuration. Permission rules. Tool restrictions. File access boundaries. Network isolation. Rate limits. Schema validation. Type checking. Linters.

These encode the specified band. They don't explain it.

An agent with three tools — Read, Approve, Reject — never needs to learn when not to use Write. The question doesn't arise. An analyst with a read-only database connection never needs to learn the data modification policy. The schema enforces it. A junior engineer whose CI pipeline rejects PRs without tests never needs to be told to write tests. The constraint makes the lesson unnecessary.

Constraints are the highest-leverage teaching tool because they operate before the learner makes a decision. There's no moment of judgment where the student weighs "should I do this?" The option doesn't exist. The cognitive load of learning the rule is zero, because the rule is the environment.

This is what the series has been building toward. The specified band is not documentation. It's architecture. And architecture teaches by existing.

### Layer 2: Design principles (applied during decisions)

"Put structure at every boundary." "Don't put an LLM in the execution loop." "Log everything." "Change implementation or tests, never both." "Restrict the tool set before upgrading the model."

These are the rules from [Post 0](00-ratchet-review.md), the ones that live in CLAUDE.md files and onboarding docs and code review checklists. They require judgment to apply — you have to recognize when you're at a boundary, when you're putting an LLM in the execution loop, when you're about to change both sides at once.

Principles are applied by the practitioner during their work. They don't need to be internalized before the work starts. They need to be *accessible* when a decision point arrives. A CLAUDE.md file that says "prefer editing existing files over creating new ones" doesn't need to be memorized. It needs to be loaded in context when the agent is about to create a file.

The key property of principles is that they're consulted, not enforced. The learner can override them. The learner *should* override them, sometimes — that's how you discover when a principle doesn't apply and needs refinement. The override, and its outcome, become data for the ratchet.

### Layer 3: Reference (loaded on demand)

The Ma series. The formal companion. This series. Architecture decision records. Design documents that explain *why* the system is shaped the way it is.

Reference material exists for the moment when someone asks "why?" — and specifically, for the moment when the answer matters for a decision they're about to make. Not as background reading. Not as onboarding curriculum. As a resource for a specific question that arose from specific work.

Most practitioners will never load this layer. That's the design working correctly. If everyone needs to read the formal companion to do their job, the constraints and principles are inadequate. Reference is the escape valve, not the foundation.

---

## The teaching ratchet

Here's where the three layers connect to everything this series has been about.

The student — agent or person — works on real tasks with constraints active. They hit a constraint. Maybe they try to access a file outside their sandbox. Maybe they try to run a query that the template library doesn't cover. Maybe they submit a PR that the linter rejects.

Each of these is a failure. Each failure is logged. The failure stream accumulates.

Patterns emerge. Three analysts hit the same template gap in the same week. An agent repeatedly tries to use a tool it doesn't have. A junior engineer's PRs get rejected by the same linter rule every time.

The patterns become changes. The template gap becomes a new template. The missing tool becomes a new slash command. The linter rule gets a better error message, or the onboarding doc gets a new example, or — and this is the important case — the constraint itself gets adjusted because the failure pattern revealed that it was too tight.

The teaching material improves with use. This is the ratchet applied to onboarding itself. Each cohort of students generates failures. Each failure set refines the constraints and principles. The next cohort hits fewer walls. The onboarding gets better without anyone writing a training manual. The training manual is the accumulated artifact of every previous student's failures.

The ratchet only turns one way. The constraints grow more precise. The principles grow more specific. The reference grows more targeted. Onboarding gets cheaper with each cycle.

---

## Onboarding a Claude Code instance

You've already seen this pattern if you use Claude Code. You just haven't called it a ratchet.

A CLAUDE.md file is a ratchet artifact. It encodes the discoveries of every previous Claude instance that worked in this codebase. "Prefer the Edit tool for modifying existing files." "Never use git commands with the -i flag." "Always quote file paths that contain spaces." Each line is a crystallized failure — something a previous instance tried, failed at, and left behind as a constraint for the next instance.

The permission configuration is the specified band. Auto-accept, default, plan mode — these are trust levels, narrowed by experience. You start broad and tighten as you discover what goes wrong. The permission config doesn't explain why certain operations need approval. It just requires the approval. The constraint teaches by constraining.

Slash commands are the three-layer structure in miniature. The command itself is a constraint (it scopes what the agent does). The command's implementation encodes design principles (how to do the thing correctly). The command's documentation is reference (why it works this way, loaded only when someone asks).

And the failure stream that refines the CLAUDE.md over time — the repeated pattern that becomes a new instruction, the permission denial that becomes a new rule, the timeout that becomes a new tool restriction — that's the ratchet turning. Each session's failures become the next session's constraints.

No one taught the Claude instance lattice theory. No one explained the formal framework. The CLAUDE.md file *is* the teaching, and it gets better every time the ratchet turns.

---

## Onboarding an analyst to a data platform

The same pattern works for humans. Consider a data platform — a BI tool, a data warehouse, a shared analytics environment. New analysts join regularly. They need to become productive. The traditional approach is training: documentation, walkthroughs, maybe a certification.

The ratchet approach uses the three layers instead.

**Constraints: access tiers.** The analyst gets a role-scoped database connection. They can see the tables relevant to their team. They can't see PII columns unless their role includes PII access. They can't run queries that exceed a resource limit. They can't modify production data.

These constraints don't need to be taught. They're enforced by the platform. The analyst who tries to access a restricted table gets an error, not a policy document. The constraint is the teaching.

**Design principles: template library.** Validated queries for common operations. "Revenue by region for the last quarter" is a template, not a skill the analyst needs to develop from scratch. "Customer cohort analysis" is a parameterized query, not a blank SQL editor. The templates encode the organization's analytical patterns — the right joins, the right filters, the right aggregation levels.

The analyst applies these templates during their work. They modify them. They combine them. When a template doesn't cover their use case, they write custom SQL — and that's a signal. The gap between what the templates cover and what the analysts need is the failure stream.

**Reference: community gallery.** A searchable library of analyses that other analysts have published. Not training material — working artifacts. The analyst loads this on demand, when they're trying to do something specific and want to see how someone else approached it.

**The ratchet: the support ticket stream.** When an analyst gets stuck — can't find the right table, doesn't understand a column name, hits a resource limit that seems wrong — they file a ticket. The ticket is a failure log. The pattern of tickets tells you where the onboarding is failing. Three tickets about the same confusing column name? Add a column description to the data catalog. Five tickets about the resource limit on a common query? Optimize the query and add it to the template library. Ten tickets from analysts who can't find the revenue table? Rename it.

Each batch of tickets makes the next analyst's onboarding smoother. No one rewrites the training documentation. The platform itself improves. The constraints get more precise. The templates cover more cases. The data catalog gets more complete. The ratchet turns.

---

## The best documentation makes itself unnecessary

There's a design principle embedded in all of this, and it's worth stating directly: the goal of good documentation is to make itself unnecessary.

If the constraints are right, most questions never arise. The analyst who can't access restricted data never needs to learn the access control policy. The agent that has only three tools never needs to learn when not to use the other twelve. The junior engineer whose linter catches formatting issues never needs to read the style guide.

Good constraints eliminate categories of questions. Each eliminated question is a piece of documentation that doesn't need to exist, a training session that doesn't need to happen, a mistake that doesn't need to be made and then corrected.

This is not about dumbing things down or removing autonomy. It's about putting knowledge in the right layer. The access control policy is real and important — but it belongs in the permission system, not in a PDF that new hires are supposed to read. The style guide is real and important — but it belongs in the linter, not in a wiki page. The tool restrictions are real and important — but they belong in the configuration, not in a prompt that says "please don't use these tools."

Every piece of knowledge that can move from documentation to constraint should move. Every piece that can move from reference to principle should move. Every piece that can move from principle to constraint should move. The ratchet pushes knowledge downward through the layers, from "thing you need to understand" to "thing the environment handles for you."

The documentation that remains — the reference layer, the "why" documents, the formal companion — exists for the edge cases. For the person who needs to modify a constraint and wants to understand what it protects. For the architect who's designing a new subsystem and needs to understand the principles it should embody. For the rare moment when understanding the mechanism matters more than using its artifacts.

That documentation is valuable precisely because it's rarely needed. It serves the person who's already deep enough in the work to have a specific question that the constraints and principles don't answer.

---

## Don't teach the space. Shape it.

The ratchet doesn't require understanding. It requires artifacts: constraints that encode boundaries, principles that encode patterns, references that encode reasons. It requires a failure stream that refines those artifacts over time. It requires the willingness to let the artifacts do the teaching.

You don't need your team to read nine posts on lattice theory. You need a CLAUDE.md file that gets better every week. You need permission configs that reflect what actually went wrong last month. You need templates that cover what people actually do, and a feedback loop that tells you when they don't.

The theory is here if you want it. The formal companion is here if you need it. But the ratchet turns whether or not anyone reads them. It turns because the artifacts improve. It turns because the failures get captured. It turns because each cycle's constraints become the next cycle's floor.

Don't teach the space. Shape it. The shaped space teaches itself.

---

*Previously: [The Classification Engine](07-the-classification-engine.md)*
*Next: [The Organizational Star](09-the-organizational-star.md)*
*For the full treatment: [The Ma of Multi-Agent Systems](../ma/00-intro.md)*
