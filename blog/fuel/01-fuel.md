# Fuel

*Every failed tool call is a frontier model's full weight manifold producing something a lookup table could have prevented. That's expensive. That's also data.*

---

## The agent is failing right now

Open your conversation logs. Not the polished summary, not the final output — the raw log. Every tool call, every result, every error.

Your agent failed seventeen times in the last session. Three permission denials when it tried to write to a directory outside its sandbox. Four repeated `grep -r` calls with slightly different patterns, searching for a file it already read two hundred turns ago but can no longer find in its context. Two timeouts on a test suite it should have run in smaller batches. One schema mismatch where it passed a string to a function expecting an integer. And seven calls where it re-read the same file because the conversation had grown long enough that earlier reads had scrolled out of its effective window.

Those seventeen failures cost you roughly twelve dollars in inference. The model engaged its full decision surface — billions of pathways through the weights — to produce proposals that specified rules rejected or that the environment simply ignored. Each failure was a frontier model doing its most expensive work to arrive at something a config file could have prevented.

That's waste. It's also the most valuable signal your system produces.

Every one of those failures is a data point about where your system's configuration doesn't match the task's requirements. Not a vague, interpretive data point. A precise one. The failure category tells you what kind of configuration change would fix it. The failure frequency tells you how much inference you're burning. The failure location tells you which boundary to move.

The failures are not noise. They are the product roadmap.

---

## The failure stream

Claude Code stores every conversation as a sequence of messages. Each tool call is logged with its arguments, its result, whether it succeeded, and how long it took. When you point DuckDB at these logs, the failures separate into five categories. Each category has a different shape, a different cause, and a different fix.

### Permission denials

The agent tried something outside its allowed set. It attempted to write to `/etc/hosts`, or called `git push` when only read operations were permitted, or tried to install a package in a locked-down environment.

Two possible causes, and they demand opposite responses.

**The mode is too restrictive.** The agent genuinely needs this capability for the task. It's trying to push because the task is "deploy this change," and you forgot to enable write access to the remote. The fix: open the boundary. Add the capability to the mode's permission set.

**The agent lacks constraint visibility.** The agent doesn't know what it can't do, so it discovers the boundary empirically — by slamming into it. Each denial costs an inference cycle. The agent spends trained reasoning to construct a careful proposal, the sandbox rejects it in microseconds, and the agent tries again with a slight variation. The fix: make the constraint visible. Tell the agent in its system prompt what it cannot do. Remove the knowledge that the capability exists, or add an explicit prohibition. Either way, eliminate the expensive middle state where the agent knows something is there but can't get to it.

### Repeated patterns

The agent is looping. It runs `grep -r "TODO" ./src`, gets results, processes some of them, and twenty turns later runs `grep -r "TODO" ./src` again. Or it tries three variations of a `find` command looking for a config file that doesn't exist.

The agent's model of its environment is wrong. It expects the grep results to still be accessible in its context (they scrolled out). It believes the config file exists (the documentation it read was stale). It thinks a slightly different flag will change the outcome (the tool doesn't support that flag).

Repeated patterns are the highest-value ratchet fuel. Each repeated pattern is a specified operation that the agent has already validated through use. The agent ran `grep -r` successfully a thousand times. That's a thousand data points saying "agents need codebase search, and this is the interface they converge on." The fix: promote the pattern to a structured tool. `grep -r "pattern" path` becomes `search(pattern, path)` — same functionality, categorically different grade. The bash call was a computation channel. The structured tool is a data channel. The inference cost of selecting the right grep flags drops to zero.

### Timeouts

The computation took too long. A test suite ran for ten minutes. A build command hung. A recursive search hit a massive directory tree.

The approach is wrong for this subtask. The agent is using a tool designed for small inputs on a large input, or using a synchronous approach where an asynchronous one is needed, or running an entire test suite when it needs a single test.

Timeouts are often a signal that the agent needs a different mode — one with different tools scoped to the actual problem size. Running the full test suite is the right thing to do in CI. During iterative development, the agent needs `run_test(specific_test)`, not `run_all_tests()`.

### Success rate decay

Early in the conversation, things went well. The first thirty tool calls succeeded. Good results, productive work, clear progress. Then somewhere around turn forty, the success rate dropped. The agent started re-reading files. Repeating searches. Producing edits that conflict with earlier edits. The proposals got less coherent.

The context is filling with unproductive content. Every tool result goes into the conversation. Results from early, productive exploration are now buried under hundreds of turns of subsequent work. The agent's effective window — the part of the context it can actually attend to — is dominated by recent, potentially less relevant content. The signal-to-noise ratio in the context is dropping.

The fix is structural, not behavioral: compaction or mode switch. Summarize the productive work, clear the accumulated noise, and start a fresh context with the summary as input. Or switch to a mode that forces a structured handoff — compress the current state through a co-domain funnel and start the next phase with a clean context and a clear objective.

### Scope exhaustion

The context window is approaching capacity. The agent is running out of room. It can't fit both the relevant context and the new work into the remaining space.

This is not a problem that more turns will solve. The conversation needs restructuring, not continuation. The fix: break the task into subtasks, each with its own context. Use structured handoffs — the output of one conversation becomes the scoped input of the next.

---

## The expensive middle state

The worst place for a system to be is the middle: the agent *knows* something exists but *can't get to it*.

Consider an agent operating in a sandbox. It has read access to the codebase. It knows — from documentation in its system prompt, from prior conversation context, from the structure of the files it's read — that a database exists with user records. It can see references to the database connection string. It can read code that queries the database.

But it doesn't have database access. The sandbox doesn't include it.

What happens next is predictable and expensive. The agent tries to connect to the database. Permission denied. It tries a different connection method. Permission denied. It looks for a cached export of the data. Not found. It tries to infer the data from the code that queries it. Partial success, but unreliable. It asks in its output whether someone can grant it access. Six tool calls, four failures, two partial results, and the full weight manifold of a frontier model engaged each time.

This is knowledge without access — the agent has a *knowledge edge* to the database projection. It knows the interface. It can reason about it. But it has no *access edge*. The knowledge shapes its reasoning without enabling its work.

The cost is not just the failed tool calls. It's the decision surface consumed by the knowledge. Every reasoning step that considers the database, proposes a way to access it, or works around not having it is inference budget spent on a boundary that a specified rule could have resolved before the conversation started.

Two resolutions, same as with permission denials:

**Grant access.** If the agent needs the database to do the task, add the access edge. The sandbox configuration should include it from the start. The knowledge edge without the access edge was a configuration error.

**Remove the knowledge.** If the agent doesn't need the database — if the task can be completed with the codebase alone — remove the knowledge edge. Don't tell the agent about the database. Don't include the connection string in scope. Don't let it read the files that reference it. The agent that doesn't know about a resource won't spend inference probing for it.

Either way, the expensive middle state is eliminated. The fix is always a configuration change — a specified modification to the projection filter that determines what the agent can see and what it can touch.

---

## The product roadmap

Each failure category maps to a specific configuration fix. This is not metaphorical. The mapping is precise enough to automate:

| Failure category | Signal | Configuration fix |
|---|---|---|
| Permission denial (justified) | Agent needs capability it lacks | Open the boundary — add to projection filter |
| Permission denial (unjustified) | Agent probing blindly | Close the knowledge — make constraint visible or remove knowledge edge |
| Repeated pattern | Agent converged on a bash solution | Promote to structured tool — close the computation channel |
| Timeout | Wrong tool for this problem size | Add scoped alternative — mode with right-sized tools |
| Success rate decay | Context filling with noise | Trigger compaction or mode switch — structured handoff |
| Scope exhaustion | Task too large for one context | Decompose — subtask with structured handoffs |

Read this table from left to right and you have a failure log. Read it from right to left and you have a development roadmap.

Your next three infrastructure investments are sitting in your failure logs right now. The tool you should build next is the bash pattern your agent runs most often and succeeds at most reliably. The permission you should change next is the one that generates the most denials. The mode switch you should automate next is the one the agent's success rate decay keeps telling you to make.

---

## The trust gap as learning surface

Here is the reframe that changes how you think about sandbox configuration.

The trust gap is the distance between what the agent can reach (the sandbox boundary) and what you expect it to reach (the task requirements). The standard framing: this gap is risk. Minimize it. Lock the sandbox down to exactly what the task needs. Reachable equals expected. Safe.

That framing is correct and incomplete.

If reachable exactly equals expected, the system never discovers anything. Every tool call succeeds. Every access request is granted. Every path the agent takes is a path you already anticipated. The system produces no failures — and therefore no data about where the configuration could improve. The ratchet has no fuel. The system is as good as it will ever be on day one.

The gap is not only risk. It's the learning surface.

A system with instrumented gap — where failures are cheap, visible, and logged — produces the data that drives configuration improvement. The agent that hits a permission boundary and fails tells you something about what it needed. The agent that loops on a bash pattern tells you which tool to build next. The agent that exhausts its context tells you where the task decomposition belongs.

No gap, no signal. Too much gap, too much risk. The design question is not "how do I eliminate the gap?" It's "how do I instrument it?"

---

## Extracting the failure stream

Claude Code stores conversation logs as JSONL. Each message has a `type`, a `message` object with `role` and `content` blocks, and metadata including `sessionId` and `timestamp`. Tool use shows up as content blocks with `type: "tool_use"` containing `name` and `input`; results come back as `type: "tool_result"` with `content` and `is_error`.

Point DuckDB at these files with `read_json_auto` and you can extract every tool call, every result, and every error. The fields you care about:

- **`name`** (from tool_use blocks) — which tool was called
- **`input`** (from tool_use blocks) — the arguments, including `command` for Bash calls
- **`is_error`** (from tool_result blocks) — whether the call failed
- **`content`** (from tool_result blocks) — the error message or result text

From these four fields, you can classify every failure in the taxonomy above. Group by `name` and the structure of `input` to find repeated patterns. Filter `is_error = true` and scan `content` for "permission denied" or "EACCES" to find boundary hits. Track the rolling error rate across a session's messages to detect success rate decay. Count how many times the same `file_path` appears in Read calls to detect scope exhaustion.

The queries are simple aggregations. The data arrives for free as a byproduct of the agent doing work. Run the diagnostics after a session, make one configuration change, and query again. The failure stream composition should shift. If it doesn't, you changed the wrong thing.

---

## Three design variables

The failure stream is shaped by three decisions you make before the conversation starts. Each is a knob. Turn them deliberately.

### How much gap: sandbox configuration

A tight sandbox (only the tools the task needs, only the files in scope) produces few failures and little learning. A wide sandbox (bash access, broad filesystem read, network access) produces many failures and rapid learning — but with real risk if the agent acts on something it shouldn't.

The right setting depends on the phase. Early exploration: wider gap, heavy logging, cheap failures. You're discovering what the agent needs. Production use: tight gap, validated tools, the ratchet has already turned. The exploration budget was spent during development.

### Where the gap lives: mode and projection filter

Not all gaps are equal. A gap in read access (the agent can't see a file it needs) produces a different failure than a gap in write access (the agent can't modify something it needs to change). A gap in tool availability (the agent needs to run tests but has no test runner) produces a different failure than a gap in constraint visibility (the agent doesn't know it can't push to main).

The projection filter — which world projections the agent can see, with what access modes — determines where the failures will happen. Design the filter to put failures where they're cheap and informative. Read access failures are cheap (no side effects). Write access failures are more expensive (the agent may have done preparatory work). Tool availability failures are the cheapest of all (instant rejection, no wasted reasoning).

### What happens when it produces a failure: monitoring and crystallization

A failure that nobody sees is waste. A failure that gets logged is data. A failure that gets analyzed is a ratchet candidate. A failure that gets crystallized into a configuration change is infrastructure.

The pipeline: log everything (DuckDB over JSONL handles this), query periodically (the SQL above), identify patterns (frequency and success rate), crystallize (either open the boundary or close the knowledge), and verify (the failure pattern should disappear from the next session's logs).

This pipeline is specified end to end. No trained judgment in the loop. The analysis is SQL. The crystallization decision — open or close — may require human judgment. But the data that informs the decision is specified, structured, and complete.

---

## Listen

Your agent is failing right now. It failed during the last session. It will fail during the next one. Those failures are not a problem to eliminate. They are the most precise signal you have about what to build next.

The permission denials tell you which boundaries to move. The repeated patterns tell you which tools to build. The timeouts tell you which approaches to replace. The success rate decay tells you when to restructure. The scope exhaustion tells you where to decompose.

Every failure that gets crystallized into a configuration change — a new tool, a visibility constraint, a mode boundary, a handoff schema — makes the system cheaper to run, more predictable to operate, and more trustworthy to deploy. The ratchet turns. The specified base grows. The inference frontier shrinks to the problems where trained judgment actually belongs.

The failures are telling you what to build. Listen.

---

*Previously: [The Ratchet Review](00-ratchet-review.md)*
*Next: [The Two-Stage Turn](02-the-two-stage-turn.md)*
*For the formal treatment: [The Ma of Multi-Agent Systems](../ma/00-intro.md)*
