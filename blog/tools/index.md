# Tools

*The instruments behind the ratchet — what they do, how they work, and how they came to be.*

---

Every tool here started as a friction point. A bash pattern repeated too many times. A workflow that was mechanical but error-prone. A piece of complexity that didn't need to live in a human's head.

The theory is in [The Ma of Multi-Agent Systems](../ma/index). The practice is in [Ratchet Fuel](../fuel/index). These are the tools that crystallized from both — the concrete things you install and run.

---

## The Retritis suite

*Retritis* (n.): inflammation caused by repeated retries. A chronic condition of agent-assisted development. No known cure — only treatments, listed below.

### Parsing & querying

- **[sitting_duck](https://github.com/teague/sitting-duck)** — CSS selectors over tree-sitter ASTs in DuckDB. 27 languages. The query engine underneath everything else.
- **[pluckit](pluckit/index)** — jQuery for source code. Fluent API over sitting_duck for querying, mutating, testing, and committing code in one chain.

### Code intelligence

- **[squackit](https://github.com/teague/squackit)** — Semi-QUalified Agent Companion Kit. MCP server AND CLI wrapping pluckit and fledgling with smart defaults, session caching, compound workflows, and token-aware output. The user-facing surface for code intelligence.
- **[fledgling](https://github.com/teague/source-sextant)** — SQL macros over DuckDB for definitions, callers, cross-file resolution, structural similarity. The query layer underneath squackit.

### History

- **[duck_tails](https://github.com/teague/duck-tails)** — Git history as queryable DuckDB tables. Per-file, per-commit, per-function.

### Build & test

- **[blq](https://github.com/teague/lq)** — Build log capture, sandbox presets, test query. Run builds, query errors, analyze results — all through MCP or CLI.
- **[ratchet-detect](ratchet-detect)** — Analyzes your Claude Code conversation logs and finds your ratchet candidates. One command, actionable report.

### Git workflow

- **[jetsam](https://github.com/teague/jetsam)** — Git workflow accelerator. Save, sync, ship. Preview plans before execution.

### Generation

- **[lackpy](https://github.com/teague/lackpy)** — Micro-inferencer that translates natural language intent into pluckit chains. Qwen 2.5 Coder 3B, local, $0.

### Policy compilation

- **[ducklog](https://github.com/teague/ducklog)** — Compiles umwelt `.umw` policy files to queryable DuckDB databases. Policy is materialized; world state is live views; resolution is derived. Every authorization decision becomes a SQL query. Consumers (kibitzer, nsjail, bwrap, lackpy) read policy with plain SQL — no CSS knowledge required.

### Observation & learning

- **[kibitzer](https://github.com/teague/kibitzer)** — Watches agent tool calls, suggests structured alternatives, coaches toward better patterns. The ratchet's observation phase, automated.
- **[agent-riggs](https://github.com/teague/agent-riggs)** — Cross-session trace analysis, pattern extraction, template promotion. Learns from what works and crystallizes it.

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
