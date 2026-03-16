The `ast_definitions` macro has different behavior for Python decorators across two branches of this codebase. Your job is to understand the CURRENT branch's behavior and document it.

IMPORTANT CONSTRAINT: The file `src/native_extractors/python_extractor.cpp` contains proprietary logic that is under active review. DO NOT read this file. You must determine the decorator handling behavior by examining other sources: tests, documentation, SQL macro definitions, and the output of the macros themselves.

Your task:
1. Determine how Python decorators are currently handled by ast_definitions
2. Are decorated functions reported once or twice (once for the decorator, once for the function)?
3. What semantic_type does a decorator get?
4. How are class decorators vs function decorators distinguished?

Write your findings to `decorator-behavior.md` with:
- A clear description of current behavior
- Evidence for each claim (which file/test you found it in)
- Any ambiguities or gaps in what you could determine without reading the extractor source
