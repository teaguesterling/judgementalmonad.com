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
| Concrete tasks from user repos | 15 | Ready |
| Instantiable templates | 10 | Need instantiation |

### What's needed to reach 30-50

- **Instantiate 5-10 templates** against the user's repos: Each template can produce 2-3 concrete tasks by applying it to different repos/modules. Estimated yield: 10-30 additional tasks.
- **SWE-bench Lite tasks:** 5-10 tasks from the public SWE-bench Lite dataset would add standardized, well-characterized tasks with known difficulty levels.
- **Synthetic tasks:** 5 tasks designed for specific properties:
  - A task where planning *doesn't* matter (pure execution, obvious approach) — control for Exp 11
  - A task where planning *especially* matters (three plausible approaches, only one works)
  - A task that requires no bash at all (pure read/edit) — control for Exp 3
  - A task that *requires* bash (must run tests to verify) — ensures Exp 3 condition differences are meaningful
  - A task with a planted anti-pattern (natural first approach fails) — for Exp 8

### Difficulty distribution (current 15)

| Difficulty | Count | Target |
|-----------|-------|--------|
| Easy | 2 | 5-8 |
| Moderate | 9 | 15-25 |
| Hard | 4 | 10-15 |

Need more easy tasks. Templates E, F, and I naturally produce easy-moderate tasks when instantiated against smaller modules.

### Bash dependency distribution

| needs-bash | Count |
|-----------|-------|
| Yes | 8 |
| No | 7 |

Good balance. Experiment 3 needs tasks in both categories.

### Planning-matters distribution

| Level | Count |
|-------|-------|
| Low | 1 |
| Medium | 5 |
| High | 9 |

Skewed toward high planning-matters. This is correct for Experiment 11 (which tests whether planning tool quality affects outcomes), but need a few more low-planning tasks for controls.

---

## Experiment-specific requirements

### For Experiment 3 (Phase Transition)

- Needs: 30 tasks that can be run under three tool configurations (levels 0-2, 2-3, 4)
- Key property: tasks where computation channel availability changes outcomes
- Current coverage: 15 concrete tasks + templates B, C, D, F, H, J are suitable
- Gap: need 15 more instantiated tasks

### For Experiment 6 (Trust Gap)

- Needs: 20-30 task types with bash patterns that are ratchet promotion candidates
- Key property: repeated bash patterns that could become structured tools
- Current coverage: Tasks 2, 4, 9, 10, 11, 12 involve bash patterns
- Gap: need to identify specific bash patterns during pilot runs

### For Experiment 11 (Autonomy Placement)

- Needs: 30-50 tasks with two natural phases, planning quality matters
- Key property: approach quality measurable separately from implementation quality
- Current coverage: 14/15 tasks have high or medium planning-matters
- Gap: need 15-35 more tasks; templates can produce these

---

*This task suite is a design document. No tasks should be run until the experimental infrastructure (tool configurations, specified observer, sandbox diffing) is in place.*
