# Plan: Structured Test Output Experiment

*Tests whether diagnostic-quality test output reduces the total cost of the debug cycle.*

---

## Motivation

The H5 experiment showed that test output quality matters more than bash availability. But H5 only varied *verbosity* (detailed tracebacks vs pass/fail counts). It didn't test whether a *structured diagnostic format* — designed for the agent's workflow — outperforms both.

Current test output formats are designed for humans:
- `pytest -v`: every test name + PASSED/FAILED (verbose, lots of noise)
- `pytest --tb=short -q`: progress dots + short tracebacks (compact but hard to parse)
- `pytest --tb=no -q`: just counts (minimal, forces investigation)

None of these are designed for an agent that needs to:
1. Identify which tests fail
2. Understand *why* each fails (expected vs actual, location in code)
3. Trace failures to root causes (which may be shared across tests)
4. Determine which failures are independent vs cascading

## The hypothesis

A structured diagnostic output format — similar to what blq does for build output and duck_hunt does for logs — will reduce the number of test-verify cycles and total cost.

**Predicted format:**
```
FAILURES (13/48):

  [Root cause group 1: String quoting — 7 tests]
  test_string_value_excludes_quotes (test_tokenizer.py:23)
    expected: 'hello'
    actual:   '"hello"'
    → String values include surrounding quotes

  test_single_quoted_string (test_tokenizer.py:29)
    expected: 'world'
    actual:   "'world'"
    → Same root cause

  test_string_concatenation (test_evaluator.py:70)
    expected: 'hello world'
    actual:   '"hello"" ""world"'
    → Cascades from tokenizer string quoting

  ... (4 more tests in this group)

  [Root cause group 2: Dict attribute access — 1 test]
  test_dict_dot_access (test_evaluator.py:213)
    AttributeError: 'dict' object has no attribute 'name'
    at src/evaluator.py:153: return getattr(o, name)
    → Dict dot access uses getattr instead of dict lookup

  [Root cause group 3: ...]

PASSED: 35/48
```

Key features:
- **Failure grouping**: Tests that share a root cause are grouped together
- **Expected vs actual**: For assertion failures, show both values
- **Source location**: Where in the source code the failure occurs
- **Cascade annotation**: Which failures are consequences of other failures
- **No noise**: No progress dots, no passing test details, no pytest header

## Connection to existing tools

| Tool | What it structures | For whom |
|------|-------------------|----------|
| **blq** | Build output (compiler errors, warnings) | Agent debugging build failures |
| **duck_hunt** | 50+ log formats | Agent analyzing logs |
| **This tool** | Test output (pytest, unittest, etc.) | Agent debugging test failures |
| **sitting_duck** | AST structure | Agent navigating code |

All follow the same pattern: take high-cardinality human-readable output, parse it into structured diagnostic-quality data, and present it through a data channel interface. This is the ratchet applied to tool output: raw output (level 4 via bash) → structured output (level 1 via MCP tool).

## Experiment design

### Independent variable

Three `run_tests` output formats:

| Format | What the agent sees | Level |
|--------|-------------------|-------|
| **raw** | Full pytest -v output (what bash gives) | Unstructured |
| **compact** | pytest --tb=short -q (current run_tests default) | Semi-structured |
| **diagnostic** | Grouped failures with root cause hints | Fully structured |

### What to measure

- Number of run_tests/pytest calls per task (fewer = better diagnosis per call)
- Total cost per task
- Time to first correct fix
- Whether the agent identifies root causes vs symptoms

### Prediction

- **diagnostic** format: 1-2 test calls per task (diagnose all bugs from first call)
- **compact** format: 2-3 test calls (current A behavior)
- **raw** format: 2-3 test calls (current D behavior, more data but same call count)
- diagnostic < compact ≈ raw on total cost

### Implementation

The diagnostic format requires parsing pytest output into structured failures. This is duck_hunt's problem applied to pytest. Options:

1. **Post-process pytest JSON output**: `pytest --json-report` plugin gives structured data. Parse and format.
2. **Custom pytest plugin**: A plugin that groups failures by source location and detects cascading failures.
3. **duck_hunt integration**: Add pytest as a duck_hunt log format. Use duck_hunt's parsing infrastructure.

Option 3 is the most aligned with the existing tool ecosystem and validates duck_hunt's generalization claim.

### Connection to the ratchet

This experiment is itself a ratchet turn:
1. **Discovery**: H5 and A-vs-D showed that test output quality matters but current formats aren't optimized for agents
2. **Observation**: Agents parse test output to extract failure locations and expected-vs-actual values. They do this manually every time.
3. **Crystallization**: Build a tool that does the parsing once and returns diagnostic-quality structured output
4. **Measurement**: Does the crystallized tool reduce the debug cycle cost?

## Dependencies

- Requires the current experiment batch (A through I) to complete first
- Should use the same synthetic codebase for comparison
- The diagnostic format design should be informed by analyzing *what information the agent actually extracts* from test output in the current runs
- duck_hunt integration is a bonus but not required for the experiment

## Priority

After the current batch completes and results are analyzed. This is the third ratchet turn:
1. First turn: file_read_batch, file_edit_batch (tool granularity)
2. Second turn: strategy instructions (cognitive pattern)
3. Third turn: structured diagnostic output (information quality)

Each turn addresses a different source of overhead discovered in the previous round.
