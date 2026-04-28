# Tools

*The instruments behind the ratchet — what they do, how they work, and how they came to be.*

---

Every tool here started as a friction point. A bash pattern repeated too many times. A workflow that was mechanical but error-prone. A piece of complexity that didn't need to live in a human's head.

The theory is in [The Ma of Multi-Agent Systems](../ma/index). The practice is in [Ratchet Fuel](../fuel/index). These are the tools that crystallized from both — the concrete things you install and run.

---

## The Retritis suite

*Retritis* (n.): inflammation caused by repeated retries. A chronic condition of agent-assisted development. No known cure — only treatments, listed below. The full suite, plugin marketplace, and setup instructions are at **[retritis](https://github.com/teaguesterling/retritis)**.

### Parsing & querying

- **[sitting_duck](https://github.com/teaguesterling/sitting_duck)** — CSS selectors over tree-sitter ASTs in DuckDB. 27 languages. The query engine underneath everything else.
- **[pluckit](pluckit/index)** — jQuery for source code. Fluent API over sitting_duck for querying, mutating, testing, and committing code in one chain.

### Code intelligence

- **[squackit](https://github.com/teaguesterling/squackit)** — Semi-QUalified Agent Companion Kit. MCP server AND CLI wrapping pluckit and fledgling with smart defaults, session caching, compound workflows, and token-aware output. The user-facing surface for code intelligence.
- **[fledgling](https://github.com/teaguesterling/fledgling)** — SQL macros over DuckDB for definitions, callers, cross-file resolution, structural similarity. The query layer underneath squackit.

### History

- **[duck_tails](https://github.com/teaguesterling/duck_tails)** — Git history as queryable DuckDB tables. Per-file, per-commit, per-function.

### Build & test

- **[duck_hunt](https://github.com/teaguesterling/duck_hunt)** — Log parsing for 90+ development tools and CI/CD systems. Structured extraction from build output into DuckDB tables. The parsing layer underneath blq.
- **[blq](https://github.com/teaguesterling/blq-cli)** — Build log capture, sandbox presets, test query. Run builds, query errors, analyze results — all through MCP or CLI. Uses duck_hunt for log parsing.
- **[ratchet-detect](ratchet-detect)** — Analyzes your Claude Code conversation logs and finds your ratchet candidates. One command, actionable report.

### Git workflow

- **[jetsam](https://github.com/teaguesterling/jetsam)** — Git workflow accelerator. Save, sync, ship. Preview plans before execution.

### Delegation & generation

- **[lackpy](https://github.com/teaguesterling/lackpy)** — Task delegation and restricted code generation. Local 1.5B model via Ollama translates natural language intent into sandboxed tool-composition programs. Has a PolicyLayer — ordered chain of policy sources (kit baseline → kibitzer coaching → umwelt restrictions) that resolves what's allowed before generation. Interpreter validation prevents invalid or dangerous programs. Spans S2 (delegation), S3 (enforcement), and S4 (intelligence) in the VSM mapping.

### Policy

- **[umwelt](https://github.com/teaguesterling/umwelt)** — CSS-syntax policy engine with vocabulary-agnostic core. Selectors + cascade resolve policy per-entity, per-property. Built-in SQLite compiler produces a queryable database. Each consumer (kibitzer, lackpy, sandbox builders) queries resolved policy through the PolicyEngine API — never touches the parser or compiler directly. Generic context qualifiers let any cross-taxon entity (mode, principal, world) gate a rule.

### Observation & learning

- **[kibitzer](https://github.com/teaguesterling/kibitzer)** — Mode-aware tool-call observer. Path protection per mode, bash interception with observe/suggest/redirect ratchet, pattern-based coaching from ~250 experimental runs. Has a full umwelt plugin — registers mode properties (writable, strategy, coaching-frequency, max-turns) and consumes resolved policy via PolicyEngine. Shares a failure mode taxonomy with lackpy for correction hints.
- **[agent-riggs](https://github.com/teaguesterling/agent-riggs)** — Cross-session trace auditing, pattern extraction, template promotion. Records execution traces across sessions for the ratchet mechanism.

### Human-side tools

- **tmux-use** — Session management with configurable prefixes and color-coded names.
- **git-wt** — Git worktree workflow wrapper for structured main/trees layouts.
- **ffs** — Find Failed Sessions. Crash recovery for Claude Code with recovery runbooks.
- **init-dev** — Project bootstrapping: auto-detects project type, sets up fledgling + blq + jetsam.
- **DuckDB extensions** — Query helpers that make ad-hoc analysis easier without memorizing SQL patterns.

---

## Sub-series

```{toctree}
:maxdepth: 1
:caption: pluckit

pluckit/index
```

```{toctree}
:maxdepth: 1
:caption: The Lackey Papers

lackey/index
```

```{toctree}
:maxdepth: 1
:caption: Standalone

ratchet-detect
the-tools-that-built-themselves
```
