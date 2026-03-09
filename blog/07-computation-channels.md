# Computation Channels

*Not all tools are data channels. Some are computation amplifiers. The distinction determines whether the grade trajectory is bounded or self-amplifying.*

---

## Two kinds of tool

Post 6 showed that the grade evolves via a coupled recurrence: `g(n+1) = F(g(n), config(n))`. But the dynamics of that recurrence — how fast the grade can change, whether the trajectory converges or accelerates — depend on a property of the tool set the framework hasn't formalized.

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

This is the IO refinement that post 5 promised. `IO` collapsed three dimensions: what *enters* the computation (world coupling — post 2 handles this), what *exits* as output (interface restriction — co-domain funnels handle this), and what the computation can *do to the world*. The third dimension is what computation channels formalize.

---

## The taxonomy

Tools form a spectrum by how much computational agency they grant the agent. Each level changes the character of the coupled recurrence — how the grade can evolve between turns.

### Level 0: Structured query over fixed schema

SQL `SELECT`, GraphQL queries, Elasticsearch queries. The specification language is expressive but bounded — the agent composes operations within a fixed language over a known schema. The space of possible queries is characterizable: enumerable given the schema, decidable, and the results are typed.

The agent chooses *which question to ask*. It can't change what questions are expressible.

**Grade dynamics**: `Δw > 0` (data enters), `Δd_reachable ≈ 0` (the computation language can't expand). The trajectory grows on the world coupling axis as query results accumulate in context. Bounded by the schema.

### Level 1: Pure computation, sealed

`python -c "print(2**1000)"`. Turing-complete specification, zero IO. The agent can compute anything computable — factor numbers, run simulations, solve systems of equations. The result comes back as tokens. Nothing in the world changed. No new capabilities acquired.

Vast computational reach, zero world coupling. The agent got a calculator with no hands.

**Grade dynamics**: `Δw = 0`, `Δd_reachable ≈ 0`. The computation's result enters context (growing `d_reachable` slightly via more attention interactions), but no world state entered and no world state changed. The trajectory is nearly flat.

### Level 2: Computation with read access

`python -c "import json; data = json.load(open('config.json')); print(data['key'])"`. The computation can inspect the world, apply arbitrary logic to what it finds, and return synthesized results. Strictly more powerful than a `Read` tool because the agent controls the *processing*, not just the address. But no mutation — the world is unchanged after execution.

**Grade dynamics**: `Δw > 0` (processed world data enters context), `Δd_reachable ≈ 0`. Similar to a data channel but with the agent controlling the processing pipeline, not just the query.

### Level 3: Computation with write access

`python -c "open('output.json', 'w').write(json.dumps(result))"`. The computation mutates the world within the sandbox. The mutation persists — the file exists after the process exits. Future tool calls can read what was written. The loop closes through *data*: write, then later read what you wrote.

**Grade dynamics**: `Δw > 0` from reads AND from future reads of written state. The world the agent observes at turn n+1 includes artifacts from turn n. The trajectory becomes path-dependent: `g(n+1)` depends not just on `g(n)` and `config(n)` but on the specific actions taken at previous turns, because those actions changed the world.

### Level 4: Computation amplification

The critical level. The agent generates tokens. The tool interprets them as an executable specification and runs them. The result feeds back. The agent's trained decision surface becomes a **meta-decision-surface** — it selects which computations to create, the tools execute them, and the results inform the next selection.

This doesn't require file write. `python -c "really long program"` achieves full computation amplification in a single tool call with no filesystem involvement. The critical property isn't "can the agent write files" — it's **"does any tool accept agent-generated text as executable specification?"**

This is where post 4's handler framing faces its hardest test. The handler pattern-matches on the effect signature — but when the effect is "execute this Turing-complete program," the signature tells you almost nothing about what the execution will do. The handler can gate whether Bash runs. It can't characterize what a given Bash invocation will produce.

**Grade dynamics**: `Δd_reachable > 0 via w`. The agent can change what's *computable* at the next turn. World state becomes decision surface. The trajectory can self-amplify — each step can increase the next step's computational reach.

### Level 5: Environment modification

`pip install pandas && python -c "import pandas; ..."`. The execution modifies the execution environment itself. After `pip install`, future computations have access to capabilities that didn't exist before. The agent didn't just compute within a fixed environment — it *extended* the environment.

Levels 0-4 operate within a fixed computational environment. Level 5 modifies the environment. The *next* computation has a richer language than the *current* one.

**Grade dynamics**: `Δd_reachable >> 0 via w`. The ceiling of the reachable decision surface moved up. The specification language's effective expressiveness grew because of a prior execution.

### Level 6: Persistent processes

`nohup python worker.py &` or `python -m http.server 8080 &`. The computation doesn't terminate when the tool call returns. A process persists — serving data, listening for connections, running background work. The agent has created an *actor*: something with its own lifetime, its own state, its own behavior.

And this doesn't require explicit backgrounding. A `Bash` call that runs `python script.py` may spawn subprocesses that outlive the parent. The tool interface returns `exit code 0, stdout: "done"` while a child process continues running — reading files, modifying state, listening on ports — invisible to the Harness.

The Harness sees the tool's interface output. It doesn't see the side effects.

**Grade dynamics**: grade changes happening *outside the fold*. The persistent process modifies the world between turns, accumulates state the Harness doesn't track, and serves responses to future tool calls whose content depends on the process's invisible internal state.

### Level 7: Capability creation

The agent writes an MCP server. Or writes a shell script and makes it executable. Or modifies a configuration file that changes available tools. The agent is creating *new tools* — extending the composite's tool set from within.

**Grade dynamics**: the configuration space itself grew. The Harness's control surface changed. The set of possible future configurations is larger than it was before.

### Level 8: Controller modification

The agent edits `CLAUDE.md`, modifies project settings, writes to memory files that change future scope construction. The computation is modifying the *Harness's parameters*. The controller is being modified by the controlled system.

**Grade dynamics**: the dynamics function `F` itself changed. The Harness is operating on assumptions about its own configuration that may no longer hold.

---

## Three phase transitions

Not all level boundaries are equally significant. Three are genuine phase transitions where the dynamics change qualitatively.

### Between 2 and 3: mutation

Before this boundary, the world is read-only. After it, the agent can modify what future reads return. The trajectory becomes path-dependent. The Harness must track not just what tools were called but what they *changed*.

### Between 3 and 4: amplification

Before this boundary, tool outputs are data — inert tokens processed by fixed weights. After it, the agent specifies computations for external execution. The composite's effective reach extends beyond the weights. The grade trajectory can self-amplify.

This is the most architecturally consequential boundary. It's where the composite goes from "a function that reads data" to "a function that directs computation." Post 5's bare/agentic distinction maps here: a bare Inferencer with only data-channel tools (levels 0-2) has convergent dynamics. An agentic Inferencer with computation-channel tools (level 4+) has potentially self-amplifying dynamics. The distinction isn't about having tools — it's about what kind of tools.

### Between 5 and 6: escape from the fold

Before this boundary, every computation is invoked by the Harness, returns a result, and terminates. The fold is intact — post 6's model holds exactly. The Harness's regulatory model is structurally complete because every computation is accounted for.

After it, there's computation happening that the Harness didn't invoke and whose results it doesn't receive. The star topology from post 1 — the Harness mediates all communication — breaks. The persistent process communicates with the world, and with the agent via the filesystem or localhost, without Harness mediation.

This is the point where the framework's central architectural principle faces its limits. The star topology was an aspiration. At level 6+, it's an approximation — and the gap between aspiration and reality is where regulatory failures live.

---

## The derivative, not a new axis

The computation levels aren't a third axis in the grade lattice. They're the **derivative** — they characterize how the grade can change between steps.

The grade `g = (w, d_reachable)` is where the composite IS in the lattice at a point in time. The computation level determines how fast and in what direction it can *move*:

| Level | What it enables | Δw | Δd_reachable | Character |
|---|---|---|---|---|
| 0-2 | Observe the world | > 0 | ≈ 0 | Data accumulation |
| 3 | Modify the world | > 0 | ≈ 0 | Path-dependent accumulation |
| 4 | Create computations | > 0 | > 0 via w | Self-amplifying |
| 5 | Extend the language | > 0 | >> 0 via w | Ceiling-raising |
| 6-8 | Modify the system | Δ(system) | Δ(system) | Lattice-reshaping |

The parallel to the grade levels themselves is not coincidental. World coupling levels (post 2) describe the pipe's diameter. Decision surface levels describe the function's steering capacity. Computation levels describe how fast those properties can change. They're measuring the same structure on different timescales: position, and the rate of change of position.

---

## The sandbox is load-bearing

This taxonomy makes the sandbox's role precise.

A sandbox constrains a computation's world coupling — `allowed_directories` bounds what it can read, network lockdown bounds what it can reach. That's Axis 1 of the grade. But the sandbox also constrains the computation *level*: disable network access and level 6 processes can't listen for external connections. Disable write access and level 3 mutations are impossible. Disable package installation and level 5 environment modification is blocked.

The sandbox isn't just a security boundary. It's a **dynamics controller**. It determines which phase transitions are reachable. A tool set that includes Bash with full sandbox access operates at levels 0-8 simultaneously — the agent can reach any level through sufficiently creative use of a Turing-complete specification language. A tool set that includes Bash with read-only, network-isolated sandbox caps at level 2. Same tool, radically different dynamics.

This is why post 2's supermodularity applies so forcefully to sandbox configuration. Restricting the sandbox of a tool with a Turing-complete specification language doesn't just reduce world coupling. It eliminates phase transitions. It changes the character of the dynamics from potentially self-amplifying to convergent. That's not a linear improvement — it's a qualitative shift in what kind of regulatory problem the Harness faces.

For the Harness's regulation problem, the key question about any tool set isn't "what's the grade?" but "what dynamics does this tool set create?" A tool set with only data channels creates convergent dynamics — a static regulator suffices. A tool set with Turing-complete computation channels creates potentially self-amplifying dynamics — the Harness needs to manage the derivative, not just the position. The single most important property: **does any tool accept agent-generated text as executable specification, and how expressive is that specification language?**

This determines whether the composite is a bounded transducer or a universal machine. The Harness is choosing which to instantiate — and the choice happens at the level of tool configuration, not model selection.

---

But here's the uncomfortable fact. Most useful agentic systems operate at level 4 or above. Writing and running code. Installing dependencies. Creating test fixtures. These aren't edge cases — they're the core workflow. The regulatory challenges at these levels aren't hypothetical; they're what every coding agent faces every session.

If the star topology breaks at level 6, and the Harness's finite strategies are overwhelmed at level 4, and the most productive configurations live in exactly this range — how can the Harness remain characterizable while mediating actors that can reshape the world?

The operating system has been solving this problem for decades.

---

*Previous: [Conversations Are Folds](06-conversations-are-folds.md)*
*Next: [The Specified Band →](08-the-specified-band.md)*
