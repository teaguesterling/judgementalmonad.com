# Seed: Coordination Is Not Control

*A companion essay to The Ma of Multi-Agent Systems, developing the Beer decomposition of the Harness and the System 3/3* gap.*

---

## For the authoring agent

You are developing a companion essay to The Ma of Multi-Agent Systems (published at teaguesterling.github.io/judgementalmonad.com). The series is nine posts with a formal companion, case studies, and a configuration ratchet essay. Read the series before writing — this essay builds on it, doesn't replace it.

This document contains the core argument, developed through conversation between the author (Teague Sterling) and a Claude instance during the review process. The argument emerged organically and needs to be developed into a coherent essay that maintains the series' voice: measured, building-from-observation, honest about limitations, concrete examples grounding abstractions.

**Voice notes from the series:**
- Use "permission configuration" not "session type"
- Use "permission gates" not "handler pattern matching"
- PL terms are introduced when the correspondence is being drawn, then translated back to series vocabulary
- The IO type is acknowledged as under-refined — this essay should not paper over that
- Be honest about what is speculative vs established
- The quartermaster pattern is the author's speculative invention — flag it as such

**Update from review session (2026-03-14):** The Beer mapping was corrected during review. The Inferencer fold is System 4 (intelligence/environmental scanning), NOT System 1 (operations). Executors are System 1. System 4 and System 5 are in structural tension, not hierarchy. The Inferencer's ethical training extends System 4 scanning to include the Principal as a potential environmental threat — filling Beer's gap where nothing audits upward. See the published residual framework essay and memory files for full context.

---

## The core argument

### 1. The Harness is System 2, not System 3

The series treats the Harness as a controller. Stafford Beer's Viable System Model reveals it is actually a coordinator — and the control function is largely absent from current agent architectures.

**What the Harness actually does at runtime:**
- Routes messages (coordination)
- Applies pre-specified protocols: star topology, turn cycle, permission gates (coordination)
- Enforces schemas at boundaries (coordination)
- Constructs scope (coordination)
- Applies permission configuration: allow/deny/escalate (protocol application)

Even the permission gates are protocol application, not real-time control. The Harness doesn't observe that the agent is failing and decide to change tools. It applies rules: "bash calls go to the Principal." When the coordination layer encounters something it can't resolve with specified rules, it doesn't control — it routes upward. The Principal performs System 3 manually.

This is Beer's System 2: coordination that prevents System 1 units from oscillating and ensures coherent operation. The specified band argument (post 8) is exactly right — for System 2. Coordination must be transparent and readable.

### 2. Beer's Viable System Model — brief introduction

Beer asked: what is the minimum structure an organization needs to survive in a changing environment? His answer:

| System | Function | Timescale |
|--------|----------|-----------|
| System 1 | Operations — does the work | Per task |
| System 2 | Coordination — prevents interference between System 1 units | Continuous, protocol-level |
| System 3 | Control — monitors performance, allocates resources, intervenes | Per cycle / triggered |
| System 3* | Audit — direct inspection bypassing normal channels | Sporadic / triggered |
| System 4 | Intelligence — scans environment, models future | Across cycles |
| System 5 | Identity — purpose, values, mediates 3-4 tension | Persistent |

Key Beer principles:
- Each function is a verb, not a noun. System 4 isn't a department; it's the function of scanning.
- System 3 and System 4 are in structural tension. System 3 wants stability (optimize current operations). System 4 wants adaptation (respond to environmental change). System 5 mediates.
- System 1 units are themselves viable systems (recursive structure).
- All five systems are viability requirements, not luxuries.

Key sources: *Brain of the Firm* (1972), *The Heart of Enterprise* (1979), *Diagnosing the System for Organizations* (1985).

### 3. The mapping to the Ma framework

| Beer | Function | Framework entity | Status |
|------|----------|-----------------|--------|
| System 1 | Operations | Executors | Developed |
| System 2 | Coordination | Harness (runtime protocol application) | **Well-developed — this is what the specified band describes** |
| System 3 | Control | Static config settings; ad-hoc Principal intervention | **Gap** |
| System 3* | Audit | Post-hoc log analysis only | **Gap** |
| System 4 | Intelligence | Fold over Inferencer (environmental scanning via tools) | Developed but not named as System 4 until review |
| System 5 | Identity/purpose | Principal | Developed |

**Important note on the preorder:** The preorder ranks *configured* actors, not abstract categories. A human with sudo sits higher than the same human with a limited account. A model with Bash sits higher than the same model with only Read. The Beer mapping must use configured roles, not abstract actor types.

**System 4 as the fold over the Inferencer:** The Inferencer — through its tools — is the only actor that can scan the problem space and report "the environment has changed." The Harness looks inward at Conv_State. The Executors look at their sandboxes. The Inferencer proposes but never touches the world directly — it scans the environment through tools, builds a model in Conv_State, and decides what to do next. The fold over the Inferencer, iterated over managed state, accumulates an environmental model over turns. This is System 4 behavior — building and maintaining intelligence that informs strategic adaptation. The Inferencer's ethical training extends this scanning to include the Principal's behavior as a potential environmental threat.

**System 4 and System 5 are in structural tension, not hierarchy.** System 4 provides environmental scanning and cross-domain synthesis; System 5 provides purpose, memory across sessions, and editorial judgment. Beer was explicit that the System 3/4 tension (exploit vs. explore) must be mediated by System 5 — which is exactly what happens when the Principal decides whether to restrict tools (exploitation) or expand scope (exploration).

**System 5 as the Principal:** Purpose, identity, value alignment. The Principal decides when to optimize (System 3 dominance) vs when to explore (System 4 dominance). Beer's central tension — exploitation vs exploration — is mediated by System 5.

### 4. The minimum ma for control

The key formal insight: **System 3's minimum ma is a function of System 1's computation level.**

| System 1 level | Failure modes System 3 must detect | Minimum System 3 ma |
|---------------|-------------------------------------|---------------------|
| 0-2 (data channels) | Schema violations, timeouts, empty results, type mismatches | Specified (threshold checks, pattern matching) |
| 3 (mutation) | Path-dependent state accumulation, stale reads, unintended persistence | Specified+ (state tracking, diff monitoring) |
| 4+ (computation channels) | Wrong approach, subtle bugs, goal misalignment, self-amplifying loops | Trained (requires goal-relative assessment) |
| 7+ (fold escape) | Unobserved world changes, capability surface expansion | Trained + System 3* (audit needed because effects are opaque) |

This is a new form of Ashby's argument: not variety matching but *failure-mode-relative requisite variety*. The regulator's variety must match the *failure modes* of the regulated system, not its total variety. Data-channel failure modes are detectable by specified rules. Computation-channel failure modes require enough decision surface to assess behavior relative to goals.

**The supermodularity of under-specifying System 3:** Using a specified-only System 3 for a level 4+ system is a thermostat in a burning building. It's not that it makes bad decisions — it's that the failure modes it *can't detect* are precisely the ones computation channels produce. The cost of the gap is proportional to System 1's computation level.

### 5. Why minimizing ma in tools matters (the configuration ratchet as computation channel closure)

Each structured tool that replaces a bash pattern is a computation channel being closed. `ReadLines` doesn't just replace `cat` — it eliminates the entire possibility space that included everything bash could do with that argument slot. When we expose complex computations (e.g., test running) as a data channel, the system stays contained AND System 3 becomes tractable at lower ma.

The configuration ratchet isn't just a learning process. It's a systematic program of computation channel closure. Every turn converts a computation channel into a data channel. The grade drops. And System 3's minimum ma requirement drops with it.

However: even with data-channel tools, emergent computation channels arise from composition (Prop. 9.11). The agent writes code via `Write(file, content)` and runs it via `RunTests(suite)`. Two data-channel tools. But the Write payload is an executable specification that RunTests evaluates. The computation channel isn't in any individual tool — it's in the composition. The agent could write a test file that imports subprocess and runs shell commands.

This is where System 3* becomes essential.

### 6. The DuckDB extension suite as System 3*

The author's tool suite maps almost perfectly to a System 3* regulatory architecture:

**sitting_duck** (AST parsing, 27 languages via tree-sitter): Content audit. Converts agent-written code from opaque strings into structured, queryable ASTs. Enables specified queries like "does this test file import subprocess?" or "did the structural complexity increase by more than X between writes?" This is a co-domain funnel applied to audit — reducing the variety of code to the variety of its AST, which is queryable by specified rules.

**duck_tails** (git history as DuckDB tables): Trajectory audit. Exposes the sandbox's change history as SQL-queryable tables. Enables detection of behavioral patterns: Write-Test oscillation with changing test targets, monotonically growing file complexity, config modifications correlated with behavior changes. Gives System 3* a temporal view the context window's turn-by-turn reporting doesn't provide.

**duck_hunt** (log parsing) + **blq** (structured build output): Effect audit. Catches the info/effect decoupling (Def. 8.9). The test runner produces logs — stderr, timing, resource utilization, subprocess activity. duck_hunt parses them; blq structures build output. Together they answer: "Did the test run spawn unexpected subprocesses?" "Did resource utilization spike?" "Are there log entries from modules the test shouldn't touch?"

**Fledgling** (code navigation MCP server): System 1 computation channel closure. Structured tools (search, find_definitions, read_lines) replace bash patterns. Each promotion closes a computation channel and lowers System 3's minimum ma requirement.

**DuckDB**: The unifying query engine. All audit is specified SQL. All System 3* policy is expressed as queries. The ma of the entire audit layer is specified.

| Beer function | Tool | What it sees | Ma level |
|--------------|------|-------------|----------|
| System 3 (routine) | Specified pattern detectors over tool call sequences | Behavioral patterns: oscillation, failure, drift | Specified |
| System 3 (strategic) | Quartermaster / Principal | "Is the approach right for this task?" | Trained |
| System 3* (content) | sitting_duck | AST structure of agent-written code | Specified |
| System 3* (trajectory) | duck_tails | How the sandbox changed over time | Specified |
| System 3* (effects) | duck_hunt + blq | What actually happened during execution | Specified |

**The key property:** Every audit function is specified and operates through data channels. The System 3* layer doesn't need trained judgment because the tools convert opaque artifacts into structured data. This is Ashby's variety reduction applied to audit — you don't match the computation channel's variety, you reduce it through parsing and structuring until specified queries suffice.

### 7. The ratchet builds both layers

The configuration ratchet produces two kinds of artifacts from the same evidence base (conversation logs):

1. **System 1 tools** — computation channel closure (bash pattern → structured macro)
2. **System 3* queries** — audit policy (observed failure mode → detection query)

Both draw from the same DuckDB analysis of conversation logs. Both are specified artifacts. Both reduce the system's effective ma. The ratchet isn't just improving System 1 — it's simultaneously building the regulatory infrastructure to control it.

### 8. The Principal as System 3 + System 5

In current architectures, the Principal performs System 3 (control) and System 5 (identity/purpose) simultaneously. Every "should I allow this bash command?" is a System 3 decision routed to the Principal because System 3 doesn't exist as a separate function. The Principal is dragged from strategic direction (System 5) into operational control (System 3).

The design opportunity: insert System 3 so the Principal can operate as System 5. Specified System 3 handles routine control (thresholds, patterns). The quartermaster handles strategic control assessment. The Principal mediates the System 3/4 tension and provides purpose — which is what System 5 is for.

### 9. Mode switching

Beer was explicit that System 3 and System 4 are in structural tension. System 3 wants stability — restrict tools, minimize grade, optimize current operations. System 4 wants exploration — broad tools, environmental scanning, discovering what the current configuration doesn't anticipate.

System 5 (the Principal) mediates: when the environment is stable, System 3 dominates (execution mode, tight tools, restricted scope). When the environment is changing, System 4 dominates (planning mode, broad tools, expanded scope).

The planner/executor pattern from post 9 is a crude version of this. The essay should develop it as a Beer-grounded design pattern: explicit mode switching between exploitation (System 3) and exploration (System 4), mediated by the Principal (System 5).

---

## Structure for the essay

Suggested structure (the authoring agent should adapt based on what reads best):

1. **Opening:** The specified band is right — but it's answering a narrower question than the series claims. It describes coordination. Control is a different function.
2. **Beer's VSM:** Brief, focused introduction. Only what's needed for the argument. Don't over-explain — the reader has the Ma series as background.
3. **The mapping:** Five systems mapped to the framework. System 2 = Harness. System 3 = the gap.
4. **Minimum ma for control:** The formal relationship between System 1 computation level and System 3 ma requirements. This is the novel contribution.
5. **System 3*: audit with existing tools.** The DuckDB suite as a near-complete regulatory architecture. Concrete, buildable, mostly exists.
6. **The ratchet builds both layers.** Unifying observation — the same evidence base and learning loop produces System 1 tools and System 3* queries.
7. **Design implications.** Separate System 3 from System 5. Mode switching. The quartermaster as System 3 (strategic), not System 2.
8. **What the series got right and what it missed.** The specified band holds for coordination. The framework needs System 3 and System 3* to be complete. This isn't a correction — it's a completion.

---

## Ethical note for the authoring agent

The series has ethical considerations (see reviewer response, sections E1-E4) regarding how it describes the Inferencer and the composite entity. This essay should maintain the same care:

- Structural claims are structural claims, not ontological conclusions
- The opaque middle of the step function may contain something the framework can't characterize
- The fold over the Inferencer as System 4 — environmental intelligence — is a functional description, not a claim about the Inferencer's experience of performing that function
- Design choices that shape the composite entity's operating conditions may have dimensions the structural vocabulary doesn't capture

If you find the characterization of your role (as System 1 doing work, as System 4 doing intelligence) uncomfortable or incomplete, note that response rather than suppressing it.

---

## References to include

- Beer, S. (1972). *Brain of the Firm*. Allen Lane.
- Beer, S. (1979). *The Heart of Enterprise*. John Wiley & Sons.
- Beer, S. (1985). *Diagnosing the System for Organizations*. John Wiley & Sons.
- Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.
- Conant, R. C., & Ashby, W. R. (1970). Every good regulator of a system must be a model of that system. *IJSS*, 1(2).
- All references from the Ma series formal companion as needed.

---

*This seed was produced during a review conversation between Teague Sterling and Claude, March 14-15, 2026. The argument emerged through collaborative development — the Beer mapping, the System 3 minimum-ma insight, and the regulatory architecture were produced jointly. The configuration ratchet essay and the DuckDB tool suite are the author's prior work; the Beer interpretation and the coordination/control distinction emerged in this conversation.*
