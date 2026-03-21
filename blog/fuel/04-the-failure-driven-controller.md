# The Failure-Driven Controller

*Coordination routes messages. Control changes modes. If you need an LLM to decide which one, your modes are wrong.*

---

## Five systems, one gap

Stafford Beer's Viable System Model says any viable organization needs five functions. Agent systems have four of them:

| System | Function | In agent architecture |
|---|---|---|
| **System 1** | Operations | The tools — they do the work |
| **System 2** | Coordination | The Harness — routes messages, enforces permissions, manages state |
| **System 4** | Intelligence | The model — scans the environment, proposes actions, reasons |
| **System 5** | Identity/purpose | The human — decides what matters, mediates trade-offs |

**System 3 — control — is missing.** Coordination (System 2) follows the same rules on every turn. It doesn't care whether the agent is thriving or spiraling. It processes the current tool call against the current permission set and moves on. It has no memory of the last twenty turns. It has no opinion about whether the configuration is working.

Control watches the trajectory. It notices that the agent has failed twelve times in the last fifteen turns. It notices that the same grep pattern has appeared three times with no progress. It notices that the success rate was 90% at turn twenty and is 40% at turn sixty. And it does something about it: switches the mode, tightens the permissions, forces a re-plan.

Beer was specific about what System 3 does: **monitor** whether the current configuration is working, **intervene** when it isn't, and **allocate resources** across competing demands. It's the factory floor manager — not the CEO (System 5), not the strategist (System 4), not the shift coordinator (System 2). The floor manager who notices the line is backing up and moves people to where they're needed.

Most agent systems have coordination. Almost none have control. The human fills that gap manually — watching the output, noticing the spiral, hitting Ctrl-C. That works. It also means your system can't get better at managing itself.

Beer also insisted: System 3 must be simpler than what it manages. If the controller requires the same kind of reasoning as the agent, you haven't built a controller — you've built another agent. The people using LLM-backed guardrails are putting System 4 where System 3 should be. The failure-driven controller is the specified alternative.

This post builds it.

---

## Modes already exist

Modes aren't a theoretical proposal. They're already shipping in production agent systems — they just aren't called modes yet, and nobody has a controller managing them.

### Claude Code

Claude Code has three modes — plus a hidden fourth:

**Standard mode** — the default. The agent can read anything. Write operations (Edit, Write, Bash with side effects) require user approval. The permission gate is the System 3 function performed manually: the human evaluates each proposed write and allows or denies.

**Accept-edits mode** (`--accept-edits`) — all file writes are auto-approved. Bash still requires approval. The trust surface widens: the agent can modify the codebase without per-operation human review.

**Plan mode** (`--plan`) — no edits at all. The agent reads and reasons but doesn't execute. This is a qualitative shift: the system drops from computation channel level 4+ to level 0-2. The dynamics go from self-amplifying to convergent. The regulatory burden drops to near-zero.

**Dangerously-skip-permissions** (`--dangerously-skip-permissions`) — everything auto-approved, including Bash. The trust surface is the entire sandbox. Maximally capable, maximally hard to regulate.

For all of these except the last, individual tool calls are further controlled by allow/deny lists — per-tool permission rules that operate independently of the mode. The mode sets the overall trust posture; the allow/deny lists handle the per-tool details.

### Claude Desktop

Claude Desktop has a different mode structure, oriented around capability bundles rather than permission levels:

**Standard mode** — conversational. The model reasons and responds. No tools, no web access, no file system. Pure co-domain funnel: deep reasoning, text output.

**Research mode** — adds web search and extended thinking. The model can pull in external information and spend more computation on reasoning. The trust surface expands to include web content, but there are no write effects — the model reads from the web and reasons, but doesn't modify anything.

**Tool-use configurations** — when connected to MCP servers, the model gains access to structured tools. Each MCP server is a named capability grant. The user decides which servers to enable.

### Modes across the industry

This isn't an Anthropic pattern. The industry has converged on modes independently:

**Cursor** has Agent mode (full tool access, terminal commands), Ask mode (read-only, conversational), and Edit mode (scoped inline changes). Agent ≈ implementation, Ask ≈ review, Edit ≈ scoped implementation.

**GitHub Copilot** in VS Code has Chat (conversational, no edits), Edits (multi-file with diff preview), and Agent (autonomous, terminal access). Same three-tier structure.

**OpenAI Codex CLI** runs in an isolated sandbox by default — sealed environment, structured output. That's the snapshot-seal-funnel pattern as the *only* mode.

### What all these modes have in common

Every system implements modes as **named configurations that determine what the agent can do.** The mode is a permission filter — which tool calls require approval (Claude Code), which capabilities are available (Claude Desktop), or which interaction pattern applies (Cursor, Copilot).

What's missing in all of them is the *other* dimension of mode control: which *projections of the world* are accessible, and — critically — **who manages the transitions.** Right now the human switches modes manually. There's no controller watching the failure stream and saying "you've been spinning for twenty turns, drop to plan mode."

### Modes as tool-set configurations

A richer mode system ties modes to tools, not just to permission gates. Each mode defines:

1. **Which tools are available** — not just whether they're auto-approved, but whether they exist in the agent's tool set at all
2. **Which world projections are accessible** — which files, directories, or resources the agent can see and with what access (read, write, sealed-write)
3. **What output schema constrains the boundary** — what structure the mode's output must conform to

Here's what that looks like for a development workflow:

### Debug mode

Tools: `{Read, Glob, Grep, Bash(read-only), RunTests}`. No `Edit`, no `Write`. Tests are read-only ground truth. Implementation is readable but not writable.

The agent can be maximally invasive in its *analysis* — read anything, search anything, run tests with extra flags — but it can't modify the codebase. The only output is a structured diagnosis: which test failed, what the expected behavior was, what the actual behavior was, where the discrepancy lives, and a hypothesis about why.

This is Claude Code's plan mode, but scoped to debugging: broad read, zero write, structured output through the funnel.

### Implementation mode

Tools: `{Read, Glob, Grep, Edit, Write, Bash(sandboxed), RunTests}`. Full write access to implementation files. Tests are read-only — not in the tool set's write scope.

The agent writes code, runs tests, iterates. The test suite is the verification layer — a constraint, not a suggestion. The agent cannot edit tests. If it has simultaneous write access to both tests and implementation, it can resolve a failing test by changing the test. That's not a hypothetical — it's a natural optimization target. The mode boundary prevents it by construction.

The diagnosis from debug mode flows in as a structured artifact — the agent knows what to fix and why.

### Test development mode

Tools: `{Read, Glob, Grep, Edit(tests only), Write(tests only), RunTests}`. Tests are writable. Implementation is read-only.

The agent is writing specification, not implementation. It can read the implementation to understand what it does, but cannot modify it. The separation ensures that test development is a distinct activity — you're defining what the system *should* do, not changing what it *does*.

### Review mode

Tools: `{Read, Glob, Grep}`. Everything is read-only. The agent reads the codebase with full trained reasoning and outputs a structured assessment: findings, severity, recommendation.

Zero write coupling to anything. This is the safest mode — the regulatory burden is minimal because you only need to evaluate the assessment, not worry about side effects. This is a co-domain funnel: high internal reasoning compressed through a narrow output interface.

---

## Why the test boundary matters

The separation between tests and implementation across modes deserves emphasis because it prevents a specific failure that current practice allows.

When an agent has simultaneous write access to tests and implementation, it can reshape its own constraints. The test suite moves from being a fixed boundary to being part of the mutable world. That's structurally equivalent to the agent modifying its own controller — it can change the definition of success to match whatever it already produced.

The mode boundary prevents this by construction:

- In **debug mode**, tests are read-only.
- In **implementation mode**, tests are read-only.
- In **test development mode**, implementation is read-only.

At no point does the agent have simultaneous write access to both sides. The separation exists because tests and implementation have different trust roles, even though they're written in the same language, live in the same repository, and look the same to the filesystem.

This is the golden rule applied architecturally: change implementation OR tests, never both at the same time. The mode enforces it.

---

## Mode transitions: failure-triggered, specified rules

Who decides when to switch modes? Not the agent. Not an LLM. The failure stream decides.

Mode transitions are triggered by failure patterns — specified thresholds over specified counters. No trained judgment in the transition logic.

### Test failure in implementation mode triggers debug mode

The test runner returns a non-zero exit code. That's a Layer 1 signal — binary, unambiguous. The controller switches to debug mode automatically. The failing test name, the error output, and the agent's recent changes are packaged as the handoff context.

No judgment needed. Exit code is non-zero. Switch modes.

### High failure rate triggers mode tightening

If the agent hits fifteen permission denials in twenty turns, the controller drops the permission level. Auto-accept becomes default. Default becomes plan mode. The agent was operating with more freedom than the task warranted; the failure rate proved it.

This is a specified threshold: `denial_count >= 15 AND window_size <= 20`. The transition is an if/then rule.

### Sustained success suggests mode loosening

If the last thirty tool calls succeeded within constraints, the controller surfaces a recommendation: "Consider enabling auto-accept for this session." But it does not enable it. The human decides.

This is the critical asymmetry. Tightening is safe to automate — you're reducing capability, which reduces risk. Loosening requires human authorization — you're expanding capability, which expands risk. The controller can pull the brake automatically. It cannot release the brake automatically.

### Repeated loop detection triggers re-planning

If the same tool call pattern appears three times with no progress — same command, similar arguments, same outcome — the controller forces a mode switch to plan mode. It packages what was tried and what failed into a structured summary and makes the agent re-plan rather than continue looping.

Three repetitions is the threshold. Progress is measured by whether the outcome changed between attempts.

### Context exhaustion triggers compaction

When the token count crosses a specified threshold (say, 80% of the context window), the controller triggers either compaction (summarize and compress) or a fresh context with structured handoff. The conversation needs restructuring, not more turns.

---

## The counters

The controller's monitoring function runs on five counters. Each is a specified metric — arithmetic over the tool call log. No inference required.

**Repeated pattern count.** How many times has the agent issued the same tool call (same tool, same argument structure) within a sliding window? This catches loops. Threshold: 3 repetitions with no change in outcome.

**Timeout count.** How many tool calls exceeded the time limit in the current window? This catches wrong-tool-for-the-job situations. Threshold: 3 timeouts in 10 turns.

**Success rate (sliding window).** What fraction of the last N tool calls succeeded? This catches context decay — the point where the conversation has gotten long enough that the agent starts producing worse proposals. Threshold: success rate drops below 50% over a 10-turn window.

**Scope utilization.** What percentage of the context window is consumed? This catches scope exhaustion before it becomes a crisis. Threshold: 80% consumed.

**Permission denial rate.** What fraction of recent tool calls were permission denials? This catches mode-task mismatch — the agent needs capabilities the current mode doesn't provide, or the agent doesn't know its constraints. Threshold: denial rate above 30% in a 20-turn window.

Each counter is a number. Each threshold is a comparison. Each transition is an if/then rule. The controller is a state machine, not a language model.

---

## The asymmetry

The controller can do two things: tighten and recommend.

**Tightening is automatic.** When failure counters cross thresholds, the controller reduces capability without asking. Drop from auto-accept to default. Switch from implementation to debug. Force a re-plan. Each of these reduces the agent's freedom, which reduces the risk of further damage. Safe to automate.

**Loosening is a recommendation.** When success counters cross thresholds, the controller produces a structured suggestion: "The last 30 calls succeeded. Consider enabling auto-accept." The suggestion goes to the human. The human decides.

This asymmetry is deliberate. It reflects a fundamental property of control systems: reducing capability is a safe default, expanding capability requires authorization from the entity that bears the risk. The controller can always make things safer. It can never make things riskier without permission.

In practice, this means the controller's automatic interventions are always conservative. It will switch to debug mode too eagerly rather than too late. It will force re-plans more often than strictly necessary. The human can override — "no, stay in implementation mode, I know what I'm doing" — but the default is caution.

The human is not in the control loop on every turn. The human is in the control loop on *expansion* decisions. Everything else is automated.

---

## Code ships: prototype mode controller

Here's a prototype controller that monitors a conversation log and triggers mode transitions. It reads JSONL log entries, tracks the five counters, and outputs structured recommendations.

This is a prototype. It's meant to be run against conversation logs to test the thresholds and transitions against your actual failure patterns before you wire it into a live system.

```python
#!/usr/bin/env python3
"""
Failure-driven mode controller (prototype).

Reads a pre-processed tool call stream (JSONL), tracks failure counters,
and outputs mode transition recommendations.

Each input line is a JSON object with:
  - tool: tool name (e.g., "Bash", "Edit", "Read")
  - arguments: dict of tool arguments (e.g., {"command": "grep -r ..."})
  - success: bool
  - result: string (error message or output preview)
  - duration_ms: int (optional)
  - cumulative_tokens: int (optional)

Claude Code's raw JSONL has a nested structure (message.content blocks
with tool_use/tool_result types). Use Fledgling's tool_calls() macro
or a preprocessing script to flatten it into this format.

Usage:
    python mode_controller.py tool_calls.jsonl
"""

import json
import sys
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Mode(Enum):
    DEBUG = "debug"
    IMPLEMENTATION = "implementation"
    TEST_DEVELOPMENT = "test_development"
    REVIEW = "review"
    PLAN = "plan"


@dataclass
class Counters:
    """Sliding-window counters over the tool call stream."""
    window_size: int = 20
    # Raw event buffers (bounded deques)
    successes: deque = field(default_factory=lambda: deque(maxlen=20))
    denials: deque = field(default_factory=lambda: deque(maxlen=20))
    timeouts: deque = field(default_factory=lambda: deque(maxlen=20))
    # Pattern tracking: (tool, arg_signature) -> recent count
    pattern_history: dict = field(default_factory=dict)
    pattern_outcomes: dict = field(default_factory=dict)
    # Scope
    tokens_used: int = 0
    token_limit: int = 200_000

    def record(self, event: dict):
        """Record a tool call event and update all counters."""
        success = event.get("success", True)
        self.successes.append(success)

        is_denial = not success and any(
            kw in event.get("result", "").lower()
            for kw in ["permission denied", "not permitted", "eacces", "access denied"]
        )
        self.denials.append(is_denial)

        is_timeout = not success and event.get("duration_ms", 0) > 30_000
        self.timeouts.append(is_timeout)

        # Track repeated patterns
        sig = (event.get("tool", ""), _arg_signature(event.get("arguments", {})))
        self.pattern_history[sig] = self.pattern_history.get(sig, 0) + 1
        outcome = event.get("result", "")[:200]
        prev_outcome = self.pattern_outcomes.get(sig)
        self.pattern_outcomes[sig] = outcome

        self.tokens_used = event.get("cumulative_tokens", self.tokens_used)

        return sig, prev_outcome, outcome

    @property
    def success_rate(self) -> float:
        if not self.successes:
            return 1.0
        return sum(self.successes) / len(self.successes)

    @property
    def denial_rate(self) -> float:
        if not self.denials:
            return 0.0
        return sum(self.denials) / len(self.denials)

    @property
    def timeout_count(self) -> int:
        return sum(self.timeouts)

    @property
    def scope_utilization(self) -> float:
        if self.token_limit == 0:
            return 0.0
        return self.tokens_used / self.token_limit


def _arg_signature(args: dict) -> str:
    """Produce a structural signature from arguments (keys only)."""
    if isinstance(args, dict):
        return ",".join(sorted(args.keys()))
    return str(type(args).__name__)


# ----- Thresholds -----

DENIAL_RATE_THRESHOLD = 0.30      # 30% denials -> tighten
DENIAL_COUNT_THRESHOLD = 15       # 15 denials in window -> tighten
SUCCESS_RATE_THRESHOLD = 0.50     # below 50% -> suggest compaction
REPEAT_THRESHOLD = 3              # 3 repeats with same outcome -> re-plan
TIMEOUT_THRESHOLD = 3             # 3 timeouts in window -> mode mismatch
SCOPE_THRESHOLD = 0.80            # 80% context used -> compaction
SUCCESS_STREAK_THRESHOLD = 30     # 30 successes -> suggest loosening


@dataclass
class Transition:
    """A recommended mode transition."""
    turn: int
    from_mode: Mode
    to_mode: Mode
    reason: str
    automatic: bool  # True = safe to automate, False = needs human approval

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "from": self.from_mode.value,
            "to": self.to_mode.value,
            "reason": self.reason,
            "automatic": self.automatic,
        }


def evaluate(
    counters: Counters,
    current_mode: Mode,
    turn: int,
    sig: tuple,
    prev_outcome: Optional[str],
    outcome: str,
) -> list[Transition]:
    """Evaluate counters against thresholds. Return any triggered transitions."""
    transitions = []

    # --- Automatic tightening ---

    # Test failure in implementation -> debug
    if current_mode == Mode.IMPLEMENTATION and not counters.successes[-1]:
        if "test" in outcome.lower() or "assert" in outcome.lower():
            transitions.append(Transition(
                turn=turn,
                from_mode=current_mode,
                to_mode=Mode.DEBUG,
                reason=f"Test failure detected in implementation mode",
                automatic=True,
            ))

    # High denial rate -> tighten
    if (counters.denial_rate >= DENIAL_RATE_THRESHOLD
            and sum(counters.denials) >= DENIAL_COUNT_THRESHOLD):
        tighter = {
            Mode.IMPLEMENTATION: Mode.PLAN,
            Mode.DEBUG: Mode.PLAN,
            Mode.TEST_DEVELOPMENT: Mode.PLAN,
        }.get(current_mode)
        if tighter:
            transitions.append(Transition(
                turn=turn,
                from_mode=current_mode,
                to_mode=tighter,
                reason=(f"Denial rate {counters.denial_rate:.0%} with "
                        f"{sum(counters.denials)} denials in window"),
                automatic=True,
            ))

    # Repeated loop -> force re-plan
    if (counters.pattern_history.get(sig, 0) >= REPEAT_THRESHOLD
            and prev_outcome is not None
            and prev_outcome[:100] == outcome[:100]):
        transitions.append(Transition(
            turn=turn,
            from_mode=current_mode,
            to_mode=Mode.PLAN,
            reason=(f"Pattern {sig[0]}({sig[1]}) repeated "
                    f"{counters.pattern_history[sig]}x with no progress"),
            automatic=True,
        ))

    # Timeout spike -> flag mode mismatch
    if counters.timeout_count >= TIMEOUT_THRESHOLD:
        transitions.append(Transition(
            turn=turn,
            from_mode=current_mode,
            to_mode=Mode.PLAN,
            reason=f"{counters.timeout_count} timeouts in window — wrong tools for this task",
            automatic=True,
        ))

    # Scope exhaustion -> compaction
    if counters.scope_utilization >= SCOPE_THRESHOLD:
        transitions.append(Transition(
            turn=turn,
            from_mode=current_mode,
            to_mode=Mode.PLAN,
            reason=f"Context {counters.scope_utilization:.0%} consumed — needs compaction",
            automatic=True,
        ))

    # --- Recommendations (need human approval) ---

    # Success rate decay -> suggest compaction
    if (len(counters.successes) >= 10
            and counters.success_rate < SUCCESS_RATE_THRESHOLD
            and turn > 20):
        transitions.append(Transition(
            turn=turn,
            from_mode=current_mode,
            to_mode=current_mode,  # same mode, but compacted
            reason=(f"Success rate {counters.success_rate:.0%} over "
                    f"last {len(counters.successes)} turns — consider compaction"),
            automatic=False,
        ))

    # Sustained success -> suggest loosening
    recent_successes = list(counters.successes)
    if (len(recent_successes) >= SUCCESS_STREAK_THRESHOLD
            and all(recent_successes[-SUCCESS_STREAK_THRESHOLD:])):
        transitions.append(Transition(
            turn=turn,
            from_mode=current_mode,
            to_mode=current_mode,
            reason=(f"Last {SUCCESS_STREAK_THRESHOLD} calls succeeded — "
                    f"consider enabling auto-accept"),
            automatic=False,
        ))

    return transitions


def run(log_path: str):
    """Process a conversation log and report transitions."""
    counters = Counters()
    current_mode = Mode.IMPLEMENTATION  # sensible default
    all_transitions = []

    with open(log_path) as f:
        for turn, line in enumerate(f, 1):
            try:
                event = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            sig, prev_outcome, outcome = counters.record(event)
            transitions = evaluate(
                counters, current_mode, turn, sig, prev_outcome, outcome
            )

            for t in transitions:
                all_transitions.append(t)
                if t.automatic:
                    current_mode = t.to_mode

    # Output
    print(json.dumps({
        "log": log_path,
        "total_turns": turn,
        "final_mode": current_mode.value,
        "counters": {
            "success_rate": round(counters.success_rate, 3),
            "denial_rate": round(counters.denial_rate, 3),
            "timeout_count": counters.timeout_count,
            "scope_utilization": round(counters.scope_utilization, 3),
        },
        "transitions": [t.to_dict() for t in all_transitions],
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <conversation.jsonl>", file=sys.stderr)
        sys.exit(1)
    run(sys.argv[1])
```

The controller is ~150 lines. It has no dependencies beyond the standard library. It reads JSONL, tracks counters, applies thresholds, and outputs structured JSON.

Run it against your conversation logs. The output tells you:

- What mode the controller would have been in at each point in the conversation.
- Which transitions it would have triggered, and why.
- Which transitions it would have *recommended* but left to you.

Tune the thresholds to your workflow. The defaults above are starting points — derived from the theory, not from empirical data. Your actual failure patterns will tell you where to set them.

The important thing is not the specific numbers. It's the architecture: counters, thresholds, if/then rules. No LLM in the control loop.

---

## What this buys you

### The controller catches spirals early

Without a controller, spiral detection is manual. You watch the output, notice the agent is looping, and intervene. With a controller, the loop is detected at repetition three. The agent gets forced into a re-plan before it burns another fifty turns on the same dead end.

### The controller enforces the test boundary

Without modes, the agent can edit tests and implementation in the same turn. It will, when that's the shortest path to "tests pass." With modes, the controller ensures that implementation mode keeps tests read-only. The boundary is structural, not behavioral — it doesn't depend on the agent choosing to respect it.

### The controller makes compaction timely

Without scope monitoring, you discover context exhaustion when the agent's output quality drops off a cliff. With the controller, compaction triggers at 80% — before the degradation starts, not after.

### The controller documents its decisions

Every transition is a structured record: which turn, which counters, which thresholds, which mode change. You can review the controller's decisions after the session. You can tune the thresholds based on whether its interventions were timely or premature. The controller is as auditable as the tools it manages.

---

## The controller stays specified

Here is the design constraint that matters more than any specific threshold or transition rule.

If you need trained judgment to decide whether to switch modes, your modes are wrong. The boundaries between modes should be sharp enough that a counter can detect when you've crossed one. Test failure is binary — exit code zero or not. Denial rate is arithmetic — count over window. Loop detection is pattern matching — same signature, same outcome, N times.

The monitoring is counters and thresholds. The transitions are if/then rules. The audit trail is structured JSON. No LLM in the control loop.

This is not a limitation. It's the point. The controller manages a system that contains trained judgment (the agent). The controller itself must be simpler than the system it manages. If the controller requires the same kind of reasoning as the agent, you haven't built a controller — you've built another agent, and now you need a controller for the controller.

Counters. Thresholds. Rules. That's the whole thing.

---

*Previously: [Where the Failures Live](03-where-the-failures-live.md)*
*Next: [Closing the Channel](05-closing-the-channel.md)*
*For the full treatment: [Coordination Is Not Control](../ma/coordination-is-not-control.md)*
