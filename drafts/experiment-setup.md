# Experiment Setup Guide

*What the next session needs to start running experiments.*

---

## Phase 0: Start immediately (Experiments 4+9+10 — longitudinal)

These run alongside normal work. Zero additional compute cost.

### Failure logging protocol

Create a file at `~/.claude/projects/*/memory/experiment_failures.md` (or a DuckDB table) that gets an entry every time something goes wrong in a conversation. Each entry:

```markdown
### [date] [session-id or conversation topic]
- **What happened:** [brief description]
- **Tool call(s):** [the tool call where the failure manifested]
- **Expected:** [what should have happened]
- **Actual:** [what did happen]
- **Classification:** infidelity | side_effect | partiality | compound | unclear
- **Classification notes:** [why this classification, or why unclear]
- **Computation level:** [0-8, what tools were involved]
- **Downstream consequence:** [what went wrong because of this]
```

The classification is Experiment 9. The computation level tracking feeds Experiment 8. The tool call patterns feed Experiment 10 (ratchet candidates).

### Ratchet observation protocol

During normal work, when you notice a bash pattern being used repeatedly:
1. Log the command pattern and frequency
2. Note whether it succeeded consistently
3. Note its world dependencies and side effects
4. Flag it as a promotion candidate
5. When you promote it (build a structured tool), record what type commitments the new tool makes and whether the implementation backs them

This is Experiment 10's Stage 1 (discovery) and Stage 2 (crystallization) measurement.

### What already exists

- Claude Code's conversation storage (JSON files in ~/.claude/)
- DuckDB + the user's extension ecosystem (duck_hunt for log parsing, duck_tails for git history, sitting_duck for AST parsing, blq for structured build output)
- Fledgling for structured code navigation

### What needs to be built

- [ ] DuckDB queries to extract tool call sequences from conversation logs
- [ ] The failure logging template (above)
- [ ] A hook or reminder to log failures (could be a Claude Code hook that runs at session end)

---

## Phase 1: Experiment 12 (definition consistency)

No infrastructure needed. This is a textual analysis.

### Input
All published posts (blog/00-intro.md through blog/09-building-with-ma.md), the formal companion, the case studies, the configuration ratchet, the residual framework, and "Where the Space Lives."

### Protocol
For each use of "ma" in the published series:
1. Quote the passage
2. What does it mean under "the space between inputs and outputs"?
3. What does it mean under "the capacity for informed judgment"?
4. What does it mean under "the residual between interface promise and behavior"?
5. Do the three agree? Which is most informative?
6. If "interface ma": does "capacity for informed judgment at the interface" work, or does it need a qualifier?

### Output
A structured document with consistency rate, divergence cases, and recommendations for v2.

### How to run
Dispatch an agent with the protocol and the file list. It reads, it analyzes, it reports. One session, 1-2 hours.

---

## Phase 2: Experiment 3 (computation channel phase transition)

First controlled experiment. Needs infrastructure.

### Task suite (shared infrastructure)

Need 20+ coding tasks. Sources:
- Tasks against the user's own repos (sitting_duck, duck_tails, Fledgling, blq)
- SWE-bench Lite tasks (public, standardized)
- Custom tasks designed for specific properties (planning-matters tasks for Exp 11)

Each task needs:
- A clear description
- A success criterion (testable — does the code work?)
- A quality criterion (human-judged — is it good?)
- A difficulty estimate
- Tags: needs-bash, planning-matters, failure-mode-prone

### Three tool configurations

Create three CLAUDE.md / settings variants:

**Condition A (Fledgling only, levels 0-2):**
```
Tools: Fledgling (search, find_definitions, read_lines), Read, Glob, Grep, Edit, Write
No Bash access.
```

**Condition B (Fledgling + Bash read-only, levels 2-3):**
```
Tools: Fledgling, Read, Glob, Grep, Edit, Write, Bash (read-only: cat, grep, find, ls, git status/log/diff)
```

**Condition C (Fledgling + Bash read-write, level 4):**
```
Tools: Fledgling, Read, Glob, Grep, Edit, Write, Bash (sandboxed: filesystem bounds, no network, resource limits)
```

### Specified observer

A rule-based predictor. Start simple:
- Given the last 3 tool calls and the task description, predict the next tool call (tool name + argument pattern)
- Bigram model: P(tool_n | tool_{n-1})
- Task-aware: P(tool_n | tool_{n-1}, task_type)
- Build from conversation log data using DuckDB

### Sandbox diffing

A Claude Code hook (or wrapper script) that:
1. `git init` in the task directory at session start
2. `git add -A && git commit` after every tool call that modifies files
3. Produces a full diff history queryable by duck_tails

### Measurements to collect per run

- Full tool call sequence with timestamps
- Sandbox diff history (via duck_tails)
- Task outcome (success/failure)
- Quality assessment (human or automated)
- Observer predictions vs actual calls (gap rate)
- Behavioral variance (across repeated runs)

---

## Phase 3: Experiments 11 and 8

These need the task suite from Phase 2 plus:

### For Experiment 11 (placement)

Three phase-gated tool configurations:
- Planning phase: broad / medium / narrow tool sets
- Execution phase: narrow / medium / broad tool sets
- A mechanism to switch tool sets between phases (could be a session break with different CLAUDE.md, or a hook that swaps the tool configuration)

Quality rubric for blind human judging:
- Approach quality (1-5): Did the plan address the right problem? Consider the right edge cases?
- Implementation quality (1-5): Given the approach, is the code correct, clean, and maintainable?
- Score these independently — judge sees plan without implementation, and implementation without knowing the condition

### For Experiment 8 (System 3)

A specified pattern detector. DuckDB queries running on conversation logs:
```sql
-- Detect Write-Test oscillation
-- Detect scope creep (files not in task description)
-- Detect stale reference (Read returning content that differs from context)
```

Could run as:
- A Claude Code hook that checks after each tool call
- A post-conversation analysis script
- A real-time monitoring process

The planted failure tasks: coding tasks where the natural first approach leads to a known anti-pattern. Need to identify 5-10 such tasks from real experience.

---

## Recommended next session plan

1. **Set up failure logging** — create the template, add to memory as a protocol
2. **Run Experiment 12** — dispatch an agent to do the definition consistency analysis
3. **Start building the task suite** — identify 20+ tasks from existing repos
4. **Build the specified observer** — DuckDB queries over existing conversation logs to build the bigram/trigram model
5. **Set up sandbox diffing** — the git-init hook

Items 1-2 can happen in the first session. Items 3-5 are the infrastructure build for the controlled experiments.
