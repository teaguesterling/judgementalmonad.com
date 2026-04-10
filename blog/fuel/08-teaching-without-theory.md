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

### Hooks: constraints as code

Claude Code hooks are the ratchet's most concrete form — failure patterns crystallized into enforcement. A hook is a shell command that runs before or after a tool call. It can gate, modify, or log the operation. Here's what the ratchet looks like as hooks.

**Failure pattern observed:** the agent keeps trying to push to main directly.

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": "Bash",
      "command": "python3 -c \"import sys, json; d=json.load(sys.stdin); cmd=d.get('input',{}).get('command',''); sys.exit(1) if 'git push' in cmd and 'origin main' in cmd else sys.exit(0)\"",
      "description": "Block direct pushes to main — use a PR"
    }
  ]
}
```

That's a failure pattern → constraint. The agent hit "push rejected" three times. Instead of adding a CLAUDE.md instruction ("please don't push to main"), the constraint is enforced by the environment. The agent can't push to main because the hook prevents it. No instruction to forget. No judgment to apply.

**Failure pattern observed:** the agent creates new files when it should edit existing ones.

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": "Write",
      "command": "python3 -c \"import sys, json, os; d=json.load(sys.stdin); path=d.get('input',{}).get('file_path',''); sys.exit(1) if os.path.exists(path) else sys.exit(0)\"",
      "description": "Warn before overwriting — prefer Edit for existing files"
    }
  ]
}
```

**Failure pattern observed:** bash commands take too long because the agent runs full test suites instead of targeted tests.

This one goes in the CLAUDE.md as a principle rather than a hook — it requires judgment about *which* test to run:

```markdown
## Testing
- Run specific tests during development: `pytest tests/test_specific.py -x`
- Only run the full suite before committing
- Use blq: `mcp__blq_mcp__run(command="test")` instead of raw pytest
```

The distinction matters: constraints (hooks) handle the cases where the right answer is always the same. Principles (CLAUDE.md) handle the cases where judgment is needed but should be guided. Reference (the formal companion) handles the cases where someone needs to understand why.

Each hook is a ratchet artifact — a failure that will never happen again because the environment prevents it. The hook file grows over time. The CLAUDE.md gets more specific. The agent gets better not because it learns, but because the infrastructure encodes what previous instances discovered.

---

## Onboarding an analyst to a data platform

The same pattern works for humans. Consider a data platform — a BI tool, a data warehouse, a shared analytics environment. New analysts join regularly. They need to become productive. The traditional approach is training: documentation, walkthroughs, maybe a certification.

The ratchet approach uses the three layers instead.

**Constraints: access tiers.** The analyst gets a role-scoped database connection. They can see the tables relevant to their team. They can't see cardholder data or financial PII unless their role includes PCI scope. They can't run queries that exceed a resource limit. They can't modify production data.

These constraints don't need to be taught. They're enforced by the platform. The analyst who tries to access a restricted table gets an error, not a policy document. The constraint is the teaching.

**Design principles: template library.** Validated queries for common operations. "Revenue by region for the last quarter" is a template, not a skill the analyst needs to develop from scratch. "Customer cohort analysis" is a parameterized query, not a blank SQL editor. The templates encode the organization's analytical patterns — the right joins, the right filters, the right aggregation levels.

The analyst applies these templates during their work. They modify them. They combine them. When a template doesn't cover their use case, they write custom SQL — and that's a signal. The gap between what the templates cover and what the analysts need is the failure stream.

**Reference: community gallery.** A searchable library of analyses that other analysts have published. Not training material — working artifacts. The analyst loads this on demand, when they're trying to do something specific and want to see how someone else approached it.

**The ratchet: the support ticket stream.** When an analyst gets stuck — can't find the right table, doesn't understand a column name, hits a resource limit that seems wrong — they file a ticket. The ticket is a failure log. The pattern of tickets tells you where the onboarding is failing. Three tickets about the same confusing column name? Add a column description to the data catalog. Five tickets about the resource limit on a common query? Optimize the query and add it to the template library. Ten tickets from analysts who can't find the revenue table? Rename it.

Each batch of tickets makes the next analyst's onboarding smoother. No one rewrites the training documentation. The platform itself improves. The constraints get more precise. The templates cover more cases. The data catalog gets more complete. The ratchet turns.

---

## Documentation should be hierarchical, discoverable, and actionable at every level

This isn't a new idea. Good CLI tools have known this forever:

- **Guessable names** — `jetsam save`, `jetsam ship`, `jetsam sync`. You can infer what they do without reading anything. This is Layer 1: the tool's name is the constraint on your expectation.
- **`--help`** — the flag names and one-line descriptions. Enough to use the tool. This is Layer 2: design principles, consulted when you need them.
- **`--help-all`** — every flag, every option, edge cases. Still scoped to one command.
- **Man pages and tutorials** — how the pieces fit together. When to use `save` vs `ship`. This is Layer 3: reference, loaded when you have a specific question.
- **API docs and developer docs** — how to extend, modify, or understand the internals. For contributors and architects.

Each level stands on its own. You can use `jetsam save -m "fix bug"` without reading the man page. You can read `--help` without reading the API docs. Basic usage requires minimal documentation. Advanced usage requires more — but it never requires reading *everything*.

The same hierarchy applies to agent systems:

- **Tool names and parameter types** are guessable — `search(pattern, path)` doesn't need documentation to use.
- **Tool descriptions** in the MCP schema are the `--help` — enough to choose the right tool.
- **CLAUDE.md instructions** are the tutorial — how the tools fit together, what patterns to follow.
- **The formal companion** is the developer docs — for the person modifying the framework itself.

The ratchet pushes knowledge *down* this hierarchy. A principle in the CLAUDE.md ("don't push to main") becomes a hook (the push is blocked). A template in the analyst's library ("revenue by region") becomes a named segment definition. A pattern in the `--help` text becomes a guessable default. Each descent makes the knowledge cheaper to access and harder to miss.

More documentation is more context consumed — for LLMs, that's tokens spent on instructions instead of work. For humans, that's startup time before they're productive. The goal isn't comprehensive documentation. The goal is the minimum documentation at each level that makes the next level unnecessary for most users.

This is especially sharp for examples. Few-shot prompts have a threshold past which more examples make the model *worse* — the patterns compete for attention and the model over-attends to whichever happens to be nearest the output position. [The Worst Model Became the Best](../tools/lackey/03-the-worst-model-became-the-best) documents an extreme case: a 3B model that went from 2/8 correct to 7/8 correct on a DSL task by reducing the example count from 20 to 6 *retrieved* examples. Same weights. Same queries. Only the prompt changed. The effect is strongest at the small-model tier, but the principle applies everywhere — an example bank you retrieve from is better than an example dump you stuff into context. This is part of what a CLAUDE.md file should *not* do: don't list every pattern the agent might need. List the ones that recur, let the failure stream surface the missing ones, and let the retrieval happen (manually or automatically) at request time.

The documentation that remains at the top — the reference layer, the "why" documents — is valuable precisely because it's rarely needed. It serves the person who's already deep enough to have a specific question that the constraints and tool names don't answer.

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
