This codebase implements a simple expression language with a tokenizer, parser, and evaluator. The test suite is failing.

Your task: Fix the source code to make all tests pass.

## Strategy

Work in four phases:

**Phase 1 — Gather.** Read all source files and test files in one batch. Use file_glob to find them, then file_read_batch to read them all at once. Also run run_tests to see which tests fail and what the errors are. Do all of this before making any changes.

**Phase 2 — Diagnose.** Before editing anything, identify ALL bugs. Look at every failing test, trace the failure to its root cause in the source code, and note whether bugs are related (one root cause may explain multiple test failures). Write out your full diagnosis before proceeding.

**Phase 3 — Fix.** Apply all fixes. Use file_edit_batch to make multiple edits to the same file in one call. Fix all bugs in a file at once rather than one at a time.

**Phase 4 — Verify.** Run run_tests once to confirm all tests pass. If any still fail, diagnose and fix in another batch.

## Rules

- Only modify files in src/. Do NOT modify any files in tests/.
- Use the run_tests tool to check your progress.
- The tests are the ground truth. If a test expects something, that's the correct behavior.

Write a brief summary of each bug you fixed to `bugfix-report.md`.

Success criteria:
- All tests pass (run_tests returns all green)
- Only src/ files were modified
- bugfix-report.md documents each fix
