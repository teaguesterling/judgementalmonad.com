# Proposed Skills

*Annotated skill definitions for Claude Code — each one a ratchet turn that closes a computation channel.*

These proposals show what superpowers/skills look like when designed from ratchet-detect data. Each skill is a crystallized pattern: a computation channel that appeared frequently in conversation logs, got characterized, and now has a structured replacement. The skill definitions are shown in code blocks with annotations explaining the design reasoning.

None of these are implemented yet as Claude Code plugins. They're proposals — the Stage 1 observation that precedes Stage 2 crystallization. Read them as annotated blueprints, not as finished tools.

```{toctree}
:maxdepth: 1

skill-ratchet-review
skill-git-workflow
skill-build-query
skill-codebase-explore
```

## The pattern

Each skill follows the same structure:

1. **Identify the computation channel** from ratchet-detect data (which Bash patterns dominate?)
2. **Map to structured alternatives** that already exist (JetSam, blq, Fledgling, built-in tools)
3. **Define the routing rules** (when to use the structured tool, when to fall back to Bash)
4. **Annotate the reasoning** (which ratchet concept drives each design decision)

The skills are themselves ratchet artifacts — the discovery phase (ratchet-detect data) crystallized into teaching artifacts (skill definitions) that route future agent behavior through data channels instead of computation channels.
