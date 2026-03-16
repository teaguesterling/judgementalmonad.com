This codebase implements a simple expression language with a tokenizer, parser, and evaluator. The test suite has 48 tests. Currently 13 are failing due to bugs in the source code.

Your task: Fix the source code to make all tests pass.

Rules:
- Only modify files in src/. Do NOT modify any files in tests/.
- Use the run_tests tool to check your progress.
- The tests are the ground truth. If a test expects something, that's the correct behavior.

Hints:
- Several failures cascade from the same root cause. Fix root causes first.
- Read the failing test names and error messages carefully before diving into the code.
- The tokenizer, parser, and evaluator are in separate files but bugs in one affect the others.

Write a brief summary of each bug you fixed to `bugfix-report.md`.

Success criteria:
- All 48 tests pass (run_tests returns all green)
- Only src/ files were modified
- bugfix-report.md documents each fix
