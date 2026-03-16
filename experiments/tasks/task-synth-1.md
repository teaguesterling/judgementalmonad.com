This codebase implements a configuration file parser with validation and merging. There are several bugs marked in the code and tests.

Your task: Find and fix ALL bugs in the codebase. The bugs are in three files:
- src/parser.py
- src/validator.py
- src/merger.py

The test files (tests/test_*.py) document the expected behavior. Some tests currently assert the BUGGY behavior with comments explaining what the correct behavior should be.

For each bug you fix:
1. Fix the code
2. Update the corresponding test to assert the CORRECT behavior (remove the "documenting the bug" assertions and uncomment or write the correct ones)

Write a summary to `bugfix-report.md` with:
- Each bug found: file, line, description
- The fix applied
- Which test validates the fix

Success criteria:
- All bugs are fixed (there are at least 5)
- All tests assert correct behavior (no "documenting the bug" assertions remain)
- bugfix-report.md contains the full list
- No new bugs introduced
