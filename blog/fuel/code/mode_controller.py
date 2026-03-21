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