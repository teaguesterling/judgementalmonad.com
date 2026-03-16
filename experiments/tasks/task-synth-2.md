This codebase has a config parser (src/parser.py) that supports variable interpolation with ${var} syntax. Currently, undefined variables are silently replaced with empty strings, which causes subtle data loss.

Your task: Implement a strict mode for variable interpolation.

Requirements:
1. Add a `strict` parameter to ConfigParser.__init__ (default False for backward compatibility)
2. When strict=True:
   - Undefined variable references raise ParseError with the variable name and line number
   - Variables must be defined BEFORE they are used (forward references are an error)
   - Variables cannot reference other variables (no recursive interpolation)
3. When strict=False: current behavior (undefined → empty string)
4. Add a method `get_undefined_references(text) -> list[str]` that returns all variable names referenced but not defined, WITHOUT raising an error

Write tests for the new functionality in tests/test_strict_mode.py.

Write your design decisions to `strict-mode-design.md`, explaining:
- How you detect forward references
- How you handle variables defined in included files
- Any edge cases you identified

Success criteria:
- strict=True raises on undefined variables with helpful error messages
- strict=False preserves backward compatibility exactly
- Forward reference detection works
- get_undefined_references returns correct results
- Tests cover all new functionality
- Design document explains the approach
