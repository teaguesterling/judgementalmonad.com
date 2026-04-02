# The Tools That Built Themselves

*What happens when you keep scratching itches for a year.*

---

## The human ratchet

The [Ratchet Fuel](../fuel/index) series describes a mechanism for agent systems: friction produces signal, signal crystallizes into infrastructure, infrastructure reduces friction. The system gets better with use.

The same mechanism runs on the human side. Every tool described in this section started as a friction point — a workflow that was annoying, or mechanical, or opaque. None of them came from a plan. They came from the moment where you think "I've done this enough times" or "I don't want to think about this anymore" or "there has to be a better way to hand this off."

That's the ratchet. The agent version captures failed tool calls and promotes patterns to templates. The human version captures repeated annoyance and promotes it to a script, then a tool, then an MCP server. Same mechanism, different actor.

---

## How they came to be

The tools cluster around three motivations. Not "what they do" — why they exist.

### Lock in what works with Claude

Some patterns just work better when Claude has structured access instead of guessing.

**fledgling** started because Claude was grepping for function definitions and missing half of them. Cross-file resolution, call graph traversal, structural similarity — these are things a code intelligence server does well and an LLM does inconsistently. The tool doesn't replace Claude's understanding; it gives Claude reliable facts to reason about.

**kibitzer** watches Claude's tool calls and suggests structured alternatives when it sees patterns that have better options. "You've searched for this function three times — try `find_callers` instead." It's not enforcement, it's coaching. The observations feed back into strategy instructions and tool design.

**blq** exists for the seam between human and agent. I run a build. Instead of copy-pasting terminal output into the conversation — losing formatting, truncating at context limits, breaking the flow — I say "check `blq errors`" and Claude queries the structured results directly. The tool isn't for me or for Claude. It's for the handoff between us.

### Lock in the mechanical

Some workflows are rote. They don't benefit from thought. Making them automatic frees attention for things that do.

**jetsam** crystallizes git workflows. `jetsam save` stages, commits, and pushes with a preview plan before execution. `jetsam sync` rebases and resolves. `jetsam ship` opens a PR. Each command does what you'd do manually, but without the five-step "did I forget to push?" dance. It shows you the plan first and asks for confirmation — the human equivalent of a sandbox preview.

**tmux-use** sets up terminal sessions with configurable layouts, color-coded by project. It sounds trivial. It eliminated the daily friction of "which tmux session was I in?" and "is this the right project directory?" for both me and for Claude Code instances running in parallel sessions.

**git-wt** wraps git worktrees in a structured layout. Feature branches get isolated directories without switching context in the main workspace. Again, trivial in concept. In practice, it meant I could have three features in progress without the "stash, switch, pop, merge, switch back" dance.

**init-dev** bootstraps a new project with fledgling, blq, and jetsam configured. Auto-detects project type (Python, Rust, C++, Node, DuckDB extension) and sets up the right hooks and commands. The kind of thing you do once per project and forget about — unless you create 15 projects in a year, in which case you automate it.

### Wrap what you don't fully understand

Some tools exist because the underlying system is complex and I don't need to internalize all of it. A good wrapper means I interact with the concept, not the implementation.

**ffs** (Find Failed Sessions) handles Claude Code crash recovery. When a session dies mid-task, there's session state scattered across temporary files, conversation logs, and git state. I don't want to learn the internals of session management. I want a command that says "here's what was happening, here's what you can recover, here's how." ffs does that.

**nsjail-python** wraps Google's nsjail sandboxing tool. nsjail has dozens of flags controlling namespaces, mounts, cgroups, and resource limits. I need sandboxing for blq's test execution. I don't need to become a Linux namespaces expert. The Python wrapper exposes the concepts (read-only filesystem, no network, process isolation) and handles the flags.

**DuckDB extensions** across the suite make querying easier without memorizing SQL patterns. sitting_duck's `ast_select()` function, fledgling's `find_definitions()` macro, duck_tails' git history tables — each wraps a complex query pattern in a function call. The SQL is still there if you need it. Usually you don't.

---

## A day with the tools

Here's what an actual work session looks like. Not a polished demo — the messy reality of how these tools compose.

### Morning: starting a feature

`tmux-use` opens the project session. Two panes: editor and terminal. `git-wt` creates a worktree for the feature branch — isolated from whatever's in progress on main. `init-dev` already ran when the project was created, so blq, fledgling, and jetsam are configured.

I describe the feature to Claude. Claude uses fledgling to understand the code structure — `find_definitions` for the entry points, `find_callers` to map the blast radius, `code_structure` for an overview. This takes 30 seconds and produces a reliable map. Without fledgling, Claude would grep around for a few minutes and build a less accurate picture.

### Midday: building

I'm editing code. Claude is editing code. We're working in the same worktree but different files. When Claude makes changes, I can see the diffs in real time.

Claude runs tests through blq: `blq run test`. I can see the results too — `blq errors` shows failures, `blq output` shows the full log. If Claude gets stuck on a test failure, I check `blq errors` myself, see the same structured data Claude sees, and give specific guidance. No copy-pasting. No "can you show me the full output?" The shared tool is the shared context.

kibitzer fires periodically. "You've made 5 edits without running tests — consider running the test suite." Sometimes it's useful. Sometimes I ignore it. The observations log either way — follow rates tell me which suggestions are actually helpful.

### Afternoon: integration

The feature works. `jetsam save 'feat: add timeout parameter'` — preview shows 4 files staged, commit message generated from the diff. Looks right. Confirm. `jetsam sync` rebases on main — no conflicts. `jetsam ship` opens the PR.

If I'd been working with agent-riggs active, the session trace would already be analyzed: which tool sequences were effective, which patterns repeated, which could be promoted to templates. The next time someone (or some agent) does a similar feature, the tooling is slightly more prepared.

### The accumulation

No single tool here is impressive. tmux session management? Git worktree wrappers? A build log viewer? Each one is a small thing.

But the accumulation changes what kind of work is possible. I don't think about terminal layout. I don't think about branch switching. I don't think about how to share build results with Claude. I don't think about crash recovery. Each tool removed one friction point, and the freed attention compounds.

A year ago, half my time with Claude was infrastructure: setting up the environment, sharing context, recovering from crashes, managing git state. Now that's handled. The time goes to the actual work.

That's the same ratchet the fuel series describes for agents — but running on the human side. Friction → tool → less friction → more ambitious work → new friction → new tool. It only turns one direction.

---

```{seealso}
- [Ratchet Fuel](../fuel/index) — The agent-side ratchet
- [Closing the Channel](../fuel/05-closing-the-channel) — Where structured tools come from
- [The Coach](../patterns/05-the-coach) — Kibitzer's design as a pattern
```
