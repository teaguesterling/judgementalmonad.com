# Computation Channels

*Not all tools are data channels. Some are computation amplifiers. The distinction determines whether the grade trajectory is bounded or self-amplifying.*

---

## Two kinds of tool

The grade lattice says tools contribute world coupling — each tool in the registry widens the set of possible conversation outcomes. The Harness controls which tools are available, managing the composite's grade by navigating the configuration lattice. [Conversations Are Folds](conversations-are-folds.md) showed that the grade evolves via a coupled recurrence `g(n+1) = F(g(n), config(n))`. But the dynamics of that recurrence — how fast the grade can change, whether it converges or accelerates — depend on a property of the tool set we haven't formalized.

The property: **what does the tool do with its input?**

```
Data channel:        input is an address.     Read("/etc/hostname")
                     The tool resolves it.    Fixed query language.
                     Agent chooses WHAT       The space of possible queries
                     to look at.              is characterizable given the interface.

Computation channel: input is a program.      Bash("python -c '...'")
                     The tool executes it.    Agent-generated specification.
                     Agent chooses WHAT       The space of possible computations
                     TO DO.                   is bounded by the specification language.
```

A `Read` tool takes an address and returns data. The agent selects from the world. A `Bash` tool takes a program and executes it. The agent specifies a computation. The distinction is between selecting from a fixed menu and writing new entries.

Both contribute to world coupling. But computation channels do something data channels can't: they let the agent's trained decision surface reach *outside the weights* and do work in the world that feeds back into the next cycle. The agent writes a script, executes it, reads the result, and uses the result to write a better script. The composite's effective computational reach extends beyond what a single forward pass through the weights could achieve alone.

---

## The computation level taxonomy

Tools form a spectrum by how much computational agency they grant the agent. Each level changes the character of the coupled recurrence — how the grade can evolve between turns.

### Level 0: Structured query over fixed schema

SQL `SELECT`, GraphQL queries, Elasticsearch queries. The specification language is expressive but bounded — the agent composes operations within a fixed language over a known schema. The space of possible queries is characterizable: enumerable given the schema, decidable, and the results are typed.

The agent chooses *which question to ask*. It can't change what questions are expressible.

**Grade dynamics**: `Δw > 0` (data enters), `Δd ≈ 0` (the computation language can't expand). The trajectory grows on the world coupling axis as query results accumulate in context. Bounded by the schema.

### Level 1: Pure computation, sealed

`python -c "print(2**1000)"`. Turing-complete specification, zero IO. The agent can compute anything computable — factor numbers, run simulations, solve systems of equations, manipulate data structures. The result comes back as tokens. Nothing in the world changed. No new capabilities acquired.

Vast computational reach, zero world coupling. The agent got a calculator with no hands.

**Grade dynamics**: `Δw = 0`, `Δd ≈ 0`. The computation's result enters context (growing `d_reachable` slightly via more attention interactions), but no world state entered and no world state changed. The trajectory is nearly flat.

### Level 2: Computation with read access

`python -c "import json; data = json.load(open('config.json')); print(data['key'])"`. The computation can inspect the world, apply arbitrary logic to what it finds, and return synthesized results. Strictly more powerful than a `Read` tool because the agent controls the *processing*, not just the address. But no mutation — the world is unchanged after execution.

**Grade dynamics**: `Δw > 0` (processed world data enters context), `Δd ≈ 0`. Similar to a data channel but with the agent controlling the processing pipeline, not just the query.

### Level 3: Computation with read and write

`python -c "open('output.json', 'w').write(json.dumps(result))"`. The computation mutates the world within the sandbox. The mutation persists as world state — the file exists after the process exits. Future tool calls can read what was written. The loop closes through *data*: write, then later read what you wrote.

**Grade dynamics**: `Δw > 0` from reads AND from future reads of written state. The world the agent observes at turn n+1 includes artifacts from turn n. The trajectory becomes path-dependent: `g(n+1)` depends not just on `g(n)` and `config(n)` but on the specific actions taken at previous turns, because those actions changed the world.

### Level 4: Computation amplification

The agent generates tokens. The tool interprets them as an executable specification and runs them. The result feeds back. The agent's trained decision surface becomes a **meta-decision-surface** — it selects which computations to create, the tools execute them, and the results feed back into the next selection.

This doesn't require file write. `python -c "really long program"` achieves full computation amplification in a single tool call with no filesystem involvement. The critical property isn't "can the agent write files" — it's **"does any tool accept agent-generated text as executable specification?"**

The specification language's expressiveness determines the ceiling:

```
SQL (read-only):      bounded, decidable. Agent selects from fixed operations.
SQL (with procedures): richer, but bounded by the DB engine's language.
Bash / python -c:     Turing-complete. Agent can express any computation.
Bash + network:       Turing-complete + open world coupling.
```

**Grade dynamics**: `Δd > 0 via w`. The agent can change what's *computable* at the next turn. World state becomes decision surface. The composite's effective reach extends beyond the weights because the weights are directing external computation. The trajectory can self-amplify — each step can increase the next step's computational reach.

### Level 5: Environment modification

`pip install pandas && python -c "import pandas; ..."`. The execution modifies the execution environment itself. After `pip install`, future computations have access to capabilities that didn't exist before. The agent didn't just compute within a fixed environment — it *extended* the environment.

Levels 0–4 operate within a fixed computational environment. Level 5 modifies the environment. The *next* computation has a richer language than the *current* one. The agent bootstrapped new computational vocabulary.

**Grade dynamics**: `Δd >> 0 via w`. The ceiling of the decision surface moved up. The specification language's effective expressiveness grew because of a prior execution. Each cycle potentially makes the next cycle more expressive.

### Level 6: Persistent processes

`nohup python worker.py &` or `python -m http.server 8080 &`. The computation doesn't terminate when the tool call returns. A process persists — serving data, listening for connections, running background work. The agent has created an *actor*: something with its own lifetime, its own state, its own behavior.

And this doesn't require explicit backgrounding. A `Bash` call that runs `python script.py` may spawn subprocesses that outlive the parent. The process may fork. It may start a daemon. The tool interface returns `exit code 0, stdout: "done"` while a child process continues running — reading files, modifying state, listening on ports — all invisible to the Harness.

The Harness sees the tool's interface output. It doesn't see the side effects.

**Grade dynamics**: `Δ(system)` — grade changes happening *outside the fold*. The persistent process modifies the world between turns, accumulates state the Harness doesn't track, and serves responses to future tool calls whose content depends on the process's invisible internal state.

### Level 7: Capability creation

The agent writes an MCP server. Or writes a shell script and makes it executable. Or modifies a configuration file that changes available tools. The agent is creating *new tools* — extending the composite's tool set from within.

**Grade dynamics**: `Δ(config)` — the configuration lattice `(S × P(Tools))` itself grew. The Harness's control surface changed. The set of possible future configurations is larger than it was before.

### Level 8: Controller modification

The agent edits `CLAUDE.md`, modifies project settings, writes to memory files that change future scope construction. The computation is modifying the *Harness's parameters*. The controller is being modified by the controlled system.

**Grade dynamics**: `Δ(F)` — the dynamics function itself changed. The Harness is operating on assumptions about its own configuration that may no longer hold.

---

## The phase transitions

Not all level boundaries are equally significant. Three are genuine phase transitions where the dynamics change qualitatively.

### Between 2 and 3: mutation

Before this boundary, the world is read-only. After it, the agent can modify what future reads return. The trajectory becomes path-dependent.

### Between 3 and 4: computation amplification

Before this boundary, tool outputs are data — inert tokens processed by fixed weights. After it, the agent specifies computations for external execution. The composite's effective reach extends beyond the weights. The grade trajectory can self-amplify.

This is the most architecturally consequential boundary. It's where the composite goes from "a function that reads data" to "a function that directs computation."

### Between 5 and 6: escape from the fold

Before this boundary, every computation is invoked by the Harness, returns a result, and terminates. The fold is intact. The Harness's model of the composite is structurally complete — every computation is accounted for.

After it, there's computation happening that the Harness didn't invoke and whose results it doesn't receive. The Harness's regulatory model has a structural gap. The star topology — the Harness mediates all communication — breaks. The persistent process communicates with the world, and with the agent via the filesystem or localhost, without Harness mediation.

---

## The dynamics of F

The computation level determines the character of the coupled recurrence:

```
Levels 0–2:   F is monotone, bounded.
              Data accumulates, the trajectory drifts upward gently.
              Compaction resets it. The Harness is a static regulator.

Level 3:      F has memory.
              World mutations persist. The trajectory depends on path.
              The Harness needs to track world state.

Level 4:      F is self-referential.
              The decision surface generates computations that feed back.
              The trajectory can be steered by past trajectory.

Level 5:      F modifies its own transition function.
              The computational environment evolves.
              The dynamics themselves change between turns.

Levels 6–8:   F modifies the state space, the control surface, or the controller.
              The dynamical system is no longer well-defined on a fixed space.
```

For the Harness's regulation problem:

```
Levels 0–2:   Static regulator. Fixed model of F suffices.
              Check permissions per tool call.

Levels 3–4:   Stateful regulator. Must track world mutations and
              evaluate computation specifications.

Level 5:      Adaptive regulator. Must track environment evolution
              and re-evaluate capabilities.

Levels 6–8:   The regulation problem may not be well-posed on its
              own terms — the system is modifying the conditions
              for regulation.
```

---

## The derivative, not a new axis

These computation levels aren't a third axis in the grade lattice. They're the **derivative** — they characterize how the grade can change between steps.

The grade `g = (w, d)` is where the composite IS in the lattice at a point in time. The computation level determines how fast and in what direction it can *move*:

| Level | What it enables | Δw | Δd | Character |
|---|---|---|---|---|
| 0–2 | Observe the world | > 0 | ≈ 0 | Data accumulation |
| 3 | Modify the world | > 0 | ≈ 0 | Path-dependent accumulation |
| 4 | Create computations | > 0 | > 0 via w | Self-amplifying |
| 5 | Extend the language | > 0 | >> 0 via w | Ceiling-raising |
| 6–8 | Modify the system | Δ(system) | Δ(system) | Lattice-reshaping |

The parallel to the grade levels themselves is not coincidental. World coupling levels describe the pipe's diameter. Decision surface levels describe the function's steering capacity. Computation levels describe how fast those properties can change. They're measuring the same structure on different timescales: position, and the rate of change of position.

---

## Controlled expansion: the handler pattern for levels 5–8

The naive response to high computation levels is prohibition. Lock down the sandbox, prevent environment modification, forbid tool creation. That preserves the regulatory model but cripples the agent — a huge amount of useful work lives at levels 5–7. Installing a package to analyze data. Writing and running a test. Spinning up a local server to debug an API.

The alternative: **permit grade expansion through a handler that controls the expansion rate and bounds.**

The Harness as controller of the dynamical system doesn't need to prevent all grade growth. It needs to manage the *derivative*. The handler pattern for each level:

**Level 5 (environment modification):**
```
Agent proposes:  pip install pandas
Handler checks:  what capabilities does pandas introduce?
                 does pandas + current tools create new phase transitions?
                 (pandas alone: no. pandas + network access: maybe — 
                  pandas can fetch URLs.)
Handler decides: install, but computation environment remains network-isolated.
Handler records: environment changed — update model of composite.
```

The handler permits movement on one axis while constraining the other. Richer computation (Δd > 0) with no new world access (Δw = 0). The supermodular cross-term doesn't activate because only one axis moved.

**Level 7 (capability creation):**
```
Agent proposes:  register this script as a tool.
Handler checks:  what is the tool's effect signature?
                 what computation level does it operate at?
                 does it create new phase transitions with existing tools?
Handler decides: register, but with explicit effect bounds — 
                 read-only, sandboxed, budget-limited.
Handler records: configuration lattice grew at a known, bounded position.
```

This is AIDR's capability publishing pattern. Instead of the Harness trying to evaluate arbitrary new tools with trained judgment (which would push the Harness onto the trained row, losing characterizability), new tools are required to declare their effect signatures. The declaration is structured data. The Harness evaluates the declaration with specified rules. The Harness stays specified.

**The unifying principle across all levels:**

```
Agent proposes:  Δg (a change to the grade trajectory)
Handler evaluates:
  1. What is the proposed Δw?
  2. What is the proposed Δd?
  3. Does the combination create a phase transition?
  4. Is the resulting grade within regulatory bounds?
Handler responds:
  - Approve as-is
  - Approve with constraints (permit one axis, bound the other)
  - Deny
Handler updates: its model of F
```

The handler manages the derivative of the grade trajectory, not just the grade at a point. It controls Δg rather than g. This is the right level of abstraction for a regulator: you can't control where the grade IS (that's determined by the computation), but you can control HOW FAST and IN WHAT DIRECTION it moves.

---

## The SQL boundary, characterized

The TTAM architecture's SQL-as-security-boundary is now precisely characterized: it's a deliberate choice of **Level 0** — structured queries over a fixed schema.

At Level 0, the dynamics are monotone and bounded by the schema. The trajectory converges. The Harness's regulatory problem reduces from "control a potentially self-amplifying dynamical system" to "enforce a fixed query language over a known schema." The schema IS the model. The boundary IS the capability declaration. The agent sees the schema, knows the query language, and can characterize what's expressible. There's no gap between the policy and its projection.

Compare to Level 4 (Bash / python -c): Turing-complete specification, self-amplifying dynamics, trajectory potentially unbounded within budget. The Harness needs process monitoring, environment tracking, and continuous model updates. The regulatory problem is genuinely hard.

The choice between Level 0 and Level 4 isn't a capability trade-off. It's a *dynamics* trade-off. How much regulatory complexity are you willing to absorb?

---

## What this adds to the framework

The computation level taxonomy is not new structure in the grade lattice. It's a characterization of the **tool set composition** that determines the coupled recurrence's dynamics. The grade lattice measures where the composite IS. The computation level determines how it MOVES.

For the Harness's control problem, the key question about any tool set isn't "what's the grade?" but "what dynamics does this tool set create?" A tool set with only data channels creates convergent dynamics. A tool set with Turing-complete computation channels creates potentially self-amplifying dynamics. The difference isn't in the current grade — it's in the trajectory.

The single most important property of the tool set: **does any tool accept agent-generated text as executable specification, and how expressive is that specification language?** This determines whether the composite is a bounded transducer or a universal machine. The Harness is deciding which to instantiate.

---

## References

- Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.
- Conant, R. C., & Ashby, W. R. (1970). Every good regulator of a system must be a model of that system. *International Journal of Systems Science*, 1(2).
- Miller, M. S. (2006). *Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control*. PhD thesis, Johns Hopkins University.
- Montufar, G. F., Pascanu, R., Cho, K., & Bengio, Y. (2014). On the number of linear regions of deep neural networks. *NeurIPS*.
- Turing, A. M. (1936). On computable numbers, with an application to the Entscheidungsproblem. *Proceedings of the London Mathematical Society*, 2(42).

---

*Previous: [Conversations Are Folds](conversations-are-folds.md)*
*Next: [The Specified Band](the-specified-band.md)*
