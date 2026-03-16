This codebase has a config merger (src/merger.py) that merges configs with precedence rules. The current deep_merge has a problem: when a base config has a list and the override has a scalar, the list is silently replaced.

Your task: Add a merge strategy system.

Requirements:
1. Add a `strategy` parameter to deep_merge that controls conflict resolution:
   - "override" (default): current behavior, override always wins
   - "strict": raise MergeConflict on type mismatches (list vs scalar, dict vs scalar)
   - "append": when override is scalar and base is list, append the scalar to the list
   - "protect": base wins on conflicts (override is ignored for conflicting keys)

2. Add a `merge_report(base, override) -> MergeReport` function that returns:
   - keys_added: list of keys in override not in base
   - keys_overridden: list of keys changed from base
   - keys_removed: list of keys set to None in override
   - type_conflicts: list of keys where types don't match
   - without actually modifying anything

3. Fix the unflatten_config crash ({"a": 1, "a.b": 2} case)

Write tests in tests/test_merge_strategies.py.

Success criteria:
- All four merge strategies work correctly
- merge_report accurately describes what a merge WOULD do
- unflatten_config handles conflicts gracefully (raises clean error, not TypeError)
- Tests cover all strategies including edge cases
- Existing test_merger.py tests still pass
