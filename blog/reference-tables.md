# Reference Tables

*A unified view of the classification schemes used across the series.*

---

## The grade lattice

Every actor, tool, and composite has a **grade** — a position in a two-dimensional product lattice measuring how hard it is to characterize from outside.

### W axis: World coupling

How much of the world can influence the computation.

| Level | Name | IO type | Actor example | Tool example |
|---|---|---|---|---|
| 0 | Sealed | `IO_null` | — | Pure function, calculator |
| 1 | Pinhole | `IO_channel` | Temperature sensor | `Read(path)` — single address |
| 2 | Scoped | `IO_sandbox` | Sandboxed agent | `Glob`, `Grep` — bounded filesystem |
| 3 | Broad | `IO_filesystem` | Agent with file + network | Network-enabled tool |
| 4 | Open | `IO` | OS kernel, Principal | Unrestricted `Bash` |

For tools specifically, the W axis is grounded in the **effect signature**: `Pure < FileRead < FileWrite < Network < ProcessSpawn < ArbitrarySyscalls`.

### D axis: Decision surface

What fills the space between input and output. One axis — actors and tools live on it together.

| Level | Name | Characterizability | Actor example | Tool example |
|---|---|---|---|---|
| 0 | Literal | Trivially readable | Executor | `echo "hello"`, constant |
| 1 | Specified | Readable with effort | Harness, OS kernel | SQL query, `Read`, `Glob` |
| 2 | Configured | Readable given the config | Parameterized Harness | Template engine |
| 3 | Trained | Opaque — must probe | LLM (Inferencer) | — |
| 4 | Evolved | Opaque + self-modifying | RL agent, Principal | — |

Tools only reach D = specified or below — a tool's mapping from input to output is always readable. But **an agent using a tool is always less specified than the tool alone** — the agent chooses whether and how to use the tool, which means the composite's internal D is at least the agent's D (trained). The question is what D the tool *exposes at the interface*:

| Tool type | Tool's own D | Internal D (agent + tool) | Interface D (what the world sees) | Why |
|---|---|---|---|---|
| **Data channel** | ≤ specified | trained (agent chooses what to query) | **≤ specified** | Tool is a co-domain funnel — compresses the agent's trained D through a characterized interface |
| **Computation channel** | ≤ specified | trained (agent chooses what to execute) | **trained** | Tool is transparent — the agent's opaque decision surface passes through to the world |

The **3→4 phase transition** is the point where the interface D jumps from specified to trained. The agent was always trained internally — what changes is that the tool stops compressing the output. That's why Rice's theorem kicks in: the Harness is now seeing the agent's trained decision surface, not a specified projection of it.

### Where actors live

```
                    World coupling
                    sealed → → → → → → → → open

Decision  evolved   |                        | Principal (human)
surface   trained   |              Inferencer|
          configured|                        |
          specified | Harness     OS/Runtime | ← THE SPECIFIED BAND
          literal   | Executor               |
```

The **specified band** (D = specified) runs across the full W axis. Characterization difficulty is supermodular: `χ(w, d) = I(w) · log P(d)`. The cross-term doesn't activate in the specified band because `log P(specified)` is bounded.

---

## The nine-level taxonomy

Not a third axis in the lattice — it characterizes the **derivative**: what mechanism can expand d_reachable between turns.

| Level | What expands d_reachable | Interface D | What's contained | Character |
|---|---|---|---|---|
| 0 | Nothing (sealed) | specified | Everything | Flat |
| 1 | Context (data accumulates) | specified | Everything | Accumulation |
| 2 | Context (processed data) | specified | Everything | Richer accumulation |
| 3 | Persistent state (written artifacts) | specified | Everything | Path-dependent |
| **4** | **Feedback loops (compute → result → compute)** | **trained** | **Computation within current env** | **Self-amplifying** |
| 5 | The specification language (new libraries) | trained | Tool call lifetime | Ceiling-raising |
| 6 | The tool surface (new tools) | trained | The environment | Config-reshaping |
| 7 | Unobserved channels | trained | The Harness's invocation model | Fold escape |
| 8 | The dynamics function | trained | Nothing | Dynamics-reshaping |

The bold row is the primary phase transition — where the interface D crosses from specified to trained. The agent was always trained internally; what changes is that the tool stops compressing the output.

Within the computation-channel regime (levels 4-8), each level crosses a containment boundary the previous level couldn't. Level 4 is anything the computation could do in a Docker container with the right volumes mounted — self-contained workflow steps. Level 5 reaches outside (pulling in third-party libraries whose content neither agent nor Harness authored, permanently expanding the space of reachable programs). Levels 6-8 progressively modify the system that runs the computations.

### Three phase transitions

| Transition | What becomes opaque | Axis | The Harness can't answer |
|---|---|---|---|
| 2 → 3 | Accumulated world state | W (effects) | "What has changed since I last looked?" |
| 3 → 4 | Computation semantics | D (specification predicate) | "What will this tool call do?" |
| 6 → 7 | Capability surface | Mediation structure | "What can this system do?" |

Each subsumes the previous.

### Operational granularity within levels 4+

Within the computation-channel regime (composite D = trained), finer distinctions affect how reliably the Harness regains control:

| Class | Termination | Example | Sandbox effect |
|---|---|---|---|
| Bounded | Always, within known time | Bash under cgroups | Resource bounds enforce this |
| Total | Always, time may be impractical | Ackermann function | — |
| Partial | Not guaranteed | Unrestricted Bash | Resource bounds convert partial → bounded |

The sandbox doesn't change the composite D (still trained, Rice still applies). It bounds the *consequences* of semantic opacity.

---

## The configuration invariant

Whether the system stays within bounds — a product-space property of (W, D).

| Interface D | Effects (W) | Invariant | Why |
|---|---|---|---|
| ≤ specified | Read-only | **Holds** | Characterized output, no world change |
| ≤ specified | Read-write | **Can drift** | Mutations are characterizable but accumulate |
| trained | Read-only | **Holds** | Opaque but can't change the world |
| trained | Read-write | **Can break** | Semantic opacity + world mutation |

The **sandbox** restores the invariant by bounding consequences on both axes — effect restriction (W) and resource bounds (operational control) — without resolving semantic opacity.

---

## Regulation

### Three layers (the OS pattern)

| Layer | What it does | Stays in specified band? |
|---|---|---|
| 1. Constraint | Bounds what's *possible* (sandbox, permissions) | Yes — it's a boundary, not an actor |
| 2. Observation | Reports what *happened* (logging, monitoring) | Yes — specified reporting |
| 3. Policy | Decides what's *allowed* (rules over observed state) | Yes — specified rules |

### The trust surface

```
level_theoretical(t)  ≥  level_sandboxed(t, S)  ≥  level_effective(t, A)
```

The gap between sandboxed and effective is where regulation relies on training rather than specification. The specified band says: regulate based on `level_sandboxed`, not `level_effective`.

---

## How the schemes relate

```
┌─────────────────────── GRADE LATTICE (W × D) ───────────────────────────┐
│                                                                         │
│  ┌──── W: World Coupling ──────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  Three views of the same axis:                                  │    │
│  │                                                                 │    │
│  │  Pipe diameter     Effect signature     Containment boundary    │    │
│  │  (grades actors)   (grades tools)       (generates taxonomy)    │    │
│  │  ───────────────   ────────────────     ──────────────────────  │    │
│  │  sealed            Pure                 nothing           → 0   │    │
│  │  pinhole           FileRead             data (read)       → 1,2 │    │
│  │  scoped            FileWrite            data (write)      → 3   │    │
│  │                                         ─── D flips here ── 4   │    │
│  │                                         current env (self-      │    │
│  │                                         contained execution)    │    │
│  │  broad             Network              environment       → 5   │    │
│  │                                         (third-party artifacts) │    │
│  │                    ProcessSpawn         tool surface      → 6   │    │
│  │  open              ArbitrarySyscalls    Harness's model   → 7   │    │
│  │                                         the controller    → 8   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ×                                          │
│  ┌──── D: Decision Surface ────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  One axis — actors and tools live on it together:               │    │
│  │                                                                 │    │
│  │  evolved ──┐                                                    │    │
│  │  trained   ├── agents live here                                 │    │
│  │  ── ── ── ─┘── ── ── ── ── ── ── ──                            │    │
│  │  configured ┐                                                   │    │
│  │  specified  ├── tools live here (always readable)               │    │
│  │  literal  ──┘                                                   │    │
│  │                                                                 │    │
│  │  THE INTERPLAY — agent + tool composite:                        │    │
│  │  ┌────────────────────────────────────────────────────────┐     │    │
│  │  │  internal D  = trained  (always — agent chooses)       │     │    │
│  │  │                                                        │     │    │
│  │  │  interface D depends on tool type:                     │     │    │
│  │  │    data channel:        specified  (tool compresses)   │     │    │
│  │  │    computation channel: trained    (tool is transparent)│     │    │
│  │  │                         ↑                              │     │    │
│  │  │    the 3→4 transition: tool stops compressing          │     │    │
│  │  └────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  χ(w, d) = I(w) · log P(d)   supermodular, bounded in specified band   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
              derives        │         derives            derives
        ┌────────────────────┼──────────────────────┐
        │                    │                      │
        ▼                    ▼                      ▼
 ┌──────────────┐   ┌──────────────┐   ┌────────────────┐
 │  NINE-LEVEL  │   │   CONFIG     │   │   REGULATION   │
 │  TAXONOMY    │   │  INVARIANT   │   │    LAYERS      │
 │              │   │              │   │                │
 │ nine ways    │   │ product of   │   │ the OS pattern │
 │ d_reachable  │   │ (W, D):      │   │ for staying in │
 │ can grow:    │   │ when the     │   │ the specified  │
 │              │   │ system can   │   │ band:          │
 │ 0-3: context │   │ break        │   │                │
 │  and state   │   │              │   │ 1. constrain   │
 │  (D=spec'd)  │   │ breaks when: │   │    (bound W)   │
 │              │   │  interface   │   │ 2. observe     │
 │ 4: feedback  │   │  D=trained   │   │    (report)    │
 │  loops       │   │    AND       │   │ 3. policy      │
 │  (D flips)   │   │  W=read-     │   │    (specified  │
 │              │   │  write       │   │    rules)      │
 │ 5-8: what    │   │              │   │                │
 │  the system  │   │              │   │ sandbox =      │
 │  IS changes  │   │              │   │ dynamics       │
 └──────┬───────┘   └──────────────┘   │ controller     │
        │                              └────────────────┘
        │ three phase transitions
        │ (boundary crossings on
        │  three independent axes)
        │
        ├── 2→3: W axis (effects)
        │   "what has changed?"
        │
        ├── 3→4: D axis (specification predicate)
        │   "what will this do?"    ← primary transition
        │
        └── 6→7: mediation structure
            "what can this system do?"
```
