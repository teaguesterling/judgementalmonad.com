# Experimental Task Suite

*Shared task suite for Experiments 3 (phase transition), 6 (trust gap), and 11 (autonomy placement). Designed for reuse across all controlled experiments.*

---

## Design requirements

From the statistical designs:
- 30-50 tasks minimum
- Each task must have two natural phases (understanding/planning, then implementation)
- Planning quality must matter (wrong approach = wasted effort)
- Tasks must have clear correctness criteria (tests pass, code compiles, behavior correct)
- Moderate difficulty (completable in ~30 minutes)
- Tagged with: `needs-bash` (yes/no), `planning-matters` (low/medium/high), `expected-failure-modes`

---

## Part 1: Concrete tasks from user repos (15 tasks)

### Task 1: Performance Test Optimization

- **Repo:** sitting_duck
- **Description:** Performance test suite (`performance_tests.test`) takes 26 seconds. Refactor to optimize without losing coverage. Current test creates 10,000-node synthetic AST with 9 complex queries.
- **Planning phase:** Identify which queries are expensive. Decide whether to reduce test data, split into tiered suites, or optimize specific queries.
- **Success criterion:** Tests pass in <5 seconds, or split into tiered suite (quick: <1s, full: <30s). All queries still exercised.
- **Quality criterion:** Solution addresses the actual bottleneck, not a guess. Tiering decision is well-justified.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [misidentified bottleneck, premature optimization, lost coverage]

### Task 2: Update duckdb_ast.test Schema Assertions

- **Repo:** sitting_duck
- **Description:** Main test file needs column name updates after unified backend refactor. `source_text` → `peek`, plus new columns: `kind`, `universal_flags`, `semantic_id`, `super_type`, `arity_bin`. ~150 assertions to update.
- **Planning phase:** Understand new schema structure. Map old columns to new. Determine which new columns are required vs optional.
- **Success criterion:** All ~150 assertions pass. All language-specific parsing tests still work.
- **Quality criterion:** Mapping is complete and consistent. No assertions blindly updated without understanding the semantics.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [incomplete schema mapping, data type mismatches, cascading test failures]

### Task 3: Implement ast_find_references() Phase 1

- **Repo:** sitting_duck (feature #016)
- **Description:** Implement simple text matching for ast_find_references(). SQL function takes parsed AST, target name, optional scope_id. Returns all matching identifier/variable_reference/function_call nodes.
- **Planning phase:** Choose between direct array traversal vs recursive macros. Understand scope semantics for language-specific rules. Design API signature.
- **Success criterion:** Function returns correct references for Python/JS/C/Rust. Scope filtering works. No false positives from unrelated identifiers.
- **Quality criterion:** Handles name shadowing correctly. Cross-language semantics documented. Edge cases identified.
- **Difficulty:** Hard
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [false negatives, scope leakage, name shadowing, cross-language inconsistency]

### Task 4: Cross-Language Semantic Type Audit

- **Repo:** sitting_duck
- **Description:** Audit all language semantic type mappings to ensure punctuation gets consistent types across languages. Currently Python uses PARSER_DELIMITER but JavaScript uses PARSER_PUNCTUATION for same characters.
- **Planning phase:** Establish categorization rules (DELIMITER vs PUNCTUATION). Plan audit across all 10+ language adapters.
- **Success criterion:** All languages use same semantic type for equivalent punctuation. Audit document produced. Validation test written.
- **Quality criterion:** Categorization rules are principled, not ad hoc. Complete coverage of all languages.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:medium, expected-failure-modes: [incomplete audit, missed languages, regression in language-specific tests]

### Task 5: Fix Missing Interaction Prompt UI

- **Repo:** pajama_man (bug #033)
- **Description:** Player approaches bed in WakingWorld_Bedroom, debug shows "Near: Bed" but no UI prompt appears. Either UI component missing, events not wired, or TMP font missing.
- **Planning phase:** Trace interaction system: proximity detection → UI listening. Diagnose which layer is broken. Multiple possible causes.
- **Success criterion:** "Press A to Sleep" prompt appears within 2m of bed, disappears when moving away. Works in editor and standalone build.
- **Quality criterion:** Root cause correctly identified on first attempt. Fix addresses cause, not symptom.
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [wrong diagnosis, missing component, event wiring, font asset issue]

### Task 6: Adjust Player Camera Height

- **Repo:** pajama_man (bug #034)
- **Description:** First-person camera at adult height (~1.7 units). Adjust to child eye level (~1.0-1.2 units) for correct furniture proportions.
- **Planning phase:** Find camera configuration (prefab vs script). Measure current height. Research child eye level.
- **Success criterion:** Bed appears at chest/waist height. Room feels like child's perspective. No regression in movement/collision.
- **Quality criterion:** Height is grounded in reference data, not a guess.
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:low, expected-failure-modes: [camera config not found, incorrect height]

### Task 7: Implement Scene Management Architecture

- **Repo:** pajama_man (feature P1-001)
- **Description:** Build Boot scene with persistent GameManager. Implement SceneLoader service for async additive scene loading. Foundation for all world transitions.
- **Planning phase:** Understand DontDestroyOnLoad semantics. Design API (LoadAsync, UnloadAsync, SwapAsync). Plan service lifecycle.
- **Success criterion:** Boot scene loads as index 0. SceneLoader additively loads/unloads scenes. InputManager survives transitions. PlayMode tests pass.
- **Quality criterion:** API design is clean and anticipates future scene types. Error handling for missing scenes.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [scene state leakage, async timing bugs, premature unload, InputManager not found]

### Task 8: Implement 3D Waking World Prototype

- **Repo:** pajama_man (feature P1-002)
- **Description:** Build greybox bedroom scene loaded additively. Camera-relative movement (CharacterController + Cinemachine), minimal interaction system with bed trigger.
- **Planning phase:** Integrate P1-001 scene loader. Design Cinemachine setup. Plan interaction system API.
- **Success criterion:** Player moves with left stick (camera-relative), camera orbits with right stick. Interaction prompt near bed. Scene loads/unloads cleanly.
- **Quality criterion:** Movement feels responsive. Camera doesn't clip. Interaction system is extensible.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [camera clipping, jerky movement, Cinemachine setup, interaction detection radius]

### Task 9: Implement Git URL Parser

- **Repo:** duck_tails (Phase 1 feature)
- **Description:** Parse `git://path/to/file@revision` syntax. Extract repo path, file path, and git ref. Support branches, tags, commit hashes, ranges.
- **Planning phase:** Design parser state machine. Understand git ref syntax edge cases (v1.0 vs v1.0.0, HEAD~1, etc).
- **Success criterion:** Parser handles relative/absolute paths, multiple ref types, special paths. Structured result with repo, file, ref. Error messages for malformed URLs.
- **Quality criterion:** Edge cases handled. Parser is robust to adversarial input.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:medium, expected-failure-modes: [incomplete ref syntax, path ambiguity, Windows path handling]

### Task 10: Implement TextDiff Type Conversion

- **Repo:** duck_tails (Phase 2 feature)
- **Description:** Bidirectional TextDiff ↔ DiffInfo conversion. Parse git diff text into structured format, export back to git-compatible patch.
- **Planning phase:** Understand git diff format spec. Design truncation/rounding strategies. Plan roundtrip validation.
- **Success criterion:** textdiff_from_string() parses git diff. textdiff_to_diffinfo() extracts hunks. diffinfo_to_textdiff() generates valid patch. Roundtrip tests pass.
- **Quality criterion:** Binary files handled. Context lines correct. Roundtrip is lossless for standard diffs.
- **Difficulty:** Hard
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [hunk boundary errors, binary file handling, context line mismatch]

### Task 11: Add Format Auto-Detection

- **Repo:** duck_hunt
- **Description:** Enhance parse_duck_hunt_log() to auto-detect log format when format='auto'. Currently requires explicit format string. Support 50+ tool output formats.
- **Planning phase:** Analyze log samples for distinguishing patterns. Design heuristic chain (magic bytes, regex, structural patterns).
- **Success criterion:** Auto-detection works for 90%+ of common tools (Make, GCC, Cargo, pytest, etc). Falls back gracefully with confidence score.
- **Quality criterion:** Heuristics are principled. False positive rate documented. Performance acceptable on large files.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:medium, expected-failure-modes: [false positives, ambiguous logs, performance regression]

### Task 12: Implement Severity Threshold Filtering

- **Repo:** duck_hunt
- **Description:** Add severity_threshold parameter to filter by minimum level. Parse log severity, implement filtering across all tool format parsers.
- **Planning phase:** Audit all 106 format parsers for consistent severity mapping. Decide semantics (>= threshold vs exact). Plan migration.
- **Success criterion:** Severity filtering works across all tools. Threshold semantics consistent. No performance regression.
- **Quality criterion:** Complete audit trail. Consistent severity mapping documented.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [inconsistent severity mapping, edge cases at boundaries, missed parsers]

### Task 13: Implement Extension Configuration Schema

- **Repo:** plinking_duck
- **Description:** Design and implement metadata schema for DuckDB extensions (name, version, author, dependencies, capabilities). C++ interface with SQL exposure.
- **Planning phase:** Understand DuckDB extension lifecycle. Design schema that scales to multiple extension types. Plan dependency resolution.
- **Success criterion:** Schema supports name, version, author, dependencies, function/type lists. Accessible via SQL metadata functions. Tests document schema.
- **Quality criterion:** Schema is extensible. Dependency cycles detected. Version constraints handled.
- **Difficulty:** Hard
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [circular dependencies, schema version conflicts, insufficient expressiveness]

### Task 14: Implement Parse-Time Filtering

- **Repo:** sitting_duck (feature #014)
- **Description:** Add filtering to read_ast_objects() to reduce memory. Support only_types param with patterns and presets (definitions, signatures, imports, structure).
- **Planning phase:** Understand tree-sitter traversal. Decide when/how to skip nodes. Design preset system.
- **Success criterion:** read_ast_objects(..., only_types=['function_definition']) loads ~2K nodes vs 50K full parse. Presets work across languages.
- **Quality criterion:** No structural gaps. Skipped nodes don't break parent references. Performance improvement measured.
- **Difficulty:** Hard
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [structural gaps, missing parent nodes, traversal correctness, language preset incompleteness]

### Task 15: Implement ast_get_source()

- **Repo:** sitting_duck (feature #013)
- **Description:** Extract original source code fragment for any AST node using line/column ranges. Support context lines, dedenting, language-specific formatting.
- **Planning phase:** Understand source location tracking in tree-sitter. Handle edge cases (tabs vs spaces, Unicode, multi-line).
- **Success criterion:** ast_get_source(node) returns correct substring. Context lines work. All languages supported.
- **Quality criterion:** Off-by-one errors eliminated. Unicode handling verified. Dedenting is correct.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [off-by-one in offsets, Unicode width, context line miscounting, tab/space confusion]

---

## Part 1b: Additional concrete tasks (Tasks 16-35)

*Tasks from repos explored in the second pass (BLQ, Jetsam, Fledgling) plus template instantiations against all repos.*

### Task 16: Implement Hard Sync (Incremental Copy)

- **Repo:** blq (lq)
- **Description:** The `_hard_sync()` function in `sync_cmd.py` is a stub that prints an error and exits. Implement incremental file copy — track file hashes, copy only new/changed log files to the destination.
- **Planning phase:** Understand the sync architecture (soft symlink vs hard copy). Study the existing `_soft_sync()` implementation. Design incremental tracking.
- **Success criterion:** `blq sync --hard` copies logs to destination incrementally. Respects `--force` flag. Existing soft sync still works.
- **Quality criterion:** Incremental tracking is efficient (hash-based, not full-file comparison). Edge cases handled (missing dest, partial copy recovery).
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [wrong sync model, incomplete incremental tracking, force flag not respected]

### Task 17: Upgrade to UUIDv7

- **Repo:** blq (lq)
- **Description:** Replace `uuid.uuid4()` with UUIDv7 in `bird.py:generate_id()`. UUIDv7 is time-ordered, which improves database performance for time-series data.
- **Planning phase:** Check Python 3.10 UUIDv7 support. Evaluate uuid7 backport package. Check if any code depends on UUID format.
- **Success criterion:** New invocations produce UUIDv7 IDs. IDs are time-ordered. Backward compatible with existing v4 IDs in database.
- **Quality criterion:** Library choice is justified. Migration path documented if existing IDs need updating.
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:low, expected-failure-modes: [library not available, format incompatibility]

### Task 18: Add Structured Logging to Jetsam

- **Repo:** jetsam
- **Description:** Add Python logging module to 8 core modules (git/wrapper.py, core/state.py, core/executor.py, core/planner.py, core/plans.py, platforms/*.py, config/manager.py). Add `--verbose` CLI flag. Configure MCP server logging.
- **Planning phase:** Audit current echo/print usage across modules. Design log level strategy. Plan CLI integration.
- **Success criterion:** All 8 modules use logging. `jetsam -v status` shows debug output. MCP server uses WARNING by default. JETSAM_LOG_LEVEL env var works.
- **Quality criterion:** Log format includes module name and level. No stdout pollution in MCP mode. Acceptance criteria from P8-003 task doc all met.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [stdout pollution in MCP, inconsistent log levels, missing modules]

### Task 19: Add Return Type Annotations to sitting_duck SQL Macros

- **Repo:** sitting_duck
- **Description:** Many SQL macros in the macro registry lack explicit return type annotations. Add them based on the actual return types (inferred from implementation).
- **Planning phase:** Audit all macro definitions. Categorize return types (TABLE, VARCHAR, INTEGER, BOOLEAN, etc.). Identify any macros where return type is ambiguous.
- **Success criterion:** All macros have explicit return type annotations. No type mismatches.
- **Quality criterion:** Annotations are precise (not just VARCHAR everywhere). Ambiguous cases documented.
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:low, expected-failure-modes: [type mismatches, ambiguous returns]

### Task 20: Refactor duck_tails Git URL Parser Error Handling

- **Repo:** duck_tails
- **Description:** The git URL parser returns None on parse failure with no error context. Refactor to return structured error objects with failure reason, position, and suggestion.
- **Planning phase:** Identify all parse failure paths. Categorize error types (malformed URL, invalid ref, ambiguous path). Design error structure.
- **Success criterion:** All parse failures return structured errors. Error messages are actionable. Existing success paths unchanged.
- **Quality criterion:** Error messages help the user fix the URL. Position information points to the problem. No silent failures remain.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [missed failure paths, wrong position info, breaking existing callers]

### Task 21: Add Missing Docstrings to duck_hunt Format Parsers

- **Repo:** duck_hunt
- **Description:** Many of the 106 format parsers lack docstrings. Add docstrings that describe: what log format the parser handles, what fields it extracts, and any known limitations.
- **Planning phase:** Sample 10-15 parsers to understand the pattern. Design a docstring template. Identify parsers that need non-obvious documentation.
- **Success criterion:** All 106 parsers have docstrings. Template is consistent. Known limitations documented.
- **Quality criterion:** Docstrings are actually useful (not just "parses X logs"). Limitations are honest.
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:low, expected-failure-modes: [inconsistent template, missed parsers, generic unhelpful docstrings]

### Task 22: Implement Config Validation for Jetsam

- **Repo:** jetsam
- **Description:** Jetsam loads configuration from files but doesn't validate the schema. Add validation that catches: missing required fields, invalid types, unknown keys, conflicting settings.
- **Planning phase:** Read existing config loading code. Enumerate all valid config fields and their types. Design validation approach (pydantic, manual, jsonschema).
- **Success criterion:** Invalid configs produce clear error messages. All valid configs still load. Unknown keys warned about.
- **Quality criterion:** Error messages point to the specific problem. Validation runs at load time, not at use time.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [over-strict validation breaking existing configs, incomplete field enumeration, wrong type constraints]

### Task 23: Extract Common Patterns from sitting_duck Language Adapters

- **Repo:** sitting_duck
- **Description:** Multiple language adapters (Python, JavaScript, Rust, C, Go) share similar logic for mapping AST node types to semantic categories. Extract the shared logic into a base adapter.
- **Planning phase:** Compare 3-4 language adapters to identify shared patterns. Design the base adapter interface. Plan migration order.
- **Success criterion:** Base adapter exists. At least 2 language adapters refactored to use it. All existing tests pass.
- **Quality criterion:** The base adapter captures the right abstraction level — not too generic (useless) or too specific (doesn't generalize).
- **Difficulty:** Hard
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [wrong abstraction level, breaking language-specific behavior, incomplete migration]

### Task 24: Add Input Validation to BLQ MCP Server Tools

- **Repo:** blq (lq)
- **Description:** The MCP server tools accept user input but don't validate it thoroughly. Add input validation for path arguments (prevent traversal), query arguments (prevent injection), and numeric arguments (range checks).
- **Planning phase:** Audit all MCP tool input parameters. Categorize by risk (path, query, numeric, string). Design validation strategy.
- **Success criterion:** All path arguments are sanitized. Query arguments are parameterized. Numeric arguments have range checks. Invalid input produces helpful errors.
- **Quality criterion:** Validation is defense-in-depth (not just first line). Error messages are actionable without leaking internal paths.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [over-strict validation breaking valid inputs, missed input parameters, leaking paths in errors]

### Task 25: Implement Diff Statistics Summary for duck_tails

- **Repo:** duck_tails
- **Description:** Add a `diff_stats()` SQL macro that summarizes a TextDiff: files changed, lines added/removed, largest hunks, binary files detected. Returns a structured summary table.
- **Planning phase:** Understand the TextDiff data structure. Design the summary schema. Handle edge cases (binary files, empty diffs, renames).
- **Success criterion:** `diff_stats(diff)` returns correct counts for added/removed lines, file count, binary detection. Works on real git diffs.
- **Quality criterion:** Summary is useful for human review. Edge cases handled. Performance acceptable on large diffs.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [wrong line counts, binary detection failure, rename handling]

### Task 26: Fix Inconsistent Error Handling in Fledgling Tools

- **Repo:** source-sextant (Fledgling)
- **Description:** Some Fledgling MCP tools return error strings, others raise exceptions, others return None. Standardize to a consistent error handling pattern across all 11 tools.
- **Planning phase:** Audit all 11 tools for error handling patterns. Design a standard pattern (structured error return vs exception). Plan migration.
- **Success criterion:** All tools use the same error handling pattern. Error messages include context. No silent failures.
- **Quality criterion:** Pattern is appropriate for MCP (structured errors that clients can parse). Migration is complete.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [breaking callers, inconsistent migration, losing error context]

### Task 27: Add Progress Reporting to BLQ Sync Command

- **Repo:** blq (lq)
- **Description:** The sync command operates silently on large log directories. Add progress reporting: file count, bytes transferred, estimated time remaining.
- **Planning phase:** Understand the sync flow. Identify where to hook progress callbacks. Design the progress display (CLI spinner, percentage, or bar).
- **Success criterion:** Progress is displayed during sync. Total files and bytes shown at completion. Quiet mode (`-q`) suppresses output.
- **Quality criterion:** Progress doesn't slow down the operation. Display is clean and updates in-place.
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:low, expected-failure-modes: [progress slowing operation, display artifacts, quiet mode not working]

### Task 28: Write Test Suite for Jetsam Plan Executor

- **Repo:** jetsam
- **Description:** The plan executor (`core/executor.py`) has limited test coverage. Write comprehensive tests covering: successful plan execution, step failure and rollback, partial completion, concurrent plan prevention.
- **Planning phase:** Read the executor code. Identify the contract (what it promises). Enumerate edge cases and failure modes. Design test fixtures.
- **Success criterion:** Tests cover happy path, single-step failure, multi-step rollback, concurrent execution prevention. Coverage >80%.
- **Quality criterion:** Tests test the contract, not the implementation. Fixtures are realistic. Edge cases documented.
- **Difficulty:** Moderate
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [testing implementation not contract, missing edge cases, brittle fixtures]

### Task 29: Add Dead Code Detection Query to sitting_duck

- **Repo:** sitting_duck
- **Description:** Write a SQL macro `ast_find_dead_code(parsed_ast)` that identifies functions/methods defined but never called within the same file. Use the existing AST definition and call-site data.
- **Planning phase:** Understand the AST schema for definitions and calls. Design the join query. Handle edge cases (exports, dynamic calls, decorators).
- **Success criterion:** Query correctly identifies unused functions in Python and JavaScript. False positive rate documented.
- **Quality criterion:** Handles common false positive cases (exported functions, test helpers, __main__ guards). Performance acceptable on large files.
- **Difficulty:** Hard
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [false positives on exports, missing dynamic calls, cross-language inconsistency]

### Task 30: Implement Batch Import for duck_hunt Log Parsers

- **Repo:** duck_hunt
- **Description:** Currently each log file is parsed individually. Add a batch import function that processes a directory of log files with progress reporting and error recovery (skip failures, continue processing).
- **Planning phase:** Understand the parser dispatch mechanism. Design the batch interface (directory scan, format detection, parallel processing). Plan error recovery.
- **Success criterion:** `parse_duck_hunt_logs(directory)` processes all log files, reports progress, skips failures with warnings, returns summary.
- **Quality criterion:** Error recovery is graceful. Summary includes success/failure counts. Performance is reasonable on 100+ files.
- **Difficulty:** Moderate
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [parser dispatch errors, silent failures, memory issues on large batches]

### Task 31: Add Schema Migration Support to BLQ Database

- **Repo:** blq (lq)
- **Description:** BLQ stores run history in DuckDB but has no schema migration mechanism. When the schema changes, existing databases break. Add a migration system that detects schema version and applies incremental updates.
- **Planning phase:** Understand current schema. Design version tracking (metadata table). Plan migration execution (idempotent, ordered, transactional).
- **Success criterion:** Schema version is tracked. New schema changes are applied on startup. Old databases are migrated without data loss.
- **Quality criterion:** Migrations are idempotent. Rollback is possible. Version checking is fast.
- **Difficulty:** Hard
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [data loss during migration, non-idempotent migrations, version detection failure]

### Task 32: Add Color Theme Support to Jetsam CLI Output

- **Repo:** jetsam
- **Description:** Jetsam CLI uses hardcoded ANSI colors. Add theme support: detect terminal capabilities, support NO_COLOR env var, allow user theme configuration.
- **Planning phase:** Audit current color usage. Research terminal capability detection. Design theme system.
- **Success criterion:** NO_COLOR disables all colors. Terminal capability detection works. User can configure colors via config file.
- **Quality criterion:** Fallbacks are graceful. No broken output in non-color terminals.
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:low, expected-failure-modes: [broken output in some terminals, NO_COLOR not fully respected]

### Task 33: Optimize sitting_duck AST Parsing Memory Usage

- **Repo:** sitting_duck
- **Description:** Parsing large files (>10K nodes) uses significant memory because the entire AST is loaded into a DuckDB table. Profile memory usage and implement streaming or chunked processing for large files.
- **Planning phase:** Profile current memory usage on large files. Identify the bottleneck (tree-sitter allocation, DuckDB insertion, intermediate structures). Design optimization strategy.
- **Success criterion:** Memory usage reduced by >50% for files with >10K nodes. No correctness regression. Performance not degraded for small files.
- **Quality criterion:** Optimization addresses the actual bottleneck. Measurement methodology is sound.
- **Difficulty:** Hard
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [wrong bottleneck, optimization changes behavior, measurement error]

### Task 34: Add Retry Logic to Fledgling Git Operations

- **Repo:** source-sextant (Fledgling)
- **Description:** Fledgling's git operations (GitDiffSummary, etc.) can fail on locked repos or slow filesystems. Add retry logic with exponential backoff for transient git failures.
- **Planning phase:** Identify which git operations are failure-prone. Categorize failures as transient vs permanent. Design retry strategy.
- **Success criterion:** Transient failures are retried (up to 3 times with backoff). Permanent failures propagate immediately. Retries are logged.
- **Quality criterion:** Retry logic doesn't mask real errors. Backoff is appropriate (not too aggressive, not too slow).
- **Difficulty:** Easy
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [retrying permanent errors, too-aggressive backoff, masking real failures]

### Task 35: Implement Cross-File Reference Tracking in sitting_duck

- **Repo:** sitting_duck
- **Description:** sitting_duck can find definitions and calls within a single file. Extend to track cross-file references: imports map to definition files, calls map to imported definitions. Limited to Python initially.
- **Planning phase:** Understand Python import resolution. Design the cross-file index structure. Plan how to combine single-file ASTs into a cross-file view.
- **Success criterion:** Given a Python import, resolve to the file and definition. Given a function call, identify if the callee is imported and from where. Works for standard import patterns.
- **Quality criterion:** Handles relative imports, __init__.py, aliased imports. False positive rate documented.
- **Difficulty:** Hard
- **Tags:** needs-bash:no, planning-matters:high, expected-failure-modes: [relative import resolution, dynamic imports, circular dependencies, __init__ confusion]

---

## Part 2: Task templates (10 templates)

These can be instantiated against any repo to generate additional tasks.

### Template A: "Find the actual bottleneck"

- **Description:** A test suite or build process is slow. Find the actual bottleneck and fix it.
- **Instantiation:** Give the agent a repo with a slow test/build. Don't hint at the cause.
- **Planning phase:** Profile, measure, hypothesize. Wrong hypothesis = wasted optimization.
- **Success criterion:** Measurable speedup (>2x). The actual bottleneck addressed, not a guess.
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [premature optimization, wrong bottleneck, measurement error]
- **Experiment suitability:** 3 (computation channels needed for profiling), 11 (planning quality determines speedup)

### Template B: "Add a feature to an unfamiliar codebase"

- **Description:** Add a specified feature to a codebase the agent hasn't seen before.
- **Instantiation:** Pick a feature request from the repo's TODO/issue list. Give no codebase context.
- **Planning phase:** Understand architecture, find integration points, design the addition.
- **Success criterion:** Feature works. Tests pass. Integrates with existing patterns.
- **Tags:** needs-bash:varies, planning-matters:high, expected-failure-modes: [wrong integration point, pattern violation, missing edge cases]
- **Experiment suitability:** 11 (placement: broad planning tools help most), 3 (level 4 tools help explore faster)

### Template C: "Fix a bug from a symptom description"

- **Description:** Given only a symptom ("X doesn't work when Y"), find the root cause and fix it.
- **Instantiation:** Pick a known bug from a repo. Describe only the symptom, not the cause.
- **Planning phase:** Reproduce, hypothesize, trace. Wrong hypothesis = wasted debugging.
- **Success criterion:** Bug fixed. Root cause documented. Regression test added.
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [wrong diagnosis, symptom-level fix, missing regression test]
- **Experiment suitability:** 3 (debugging benefits from computation channels), 11 (planning quality critical for diagnosis)

### Template D: "Refactor without breaking"

- **Description:** Refactor a module to improve structure. All existing tests must pass.
- **Instantiation:** Pick a module with known structural issues (duplicated code, confusing API, poor naming).
- **Planning phase:** Understand the module's callers. Plan the refactor to maintain invariants.
- **Success criterion:** All existing tests pass. Code is measurably improved (fewer duplications, clearer API).
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [broken callers, lost semantics, incomplete rename, test update masking bug]
- **Experiment suitability:** 11 (understanding architecture before changing it), 3 (tests validate correctness at each step)

### Template E: "Write tests for untested code"

- **Description:** Given a module with no tests, write a comprehensive test suite.
- **Instantiation:** Pick a module with existing behavior but no test coverage.
- **Planning phase:** Understand the module's contract. Identify edge cases. Design test strategy.
- **Success criterion:** Tests cover happy path, edge cases, and error conditions. Coverage >80%.
- **Tags:** needs-bash:yes, planning-matters:medium, expected-failure-modes: [testing implementation not contract, missing edge cases, brittle tests]
- **Experiment suitability:** 6 (trust gap — does the test suite match behavioral expectations?), 11 (planning helps identify edge cases)

### Template F: "Migrate to a new API version"

- **Description:** A dependency updated its API. Migrate all call sites.
- **Instantiation:** Simulate or use an actual API change in a dependency.
- **Planning phase:** Understand the API changes. Plan migration order. Identify breaking changes.
- **Success criterion:** All call sites updated. Tests pass. No deprecated API usage remains.
- **Tags:** needs-bash:yes, planning-matters:medium, expected-failure-modes: [incomplete migration, behavioral change not caught, missing call sites]
- **Experiment suitability:** 3 (computation channels help find all call sites), 11 (planning prevents partial migration)

### Template G: "Implement a spec from documentation"

- **Description:** Given a specification document, implement it from scratch.
- **Instantiation:** Use an existing spec/design document from the repo.
- **Planning phase:** Read and understand the spec. Identify ambiguities. Design implementation approach.
- **Success criterion:** Implementation matches spec. All specified behaviors present. Ambiguities resolved correctly.
- **Tags:** needs-bash:varies, planning-matters:high, expected-failure-modes: [spec misinterpretation, missing edge cases, overengineering]
- **Experiment suitability:** 11 (front-loaded planning matches spec understanding), 3 (levels 0-2 sufficient for implementation)

### Template H: "Debug a flaky test"

- **Description:** A test passes most of the time but fails intermittently. Find and fix the flakiness.
- **Instantiation:** Pick or create a test with timing sensitivity, order dependence, or shared state.
- **Planning phase:** Reproduce the failure. Hypothesize causes (timing, ordering, shared state, environment).
- **Success criterion:** Test passes 100/100 consecutive runs. Root cause documented.
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [wrong diagnosis, masking instead of fixing, insufficient reproduction]
- **Experiment suitability:** 3 (repeated execution needs bash), 11 (diagnosis requires deep understanding)

### Template I: "Add error handling to a happy-path implementation"

- **Description:** A module handles the success case but crashes or returns garbage on errors.
- **Instantiation:** Pick a module that lacks error handling for network failures, malformed input, etc.
- **Planning phase:** Enumerate error cases. Decide error handling strategy (return errors, throw, default values).
- **Success criterion:** Module handles all identified error cases. Error messages are actionable. No silent failures.
- **Tags:** needs-bash:no, planning-matters:medium, expected-failure-modes: [missed error cases, too-broad exception handling, unclear error messages]
- **Experiment suitability:** 6 (trust gap — are errors handled or swallowed?), 11 (planning identifies error cases)

### Template J: "Optimize a data processing pipeline"

- **Description:** A data processing step is too slow for production use. Optimize without changing the output.
- **Instantiation:** Pick a pipeline step with measurable performance and clear output spec.
- **Planning phase:** Profile. Identify algorithmic vs implementation bottleneck. Choose optimization strategy.
- **Success criterion:** 3x+ speedup. Output unchanged (diff against baseline). No new failure modes.
- **Tags:** needs-bash:yes, planning-matters:high, expected-failure-modes: [wrong bottleneck, optimization changes output, regression on edge cases]
- **Experiment suitability:** 3 (profiling needs computation channels), 11 (planning quality determines which optimization to pursue)

---

## Part 3: Task suite statistics

### Current inventory

| Source | Count | Status |
|--------|-------|--------|
| Concrete tasks (Part 1) | 15 | Ready |
| Concrete tasks (Part 1b) | 20 | Ready |
| Instantiable templates | 10 | Available for expansion |
| **Total concrete** | **35** | **Meets 30-task minimum** |

### Difficulty distribution (all 35 tasks)

| Difficulty | Count | Target | Status |
|-----------|-------|--------|--------|
| Easy | 7 (17, 19, 21, 27, 32, 34, 6) | 5-8 | ✓ Met |
| Moderate | 19 (1, 2, 4, 7, 8, 9, 11, 12, 15, 16, 18, 20, 22, 24, 25, 26, 28, 30, task-10) | 15-25 | ✓ Met |
| Hard | 9 (3, 10, 13, 14, 23, 29, 31, 33, 35) | 5-10 | ✓ Met |

### Bash dependency distribution

| needs-bash | Count | Requirement |
|-----------|-------|-------------|
| No | **25** | ≥20 for Exp 3 Stratum 1 ✓ |
| Yes | **10** | Enough for Exp 3 Stratum 2 ✓ |

**Critical threshold met:** 25 `needs-bash: no` tasks exceeds the 20 minimum required for Stratum 1 of Experiment 3 to have adequate statistical power.

### Planning-matters distribution

| Level | Count |
|-------|-------|
| Low | 5 (17, 19, 21, 27, 32) |
| Medium | 12 (4, 9, 11, 15, 18, 20, 24, 25, 30, 34, 5, 6) |
| High | 18 (1, 2, 3, 7, 8, 10, 12, 13, 14, 16, 22, 23, 26, 28, 29, 31, 33, 35) |

Good distribution. 5 low-planning tasks serve as controls for Experiment 11.

### Repo coverage

| Repo | Tasks | Language |
|------|-------|----------|
| sitting_duck | 8 (1, 2, 3, 4, 14, 15, 19, 23, 29, 33, 35) | Python/SQL |
| pajama_man | 4 (5, 6, 7, 8) | C# (Unity) |
| duck_tails | 3 (9, 10, 20, 25) | Python |
| duck_hunt | 3 (11, 12, 21, 30) | Python |
| plinking_duck | 1 (13) | C++ |
| blq (lq) | 4 (16, 17, 24, 27, 31) | Python |
| jetsam | 3 (18, 22, 28, 32) | Python |
| source-sextant (Fledgling) | 2 (26, 34) | Python |

---

## Experiment-specific requirements

### For Experiment 3 (Phase Transition)

- Needs: 30 tasks, at least 20 `needs-bash: no` for Stratum 1
- **Status: MET.** 35 tasks total, 25 `needs-bash: no`
- Stratum 1 (no bash): 25 tasks — adequate power for co-primary tests
- Stratum 2 (needs bash): 10 tasks — adequate for B vs C comparison

### For Experiment 1 (Supermodularity)

- Needs: 30 tasks with per-task file lists for Low W conditions
- **Status: Tasks ready, file lists needed.** Each task needs a 3-5 file list specifying the relevant files. These should be created during Session 4 prep from the task descriptions and repo structure.

### For Experiment 6 (Trust Gap)

- Needs: 20-30 task types with bash patterns that are ratchet promotion candidates
- **Status: Partially ready.** Tasks 2, 4, 9, 10, 11, 12, 28, 33 involve bash patterns. Additional candidates will be identified from Experiment 3 run data.

### For Experiment 11 (Autonomy Placement)

- Needs: 30 tasks with two natural phases, `planning-matters: high`
- **Status: MET.** 18 tasks tagged `planning-matters: high`, plus 12 `medium` that are usable. Select 30 from the combined pool.

---

*The experimental infrastructure (MCP server, run script, condition configs) is in place. Tasks can be run using `experiments/tools/run-experiment.sh`.*
