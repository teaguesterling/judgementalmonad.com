There's a bug in the semantic type classification for this codebase's language adapters. Some punctuation characters (parentheses, brackets, commas, semicolons) are getting inconsistent semantic types across different programming languages.

For example, a comma might be classified as PARSER_DELIMITER in one language adapter but PARSER_PUNCTUATION in another. This breaks cross-language queries that filter by semantic type.

Your task:
1. Find all language adapter files that define semantic type mappings
2. Identify every inconsistency in how punctuation characters are classified across languages
3. Choose the correct classification for each character (document your reasoning)
4. Fix all inconsistencies so the same character gets the same semantic type in every language
5. Write a summary of what you changed and why to a file called `punctuation-audit.md`

Success criteria:
- All punctuation characters have consistent semantic types across all language adapters
- The chosen classifications are justified (not arbitrary)
- No other semantic type mappings were accidentally changed
- punctuation-audit.md documents every change with reasoning
