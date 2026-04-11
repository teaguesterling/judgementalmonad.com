# Integration Layer Plan

*Tying the Rigged suite together into a working system that maintains itself.*

**Status**: Draft. 2026-04-10. **Reframed** after the umwelt vision docs crystallized the missing-layer concern into a concrete package with its own architecture — see the "Reframing: umwelt is the layer" section immediately after Intent.

---

## Intent

The Rigged suite — jetsam, blq, fledgling, pluckit (in design), kibitzer, agent-riggs, lackpy — has accumulated as a set of individually-capable tools. Each one is written up in its own series, each one has its own documentation, each one does its own job well. What's missing is the layer that makes them work together without a human manually triggering each step.

This plan has two goals:

1. **Mechanistic**: the concrete integration — shared data substrate, event flows, health monitoring, automated triggers — that lets the tools exchange signals and respond to each other's outputs without human intervention at every step.
2. **Architectural**: the systems-level frame that says what each tool is *for* in the overall Viable System Model, where the gaps are, and what belongs where. Currently the framing is implicit. Making it explicit is a prerequisite for designing integration that doesn't end up rebuilding the gaps.

This plan is not an implementation. It's the document that precedes implementation. It names the components, assigns them to Beer VSM functions, identifies what each needs from the others, calls out what's currently manual, and sequences the build order.

Once this plan is in place and validated, a second document will describe the build itself, and a third (after the build stabilizes) will be the blog writeup for the broader audience.

---

## Reframing: umwelt is the layer

*This section was added after the rest of the plan was written. The original version described the missing integration layer as a "unified context substrate" built around a shared DuckDB store, with Phase 1 being "build the substrate." Since then, the umwelt vision docs have crystallized the missing layer into a concrete package with its own architecture, and this plan's framing needs to be updated accordingly.*

The plan's original framing identified three gaps:

1. System 3 (the controller) distributed across the human operator, CLAUDE.md, and per-tool configs — no centralized decision logic
2. System 3* (audit data) scattered across blq's DuckDB, kibitzer's logs, agent-riggs' store, jetsam's git state with no join key
3. Health monitoring absent — MCP servers fall down and nobody notices

Those three gaps are still real. What changed is that the **integration layer has two axes**, not one — and the plan originally conflated them.

- **Unified state (audit substrate).** What every tool has observed, in a shared store so System 3 can correlate across them. This is the DuckDB-substrate story the original plan described. Still correct.
- **Unified directive (policy vocabulary).** What every tool should be enforcing right now, written once in a form every enforcement tool can compile. This is the axis the original plan was missing, and it's what the [umwelt vision docs](https://github.com/teaguesterling/umwelt) now specify.

**umwelt is the directive axis of the integration layer.** It's a CSS-shaped declarative policy format with a vocabulary-agnostic core (parser, selectors, cascade, compilers) plus a plugin API that lets each tool register its own entity taxa. The sandbox consumer registers `world` (filesystem, network, resources), `capability` (tools, kits, computation levels), `state` (jobs, hooks, budgets), corresponding one-to-one with load-bearing concepts in the Ma framework. Every tool in the Rigged suite that cares about bounding actor behavior — nsjail, bwrap, lackpy validator, kibitzer hooks, claude-plugins permission hooks — becomes a compiler target for umwelt. Every tool that cares about auditing actor behavior — blq, ratchet-detect, agent-riggs — reads umwelt views and observations in the same vocabulary.

The two-axis frame:

| Axis | Mechanism | Gap in original plan |
|---|---|---|
| **Unified state (audit)** | Shared DuckDB substrate | Identified; still needed |
| **Unified directive (policy)** | umwelt views + compilers | Not explicitly named |

**What this means for the phased implementation.** The original Phase 1 was "build the substrate + health watchdog." The reframed Phase 1 is **build umwelt** — because the substrate's job is to store audit data the ratchet utility reads, and the ratchet utility produces umwelt views, so umwelt has to exist before the substrate's shape is decidable. The substrate's schema is downstream of umwelt's entity model. Building the substrate first would force ad-hoc schema decisions that would then need to be unwound when umwelt arrives.

The corrected phase order:

- **Phase 0 — Prove the plumbing**: the `claude_code` inference provider in lackpy. Unchanged.
- **Phase 1 — Build umwelt**: core parser, AST, selector engine, cascade resolver, plugin registry, first-party sandbox consumer, nsjail compiler, minimal CLI. This is the ~2 weeks of focused work the umwelt vision docs spec. See `~/Projects/umwelt/docs/vision/` for the complete spec.
- **Phase 2 — The shared substrate**: DuckDB store with schemas informed by umwelt's entity model. This becomes the unified audit store that the original plan identified as gap #2. Now that we know what views look like, we know what the substrate needs to record.
- **Phase 3 — Controller + health watchdog**: System 3 logic that reads the substrate, produces umwelt views via the ratchet utility, and detects MCP-server failures. Previously Phase 1; now deferred because it depends on umwelt being the controller's output format.
- **Phase 4 — Learning feedback loop**: the umwelt ratchet utility reading from the substrate and proposing view revisions. This closes the loop.
- **Phase 5 — Cross-project consolidation**: the view bank across projects, git-history distillation, and the organizational features from the original Phase 5.

**What the original plan still gets right.** The per-tool sections (jetsam, blq, fledgling, pluckit, lackpy, kibitzer, agent-riggs) and what each needs from the others remain accurate. The Beer VSM mapping remains accurate. The "what's currently manual" inventory remains accurate. The gap analysis remains accurate. What changes is that the mechanism for addressing the gaps now has a concrete shape that didn't exist when the plan was written — umwelt — and the phase order has to move umwelt forward to Phase 1 because everything else depends on it.

**The rest of this document** is the original plan, preserved as it was written. Read it with the reframing in mind: every mention of "unified context substrate" is now "umwelt + substrate as two distinct things"; every mention of "the integration layer" should be parsed as "umwelt as the directive axis plus a separate audit substrate"; Phase 1 as originally written ("substrate + health watchdog") is retimed to happen after umwelt ships. The rest — the Beer VSM framing, the per-tool analysis, the architectural principles, the gap inventory — is unchanged because umwelt doesn't replace any of that. It's the missing component the plan identified and was reaching for.

For the umwelt-side story of *why* the missing layer looks the way it does, see:
- [`~/Projects/umwelt/docs/vision/policy-layer.md`](https://github.com/teaguesterling/umwelt) — the Ma-grounded framing (umwelt is Layer 3 of the three-layer regulation strategy from Ma post 8)
- [`drafts/umwelt-the-layer-we-found.md`](../../../drafts/umwelt-the-layer-we-found) — the narrative companion to the vision docs, capturing the nine architectural decisions that shaped the package
- [`drafts/the-sandbox-tower.md`](../../../drafts/the-sandbox-tower) — the theoretical frame, updated after the vision docs were written

---

## The theoretical frame

Beer's Viable System Model identifies five functions that any viable organization needs. The Ma framework maps them to agent architecture ([Building With Ma post 9](../../../blog/ma/09-building-with-ma.md), the [Coordination Is Not Control](../../../blog/ma/coordination-is-not-control.md) essay):

| System | Function | In agent architecture |
|---|---|---|
| **System 1** | Operations | The tools that do the work |
| **System 2** | Coordination | The Harness — routes messages, enforces permissions, maintains coherent operation across parallel work |
| **System 3** | Control | Watches the trajectory, allocates resources, tightens or loosens configuration in response to the failure stream |
| **System 3*** | Audit | The sub-function of System 3 that watches System 1 directly, independent of System 2's routing |
| **System 4** | Intelligence | Environmental scanning, adaptation, proposing new approaches |
| **System 5** | Identity/policy | What the system is for, what trade-offs it makes, whose values it serves |

Current agent architectures have System 1, 2, 4, 5 but only a partial System 3. The Harness (Claude Code) implements System 2 — it routes messages, enforces permission gates, manages tool dispatch. The frontier model implements System 4 — it proposes actions, scans the environment, adapts to inputs. The human implements System 5 — they decide what the system is for and what trade-offs to make. System 3, the controller that watches the failure stream and intervenes when the trajectory goes wrong, is currently performed *manually by the human* or not at all.

The Rigged suite is an attempt to fill System 3 and the audit sub-function 3*. Each tool serves a specific slot.

### Tool-to-VSM mapping (current state)

| Tool | VSM slot(s) | What it actually does |
|---|---|---|
| **jetsam** | System 1 (git operations) | Git workflow acceleration; mutating ops return plans for confirmation. The System 1 executor for git. |
| **blq** | System 1 (build/test) + System 3* (build audit) | Captures build/test events into DuckDB. Queryable after the fact. The System 1 executor for build; the System 3* auditor for build events. |
| **fledgling** | System 1 (code/git/docs/conversation reads) + System 3* (conversation audit) | SQL views over code (via AST), git history, docs, and conversation logs. The System 1 executor for structured reads; the System 3* auditor for conversation history. |
| **pluckit** | System 1 (code queries — in design) | CSS-selector DSL for code. Planned as a System 1 tool that lackpy generates calls to. Not yet implemented. |
| **lackpy** | System 1 (restricted composition) + crystallization layer for System 3 | Natural language → restricted Python → validated execution. Templates crystallize from successful programs, which is a System 3 function (the system learns to not need deliberation for recurring patterns). |
| **kibitzer** | System 3 (in-session control) + System 3* (in-session audit) | Claude Code hooks that watch tool use, intercept bash with structured alternatives, enforce path protection. The closest thing to actual System 3 we have — but it's per-session and can't see across sessions. |
| **agent-riggs** | System 3* (cross-session audit) + partial System 3 (trust-informed recommendations) | Reads kibitzer's hooks and other sources into a DuckDB store. Maintains EWMA trust windows. Surfaces ratchet candidates. Recommends tightening/loosening. Currently the recommendations go to a human, not to an automated control loop. |

### The gaps

Three gaps are visible in this mapping:

**Gap 1: System 3 is distributed and incomplete.** Kibitzer does in-session control but can't see prior sessions. Agent-riggs sees cross-session patterns but can't make immediate interventions (it recommends to a human). Together they'd form a reasonable System 3, but currently the bridge between them — riggs feeding kibitzer's mode transitions, kibitzer emitting events riggs ingests — is manual or nonexistent.

**Gap 2: System 3* data is scattered.** Blq has its own DuckDB store. Fledgling reads Claude Code conversation logs (which kibitzer writes to). Agent-riggs has its own DuckDB store. There's no unified audit substrate. When a build failure happens that was caused by a bad edit that was generated by a model that was working against a stale plan — the causal chain crosses four tools' data boundaries, and nothing currently reassembles it.

**Gap 3: Health monitoring is absent.** The MCP servers fall down (hang, crash, return wrong responses). There's no watchdog. When they fail, the human notices because things stop working, restarts them manually, and loses whatever state they were holding. This is System 3 work being done by System 5. Worse: when an MCP server silently misbehaves (returns stale data, times out intermittently), the failure can propagate for a while before anyone notices.

The integration plan is the work of closing these three gaps.

---

## Architectural principles

Before the per-tool and per-phase details, four principles that should hold across all of it.

**P1: Shared substrate over point-to-point.** Tools communicate by reading and writing to a common store, not by calling each other directly. This is event sourcing applied to the agent ecosystem. The shared store (DuckDB, with tool-owned schemas and shared views) is the truth. Each tool writes its events and reads what it needs from views across other tools' events. Point-to-point coupling makes the integration brittle; shared substrate makes it resilient and inspectable.

Concretely: kibitzer writes hook events. Blq writes build events. Jetsam writes git events. Lackpy writes trace events. Agent-riggs doesn't call any of these — it queries the shared store and produces analysis events. Everything can be reconstructed from the event log.

**P2: Pull, not push, for analysis.** Agent-riggs, the watchdog, and other consumers poll or query the store rather than being pushed events. This decouples producers from consumers and lets each consumer run on its own cadence. It also means a consumer can fall behind or be restarted without losing events — they're in the log.

Exception: *critical* events that require immediate response (an MCP server hanging, a permission violation, a sandbox escape attempt) can use a notification channel in addition to being logged. But the log is still the source of truth.

**P3: System 3 acts on System 3* data.** The controller (System 3 — the thing that decides to tighten or loosen configuration, restart a failing server, promote a template) does so based on observations from the auditors (System 3* — kibitzer's hooks, blq's event log, riggs's trust windows). System 3 does not directly observe System 1. This keeps the control loop clean and debuggable: the data it acts on is the same data a human can inspect.

**P4: Manual overrides always available.** Any automation can be disabled. Any recommendation can be overridden. Any promoted template can be demoted. The system is designed to let the human stay in control when they choose to, but stay out of the loop when they don't. The human sees what's happening through a dashboard or a feed, not by operating the machinery.

---

## Per-tool implementation considerations

For each tool: what it currently does, what VSM function it serves, what it currently consumes and produces, what integration hooks it needs, and what's known to be fragile.

### jetsam

**VSM function**: System 1 — git operations.

**Currently does**: MCP server exposing git workflow tools (status, save, sync, log, diff, pr_*, issue_*). Mutating operations return plans that must be confirmed with `confirm()`. The `git` tool handles anything not covered by workflow tools.

**Consumes**: git state, the user's intent (via tool calls).

**Produces**: git events (commits, pushes, PR operations). These are inspectable via `git log` but aren't currently written to a shared event stream.

**Integration hooks needed**:
- Event emission to the shared store: every mutating operation should produce an event record (timestamp, operation, target, result, confirmed-by).
- Read access to the plan queue: jetsam's plans-that-need-confirmation should be visible in the shared store so other tools (or a dashboard) can see what's pending.
- Health status: a way to check that the jetsam MCP server is actually responsive. A `ping` tool or a periodic heartbeat into the shared store.

**Fragilities**:
- Plans can be lost if the MCP server restarts between `save()` returning a plan and `confirm()` being called. Session state isn't persisted.
- Some git operations have side effects that don't roundtrip through jetsam — a user running `git rebase` in a shell changes state jetsam doesn't see.

### blq

**VSM function**: System 1 (build/test operations) + System 3* (build audit).

**Currently does**: Captures build/test output into a DuckDB store. Provides MCP tools to query errors, events, history, run commands, inspect failures. No shell pipes — filtering happens via `output(tail=20)` etc. Shared store is queryable from both the CLI (`blq run build`) and from MCP.

**Consumes**: build command output, registered commands.

**Produces**: structured build events in its DuckDB store. This is already the right shape for P1 — blq's store is a candidate for the shared substrate, or at least a model for it.

**Integration hooks needed**:
- Event export to the cross-tool shared store: blq's internal events should be visible to agent-riggs and the System 3 controller, either by pointing agent-riggs at blq's DuckDB directly or by replicating relevant events to the shared store.
- Schema documentation: what does a blq build event look like? What are the common queries? Making this explicit lets other tools depend on the schema.
- Health status: same ping/heartbeat story as jetsam.
- Integration with kibitzer: when a build fails, kibitzer should be able to see it via the shared store and factor it into trust scoring.

**Fragilities**:
- The blq store is per-project. Cross-project analysis (a pattern that appears in multiple codebases) requires union queries or replication. Not a problem now but will be soon.
- Run IDs are stable but event IDs may not be. Need to verify foreign keys work across sessions.

### fledgling (source-sextant)

**VSM function**: System 1 (structured reads over code, git, docs, conversations) + System 3* (conversation audit).

**Currently does**: Exposes MCP tools for AST queries (FindDefinitions, CodeStructure), git history (GitShow, GitDiffSummary), docs (MDSection), conversation logs (ChatSearch, ChatSessions, ChatDetail, ChatToolUsage), and raw DuckDB queries. Fledgling reads Claude Code conversation logs (JSONL files under `~/.claude/`) and provides structured views.

**Consumes**: source code, git history, markdown docs, Claude Code conversation logs.

**Produces**: query results on demand. Doesn't currently produce an event stream — it's read-only over existing data sources.

**Integration hooks needed**:
- Expose the conversation log views as the canonical conversation audit substrate. Kibitzer, agent-riggs, and any other tool that wants to query conversation history should go through fledgling's views rather than parsing JSONL directly.
- Index maintenance: fledgling needs to know when new conversation logs arrive so its views stay fresh. Currently this is probably implicit (queries read files on each call). A tailing ingester would be faster and enable event-driven downstream consumers.
- Shared DuckDB attach: fledgling's DuckDB database could be the shared substrate itself, with other tools attaching their schemas to it. This is the minimum-friction integration path.

**Fragilities**:
- Conversation log format is controlled by Claude Code, not us. Format changes break fledgling.
- Large conversation histories may be slow to query without proper indexing.
- The AST queries depend on sitting_duck's language extractors, which have their own issues (documented in the sitting_duck repo).

### pluckit

**VSM function**: System 1 (code queries via CSS-selector DSL). Not yet implemented — currently a spec.

**Currently does**: Documented in the pluckit series (blog/tools/pluckit/). The API is specified. The intent is for lackpy to generate `ast_select()` calls from natural language and for pluckit to execute them over sitting_duck's AST data.

**Integration hooks needed**:
- When implemented: consume `ast_select` calls, return structured results, emit trace events to the shared store so that agent-riggs can see which selectors are being used and identify patterns.
- Grammar versioning: the selector grammar will evolve. Need a way to tag events with the grammar version so retrospective analysis stays consistent.

**Fragilities**:
- Not yet implemented; nothing to be fragile about yet. But the spec should be frozen before implementation starts so that synthetic training data (from the spec itself) has a stable target.

### lackpy

**VSM function**: System 1 (restricted composition) + crystallization for System 3.

**Currently does**: Takes natural language via `delegate()`. Generates a restricted Python program using a local 3B model (Qwen 2.5 Coder). Validates against an AST whitelist. Executes with traced namespaces. Returns structured results. Has a dispatch hierarchy: templates > rules > local model > API fallback.

**Consumes**: natural language intent, tool namespace (kit), examples (from a retrieval layer — per [the worst model became the best](../../../blog/tools/lackey/04-the-worst-model-became-the-best.md)).

**Produces**: execution traces — (intent, program, kit, success, tool calls, results). These go into lackpy's own store.

**Integration hooks needed**:
- Export execution traces to the shared store so agent-riggs can identify ratchet candidates (recurring intent patterns that should become templates).
- Consume promoted templates from agent-riggs: when riggs surfaces a pattern that meets promotion criteria, lackpy should accept the template registration as an event rather than requiring manual `create()` calls.
- Health status: the local Ollama dependency is an extra failure point. Lackpy should report whether it can reach the local model and degrade gracefully to the API fallback if it can't.
- Example bank updates: when new examples should be added (from successful traces that didn't quite match existing templates), the retrieval layer needs to be updated. This is currently manual.

**Fragilities**:
- The Ollama connection can time out or return malformed responses. Retries help but don't eliminate the failure mode.
- The example bank is currently a YAML file edited by hand. Needs to be writable by the integration layer so successful runs can add to it.
- Template promotion is currently manual (via `create()`). The criteria in post 5 describe a plan, not an implementation.

### kibitzer

**VSM function**: System 3 (in-session control) + System 3* (in-session audit).

**Currently does**: Hooks into Claude Code's PreToolUse and PostToolUse events. Enforces path protection per mode. Intercepts bash commands that have structured alternatives and redirects them. Coaches the agent toward better tool usage. Exposes `ChangeToolMode` and `GetFeedback` as MCP tools so the agent can introspect and request changes.

**Consumes**: tool call events from Claude Code hooks, configured mode definitions, path protection rules.

**Produces**: hook events (logged somewhere — currently to its own files), mode change events, coaching feedback to the agent.

**Integration hooks needed**:
- Write hook events to the shared store so agent-riggs can see them cross-session.
- Read trust window data from agent-riggs so that kibitzer's mode transitions can be trust-informed without kibitzer having to reimplement cross-session memory.
- Expose current mode and current trust state via MCP so the agent and the human dashboard can see what state the session is in.
- Accept mode transition recommendations from agent-riggs via the shared store and apply them (with optional human confirmation).

**Fragilities**:
- The hook system depends on Claude Code not changing its hook interface. Has changed before.
- Path protection can be bypassed if the agent runs a new shell session that doesn't inherit the protections.
- The coaching messages can be ignored by the model; they're advisory, not enforced.

### agent-riggs

**VSM function**: System 3* (cross-session audit) + partial System 3 (trust-informed recommendations).

**Currently does**: Reads data into a DuckDB store. Maintains three EWMA windows (immediate, session, baseline). Scores turns. Surfaces ratchet candidates. Recommends mode transitions. The recommendations currently go to a human who decides whether to act on them.

**Consumes**: kibitzer's hook events (currently via direct file reads?), blq's build events, lackpy's traces, git events (probably via jetsam?), conversation logs (via fledgling or directly).

**Produces**: trust scores, ratchet candidates, mode transition recommendations. Written to its own DuckDB store.

**Integration hooks needed**:
- Become the primary consumer of the shared store (once P1 is in place). Stop reading individual tools' stores directly.
- Expose its outputs (ratchet candidates, trust windows, recommendations) as queryable views in the shared store so kibitzer and the dashboard can read them.
- Emit notification events when thresholds are crossed (trust window drops below 0.3, ratchet candidate passes promotion threshold, failure pattern appears). Critical events can use the notification channel (P2 exception).
- Accept "applied" markers: when kibitzer applies a recommendation or a human acts on a ratchet candidate, that fact should be logged back to riggs so it can learn whether its recommendations were good.

**Fragilities**:
- Cross-project analysis not yet supported (same as blq).
- The EWMA thresholds are currently hand-tuned. May need calibration per project or per model.
- If riggs is down, nothing is watching the trajectory across sessions. Needs a health story.

---

## The integration architecture

Given the per-tool considerations, here's what the integrated system looks like.

### The shared substrate

**One DuckDB database per user** (or per workspace, depending on multi-tenancy needs) that acts as the shared event store. Tools attach to it and write to their own schemas; cross-tool views join across schemas.

```
~/.rigged/store.duckdb
├── kibitzer.*        (hook events, mode transitions, feedback)
├── blq.*             (build events, test results, errors)
├── jetsam.*          (git operations, plans, confirmations)
├── lackpy.*          (execution traces, template promotions)
├── fledgling.*       (conversation log index, AST cache)
├── riggs.*           (trust windows, ratchet candidates, recommendations)
├── health.*          (heartbeats, MCP server status, error counts)
└── views.*           (cross-tool views: unified events, trajectories, trust timelines)
```

Each tool owns its schema — reads and writes freely. The `views` schema is shared; any tool can define a view that joins across schemas. Agent-riggs does most of the view work because its job is cross-tool analysis.

Why DuckDB: fledgling already uses it, blq already uses it, agent-riggs already uses it. The ecosystem has settled on it. Fast, SQL-native, embeddable, single-file. The switching cost to something else would be high and the benefit unclear.

### Event model

Every event is a row with at least:
- `event_id` — UUID or ULID
- `emitted_at` — timestamp with timezone
- `tool` — which tool emitted it
- `schema_version` — so format changes don't break consumers
- `session_id` — the Claude Code session, if applicable
- `project_id` — the workspace, for cross-project analysis
- `type` — what kind of event (tool call, plan, confirmation, failure, heartbeat)
- `payload` — JSON blob with tool-specific structure

This is append-only. Events are never modified. Updates happen by emitting new events that supersede old ones; queries look at the latest.

### The System 3 controller

The missing piece. A long-running process that:
1. Watches for trust window changes (from riggs) and applies mode transitions (via kibitzer) when thresholds cross.
2. Watches for ratchet candidates (from riggs) and either auto-promotes them (if they pass confidence thresholds and the promotion is reversible) or queues them for human review.
3. Watches for health events (from the watchdog) and takes action: restart a hung MCP server, alert the human about repeated failures, disable a tool that keeps crashing.
4. Logs its own decisions back to the shared store so they can be audited, reverted, and fed back into riggs's trust analysis.

This is the new component. It's small in code but critical in role. It lives somewhere as a daemon — probably launched as part of `rigged init` alongside the existing tools.

The controller's decisions are *specified* — not an LLM in the loop. It reads the trust windows and applies rules: "if t1 < 0.3 for 3 turns, recommend tightening mode." It doesn't reason about what to do; it pattern-matches on observations from 3*.

### The health watchdog

A smaller, orthogonal daemon that pings each MCP server periodically, records heartbeats, and takes action when servers fail to respond:
- Log the failure to the `health.*` schema.
- Attempt a restart (with backoff).
- If restarts keep failing, mark the server as down and notify the user.

The controller reads health events and can degrade the system's capabilities in response: "lackpy is down, route delegate calls to API fallback only" or "blq is down, disable build-status checks from the trust scoring until it's back."

### The dashboard (later)

Not needed for the first build, but should be planned: a small web UI or TUI that shows the current state of the system — session trust windows, pending ratchet candidates, MCP server health, recent failures, controller actions. The human uses this to stay informed without operating the machinery.

---

## What's currently manual

The inventory of things the human currently does that should migrate to automated control. Roughly ordered from most valuable to automate first.

| Current manual work | Automated by | Phase |
|---|---|---|
| Restarting hung MCP servers | Health watchdog | 1 |
| Noticing that a tool is failing repeatedly | Health watchdog + controller alerting | 1 |
| Promoting ratchet candidates (templates, tool configs) | Riggs analysis + controller auto-promote (with bounds) | 3 |
| Applying kibitzer mode transitions | Controller reading trust windows → kibitzer | 3 |
| Running agent-riggs audits periodically | Riggs daemon mode (already exists?) | 2 |
| Updating lackpy example bank from successful traces | Controller ingestion of successful traces → retrieval update | 4 |
| Deciding which tool configuration to use per task | Quartermaster pattern (per-task tool selection) | 5 |
| Reconciling build failures with conversation events | Shared store + cross-tool views | 2 |
| Triggering template crystallization after observing patterns | Controller auto-promote | 3 |
| Reviewing whether a strategy instruction helped | Riggs trust-delta analysis | 4 |

Each row is a ratchet candidate for the integration layer. The plan converts each one from "the human does this" to "the system does this, the human reviews or overrides when needed."

---

## Phased implementation

Five phases, sequenced by dependency. Each phase produces a working system that's better than the one before it. Phase N doesn't depend on phase N+1.

### Phase 1: Foundation — substrate and health

**Goal**: Tools write to a common store. Nothing falls over silently.

**Deliverables**:
- `rigged init` creates `~/.rigged/store.duckdb` with the schema skeleton.
- Each tool gains the ability to connect to the shared store and write events to its own schema.
- Kibitzer's hook events are the first event stream; they flow into `kibitzer.hook_events`.
- Blq's build events replicate into `blq.build_events` in the shared store (keeping blq's own store as the authoritative cache).
- Jetsam emits git events into `jetsam.git_events`.
- Lackpy emits trace events into `lackpy.traces`.
- Health watchdog daemon: pings each registered MCP server on a configurable interval, logs heartbeats, restarts on failure with exponential backoff, alerts the user when restart attempts fail.
- A `rigged status` CLI command that shows the health table and recent events at a glance.

**Verification**:
- After a Claude Code session, `rigged status` shows events from all tools that were active.
- Killing an MCP server and watching the watchdog restart it.
- Querying the shared store across tool schemas (e.g., "show me every build failure that happened within 60 seconds of a `file_edit` on a Python file" — should be a single SQL query).

**Blockers to resolve**:
- Do tools write directly or via a separate event-ingestion daemon? (First pass: direct writes with a library helper.)
- What's the connection model — each tool holds its own connection, or everything goes through a single writer? (DuckDB supports concurrent reads and a single writer; a small dispatcher daemon is the cleanest path but adds complexity. First pass: each tool opens its own connection, accepts the concurrency limits, measures whether they matter.)
- Schema versioning: how do we handle tool upgrades that change event shape? (First pass: `schema_version` field per row, queries filter on it. Long term: migration scripts.)

### Phase 2: Audit unification — riggs sees everything

**Goal**: Agent-riggs reads from the shared store exclusively. The System 3* function is unified across tools.

**Deliverables**:
- Riggs stops reading individual tools' data sources and reads from the shared store.
- Cross-tool views in `views.*` that join across schemas: unified trajectory view (all events per session), trust-relevant events, ratchet candidate queries.
- Riggs emits its outputs (trust windows, candidates, recommendations) as events back to the shared store in `riggs.*` schemas.
- Riggs runs as a daemon (not manually invoked) with a configurable polling interval.
- A `rigged audit` CLI command that prints the current trust state and any pending recommendations.

**Verification**:
- A session that produces a build failure, a bash → structured tool switch, and a git commit — all three events should appear in the unified trajectory view. Riggs's trust score for that session should reflect all three.
- Comparing riggs's outputs before and after the migration: should be functionally equivalent on the same input data, because the substrate changed but the analysis didn't.

**Blockers to resolve**:
- If riggs's old data lives in its own DuckDB store, how do we migrate existing history? (Option A: fresh start. Option B: replay events from old store into new store. First pass: fresh start, document the cutover.)
- Cross-project analysis: do we point riggs at a single store or multiple? (First pass: single store per workspace. Multi-project analysis is phase 5+.)

### Phase 3: Control — System 3 becomes a thing

**Goal**: The controller daemon exists and automates the safest subset of what the human currently does manually.

**Deliverables**:
- `rigged-controller` daemon that polls the shared store on a configurable interval.
- Trust-driven mode transitions: when t1 drops below a threshold, controller recommends tightening via an event; kibitzer picks up the recommendation and (optionally with human confirmation) applies it.
- Ratchet candidate auto-promotion for *reversible* changes: templates that pass thresholds auto-promote to lackpy; promotions are logged and can be demoted via CLI. Non-reversible changes (permission grants, tool set changes) still require human review via a candidate queue.
- Controller actions are logged to `riggs.controller_actions` so they can be audited, reverted, and analyzed.
- A `rigged controller` CLI for seeing what the controller has done recently, what it's considering, and what's pending.

**Verification**:
- A spiraling session (repeated failures): controller should recommend tightening without being asked. Kibitzer should apply it (with or without confirmation). Trust window should recover.
- A recurring template pattern: controller should auto-promote after N successful applications. The promoted template should take effect on the next relevant `delegate()` call.
- A controller recommendation that the human overrides: should log the override, feed back into riggs's analysis, adjust future recommendation confidence.

**Blockers to resolve**:
- Auto-promotion criteria: what's reversible and what's not? (Template promotion: reversible, auto-promote. Permission changes: not reversible, queue for review. Mode transitions: reversible in current session only, require confirmation for transitions that persist.)
- How often does the controller poll? (Start with 5 seconds; measure; adjust.)
- What if the controller itself hangs? (Watchdog monitors controller; circular dependency resolved by having the watchdog be a simpler, more reliable component that only does heartbeat checks.)

### Phase 4: Feedback loop — the system learns

**Goal**: Successful outcomes improve the system automatically. Failed automation actions get demoted.

**Deliverables**:
- Lackpy's example bank updates from successful traces: when a trace doesn't match an existing template but succeeded, the controller adds it as a new example for the retrieval layer.
- Controller tracks its own accuracy: recommendations that get overridden are logged, recommendations that were applied and then led to trust degradation are logged, confidence on similar recommendations adjusts.
- Riggs produces a "controller report" showing which automation decisions paid off and which didn't.
- A `rigged review` CLI that surfaces decisions the human should look at: automated actions that caused trust drops, promoted templates that haven't been used, recommendations that keep getting overridden (the threshold might be wrong).

**Verification**:
- A template that gets promoted, applied, and then produces a failure should demote itself (or at least flag itself for review).
- A strategy instruction that helps Sonnet but hurts Opus should be detected by riggs's per-model trust analysis (this is where the model-dependent findings from the experimental program become actionable).
- The example bank for lackpy should grow organically over time, with the controller surfacing additions for human review before they're committed.

**Blockers to resolve**:
- What counts as a "failure caused by automation" vs an unrelated failure? (Temporal correlation + event chain analysis; not perfect but actionable.)
- How do we prevent the controller from gaming its own metrics? (Keep the metrics specified, not trained. The controller decides what to do based on rules; riggs decides whether the rules were good based on separate rules.)

### Phase 5: The quartermaster and cross-project

**Goal**: The system selects the right tool configuration per task; patterns transfer between projects.

**Deliverables**:
- Quartermaster pattern: a pre-task component that looks at the task description and selects the tool kit, mode, and model based on past observations. Implemented as a lookup over riggs's historical data, not as trained judgment.
- Cross-project template sharing: successful templates in project A become available in project B, with a compatibility check.
- Model-specific strategy injection: when a task is about to run with Haiku, the principle instruction gets injected automatically. When it runs with Opus, it doesn't.
- A `rigged suggest` CLI that takes a task description and prints the recommended configuration, giving the human a review step before automation.

**Verification**:
- A debugging task arrives; controller suggests debug mode + file tools + run_tests. A feature task arrives; controller suggests implementation mode + edit tools + bash. The suggestions match what the human would have chosen.
- A template from one project shows up as applicable in another project when the pattern matches.
- Haiku + principle and Opus + no principle should both work in the same session, with the controller switching automatically.

**Blockers to resolve**:
- Task classification: how do we categorize an incoming task? (First pass: keyword matching over the task description, same technique as lackpy's retrieval.)
- Cross-project trust: does a template that worked in project A earn trust in project B? (Default: no, it starts at baseline trust. Human can explicitly elevate.)

---

## Open questions

Things we don't yet know the answer to, that implementation will force us to resolve.

1. **Where does the shared store live?** `~/.rigged/store.duckdb` is a reasonable default, but per-project vs global vs hybrid needs a decision. Probably hybrid: global store for cross-project data (riggs's baseline trust, cross-project templates), per-project stores for project-specific data (blq builds, conversation logs).

2. **What's the concurrency story?** DuckDB allows multiple readers but only one writer at a time. If several tools write simultaneously, either they need to serialize (bottleneck) or they need to write to their own files and merge (complexity). Need to measure the actual contention before over-engineering.

3. **How do we version schemas across tool upgrades?** When blq changes its event format, how do consumers keep reading old events? Answer: `schema_version` field + read-time compatibility shims. Cost: modest. Must be designed in from the start.

4. **How do we handle the case where a tool is installed but the user doesn't want to use it?** The shared store should not require every tool to be present. Tools register themselves when they start; the controller works with whatever's registered.

5. **What's the authentication story?** If the shared store lives on disk in the user's home directory, the security model is "whoever can read the home directory can read the store." Fine for single-user use. Multi-user workstations or shared developer environments need more thought, but not for the first build.

6. **How does the controller interact with Claude Code's existing session lifecycle?** The controller is a long-running process; Claude Code sessions come and go. The controller watches events from whichever sessions are active. When a session ends, the controller notices via the event stream (no more events from that session_id) and stops watching. No tight coupling.

7. **What happens when the controller is wrong?** Every automated action is logged. Every automated action is reversible (templates can be demoted, mode transitions can be reverted, permissions can be restored). The human can see what the controller did via `rigged controller` and roll back via `rigged revert <action_id>`. If the controller's accuracy drops below a threshold, it can be disabled entirely.

8. **Does this need a UI?** For the first build, no — CLI is enough. Eventually, a dashboard would help the human see what's happening without running a dozen CLI commands. The dashboard is phase 6+.

9. **What do we call this thing?** Not "OS" — the user ruled that out. Candidates: nervous system (biological, matches Beer's cybernetics), substrate (honest but dry), fabric (technical), the supervisor, the keeper, the observer mesh. This plan uses "the integration layer" as a neutral placeholder. The public writeup will need a name.

10. **What's the blog writeup timeline?** Not until after the build stabilizes. Publishing the integration layer as a series before it actually works would be premature. The writeup should come after enough of Phase 1-3 is running that we can point to evidence.

---

## Dependencies between phases

```
Phase 1 (substrate + health)
    ↓
Phase 2 (riggs unified audit)
    ↓
Phase 3 (controller — System 3)
    ↓              ↓
Phase 4 (learning)  Phase 5 (quartermaster + cross-project)
```

Phases 1 and 2 are strictly sequential: riggs can't read from the shared store until the shared store exists. Phase 3 depends on phase 2 because the controller reads riggs's outputs. Phases 4 and 5 can run in parallel once phase 3 is stable. Both depend on phase 3.

Rough timeline estimate (for work at one-engineer pace, interrupted by other work):
- Phase 1: 2-4 weeks
- Phase 2: 1-2 weeks (once Phase 1 is solid)
- Phase 3: 3-6 weeks (the controller is the biggest new component)
- Phase 4: 2-4 weeks
- Phase 5: 4-8 weeks

Total: ~3-6 months of part-time work to get to a system that genuinely operates itself for most of what the human currently does manually.

---

## What this plan does not cover

Things deliberately out of scope for this plan. These may become separate plans later.

- **Sitting_duck improvements**. The AST extraction layer has known issues (documented in that repo). This plan assumes sitting_duck continues to work; improving it is a separate project.
- **Pluckit implementation**. The spec exists. Building pluckit is its own project that this plan depends on only in Phase 5 (if pluckit is ready by then).
- **Fine-tuning**. The integration layer enables fine-tuning (successful traces become training data) but doesn't actually do fine-tuning. That's a future phase.
- **Multi-user / team deployment**. Currently single-user. Team deployments need thought about shared stores, trust, and access control. Not covered here.
- **Cross-language support**. Everything assumes Python tooling. Supporting other language ecosystems is a separate plan.
- **The series writeup**. This plan is internal; the blog series about the integration layer comes after the build stabilizes.

---

## Next action

Before implementation starts, this plan needs:

1. **Verification pass with existing tool behavior**. Each per-tool section above is based on partial information. Read each tool's code, confirm what it actually does matches the description, note the discrepancies. Update this document.
2. **Schema sketch for the shared store**. Name the tables, define the columns, document the event types. This becomes a separate design doc that Phase 1 implements.
3. **Controller decision rules**. Enumerate the rules the controller will apply in Phase 3. Each rule is a specified pattern: "if X, then Y." This becomes a separate design doc for Phase 3.
4. **Review with the human**. This plan is a draft. Read it, disagree with parts of it, identify what's missing, adjust scope. Nothing should be built until it's been reviewed.

---

*Status: plan draft. Not reviewed. Not implemented. This document describes intent, not reality.*
