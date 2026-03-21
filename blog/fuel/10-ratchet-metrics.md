# Ratchet Metrics

*If you can't measure the ratchet, you can't manage it. If you can't manage it, you're just hoping.*

---

## The instrument panel

Nine posts in this series described a system that learns from its own failures. The failure stream feeds the ratchet. The ratchet promotes patterns from computation channels to data channels. The controller watches counters and switches modes. The organizational star distributes these ideas across teams.

All of that machinery runs on one assumption: you can see what's happening.

This post builds the instrument panel. Six metrics, each connected to a specific concept from the series. For each metric: what it measures, what healthy looks like, what sick looks like, and what to do about it. Then the DuckDB queries that extract them from your conversation logs.

No metric here requires trained judgment to compute. Every one is arithmetic over the tool call log, the failure stream, and the promotion history. That's the point. The instrument panel is specified — Layer 0 through Layer 3, no computation channels — because the thing monitoring your system cannot itself be the thing you're trying to monitor.

---

## 1. Ratchet rate

**What it measures:** How fast computation channels are closing.

The ratchet rate is the number of Stage 2 promotions per period — week, month, quarter, whatever cadence fits your team. Each promotion is a pattern that crossed from exploration to infrastructure: a bash command that became a structured tool, an ad-hoc query that became a validated definition, a bespoke process that became a template.

Post 2 — [The Two-Stage Turn](02-the-two-stage-turn.md) — described the mechanism. Stage 1 is discovery: the agent explores, converges on patterns, validates them through repeated use. Stage 2 is crystallization: you observe the pattern, encode it in a structured tool, and close the computation channel. The ratchet rate counts Stage 2 events.

**Healthy:** Steady positive rate. Not necessarily high — three promotions per week is excellent if they're the right three. The rate reflects how actively you're observing the failure stream and acting on what you find.

**Stalling:** Rate drops to zero. Two possible causes. First, you're not looking — the failure stream is producing ratchet candidates, but nobody is reviewing the repeated-pattern queries and making promotion decisions. This is an attention problem, not a system problem. Second, you're looking but not finding — the failure stream has shifted composition (more permission denials, fewer repeated patterns), which means the system's bottleneck has moved. Check the failure stream composition metric below.

**Saturating:** Rate drops because most common patterns are already promoted. The frontier has shrunk. The agent's tool calls are overwhelmingly data-channel (structured tools, validated queries) and the remaining computation-channel calls are genuinely novel — tasks where trained judgment belongs.

That's success. The ratchet was always supposed to slow down. A system where the ratchet rate is zero because there's nothing left to promote is a system that has internalized its own usage patterns into infrastructure. The metric tells you whether the slowdown is earned (saturation) or neglected (stalling). The failure stream composition distinguishes the two.

---

## 2. Trust gap

**What it measures:** The distance between what the agent can reach and what you expect it to reach.

Post 1 — [Fuel](01-fuel.md) — introduced the trust gap as a learning surface. Too narrow and the system produces no failures, therefore no data, therefore no improvement. Too wide and the agent is probing boundaries that carry real risk. The trust gap metric quantifies where you are on that spectrum.

Two sub-metrics.

### Boundary hit rate

What fraction of tool calls hit a boundary that a specified rule could have prevented? This counts the times the agent attempted something, got denied, and the denial was predictable from the configuration — the constraint existed, the agent just didn't know about it.

High boundary hit rate means the agent is spending inference probing constraints that are invisible to it. The fix is constraint visibility: tell the agent what it can't do, so it stops discovering the boundaries empirically at full inference cost.

Low boundary hit rate means either the constraints are visible (good) or there aren't enough constraints (check the failure stream for what the agent is doing unchecked).

### Observer gap rate

This one comes from the experimental program. A specified observer — DuckDB queries, file diffing, schema comparison — checks the agent's work after the fact. The observer gap rate is how often the observer detects a divergence between what the agent claimed to do and what actually happened.

The agent says it updated three files. The observer diffs and finds four files changed. The agent says the tests pass. The observer runs the tests and finds two failures. The agent says the output matches the specification. The observer compares and finds a discrepancy.

Each divergence is a trust gap made visible. A zero observer gap rate means either the agent is perfectly reliable (unlikely) or the observer isn't checking the right things (more likely). A high observer gap rate means the review mode from Post 4 — [The Failure-Driven Controller](04-the-failure-driven-controller.md) — isn't catching what it should, or isn't being triggered often enough.

**Healthy:** Low boundary hit rate (constraints are visible), non-zero but declining observer gap rate (the observer is catching things, and the things it catches are driving configuration improvements that reduce future divergences).

**Sick:** High boundary hit rate (the agent is wasting inference on invisible constraints) or zero observer gap rate sustained over many sessions (you're not checking enough).

---

## 3. Failure stream composition

**What it measures:** Where the system is stuck.

Post 1 classified failures into five categories: permission denials, repeated patterns, timeouts, success rate decay, and scope exhaustion. The composition — what fraction falls into each category — is a diagnostic. It tells you which part of the system needs attention next.

Read the distribution. The dominant category is the bottleneck.

**Mostly permission denials:** Boundaries are misconfigured. Either too tight (the agent needs capabilities you haven't granted) or too opaque (the agent can't see the boundaries, so it discovers them by collision). Check whether the denials are justified — does the agent actually need the capability? If yes, open the boundary. If no, make the constraint visible.

**Mostly repeated patterns:** The ratchet is not turning. These are promotions waiting to happen. The agent has converged on bash patterns that work reliably. Each one is a structured tool you haven't built yet. This is the healthiest failure composition, paradoxically — it means your biggest cost center is also your clearest roadmap. Promote the top three patterns and re-measure.

**Mostly timeouts:** Wrong tools for the task size. The agent is using synchronous tools on large inputs, running full test suites when it needs targeted tests, or searching massive directory trees with tools designed for small scopes. Add scoped alternatives — mode-specific tools that match the problem size.

**Mostly success rate decay:** Context management needs work. The agent starts strong and degrades as the conversation grows. The context is filling with noise — old tool results, superseded information, dead-end explorations that still occupy token budget. The fix is structural: compaction, mode switches with structured handoffs, or shorter conversation lifetimes with better task decomposition.

**Mostly scope exhaustion:** Tasks are too large for single contexts. The decomposition is too coarse. Break tasks into subtasks, each with its own context and structured handoff. Post 4's controller should be triggering compaction or handoff before scope exhaustion becomes the dominant failure mode.

**The healthy composition:** Most failures are in the "repeated pattern" category. Those are ratchet candidates — fuel waiting to burn. The system is failing in the most productive way possible.

**The sick composition:** Permission denials and timeouts dominate. The system is fighting its own boundaries and using the wrong tools. Configuration is mismatched to the task. Step back and fix the sandbox before optimizing anything else.

---

## 4. Mode utilization

**What it measures:** Where time goes.

Post 4 defined four modes: debug, implementation, test development, and review. Each mode has a different trust profile and a different purpose. The mode utilization metric measures how much time the system spends in each mode — and what that distribution reveals about system health.

**High debug time:** Implementation mode is producing too many failures. The agent is writing code that fails tests, then spending extended cycles in debug mode diagnosing the failures. The tools available in implementation mode may be wrong — not enough structure, not enough constraint visibility, not enough validated patterns. Or the task decomposition is too coarse, and the agent is attempting changes too large to reason about in a single pass.

**Low review time:** Reviews are being skipped. The observer gap is growing silently. Every session that skips review mode is a session where divergences between agent claims and actual outcomes go undetected. The trust gap widens without anyone noticing. If review time is consistently below 10% of total session time, the controller's review triggers need adjustment.

**High plan time:** Task decomposition is too coarse. The agent is spending excessive time planning because the tasks are too large or too ambiguous to execute directly. Break the work into smaller, more concrete subtasks. Planning should be a small fraction of total time — the structure should come from the task definition and the mode configuration, not from extended agent deliberation.

**Healthy distribution:** Most time in implementation and test development, moderate time in debug (some failures are expected — that's learning), consistent time in review (non-negotiable — this is where the observer gap gets measured).

---

## 5. Computation channel fraction

**What it measures:** The big picture.

Post 0 — [The Ratchet Review](00-ratchet-review.md) — established the computation channel boundary as the central divide. Below it, the agent picks from a menu. Above it, the agent writes new menu items. Below it, the orchestrator can vet every action. Above it, the orchestrator is pattern-matching on command strings and hoping.

The computation channel fraction is the ratio of system interactions that go through computation channels (Level 4+ — bash, code generation, freeform text-to-action) versus data channels (Level 0-3 — structured tool calls, validated queries, schema-constrained operations).

The ratchet pushes this ratio toward data channels. Every promotion converts a computation-channel interaction into a data-channel interaction. Over time, the fraction should decline. If it doesn't — if the computation channel fraction is stable or growing — capability is increasing without structure. The agent is doing more things through bash, not fewer. The ratchet isn't turning, or new tasks are introducing computation channels faster than old patterns get promoted.

**Healthy:** Declining computation channel fraction over weeks and months. The denominator (total interactions) may grow, but the numerator (computation-channel interactions) should grow slower or shrink.

**Sick:** Stable or increasing computation channel fraction. The system is getting more powerful without getting more structured. Each new capability arrives as a bash pattern rather than a promoted tool. The trust gap is widening in the place where it matters most — the uncharacterizable space above the computation boundary.

**What to do:** Go back to the repeated patterns query. The computation-channel calls that appear most frequently with the highest success rates are the promotions you're missing. Build them. Close the channels.

---

## 6. Self-service ratio

**What it measures:** For data platforms specifically, how much access goes through crystallized infrastructure versus ad-hoc queries.

This metric applies to teams that run data platforms — analytics, reporting, ML feature stores, business intelligence. The self-service ratio is the fraction of data access that goes through validated definitions (documented metrics, tested queries, structured dashboards) versus ad-hoc queries (raw SQL against production tables, one-off extracts, bespoke notebooks).

Each validated definition is a ratchet promotion. Somebody wrote an ad-hoc query. It worked. It got reused. Eventually it was promoted to a validated, tested, documented metric. The self-service ratio counts how much of the data platform's traffic flows through those promotions versus through the raw, unvalidated channel.

**Healthy:** Self-service ratio increases monotonically. More access goes through validated definitions over time. The ad-hoc channel still exists — it's where new queries get explored — but it's a smaller fraction of total traffic.

**Plateau:** The ratio stops increasing. The ratchet has stalled. Ad-hoc queries are accumulating without being promoted. Either the promotion process is too expensive (too much ceremony to validate a definition) or the observation step is missing (nobody is watching the ad-hoc query logs to identify patterns worth promoting).

**Declining:** The ratio is dropping. Validated definitions exist but people are bypassing them — writing ad-hoc queries for things that already have structured definitions. This usually means the validated definitions are hard to find, hard to use, or don't match what people actually need. The ratchet turned, but the promoted tools aren't being adopted.

---

## Code ships: the dashboard

These DuckDB queries extract all six metrics from the conversation logs and failure stream data established in Post 1. They assume the `tool_calls` view from Post 1 exists, plus a `tool_promotions` table that tracks when patterns are promoted to structured tools, and a `mode_transitions` table that logs mode changes.

### Schema setup

```sql
-- Promotion tracking: log each time a pattern gets promoted
CREATE TABLE IF NOT EXISTS tool_promotions (
    promotion_id INTEGER PRIMARY KEY,
    pattern_description VARCHAR,     -- what the bash pattern was
    tool_name VARCHAR,               -- what it became
    promoted_at TIMESTAMP,           -- when the promotion happened
    source_frequency INTEGER,        -- how often the pattern appeared
    source_success_rate DOUBLE       -- success rate before promotion
);

-- Mode transitions: log each mode change with timing
CREATE TABLE IF NOT EXISTS mode_transitions (
    transition_id INTEGER PRIMARY KEY,
    task_id VARCHAR,
    from_mode VARCHAR,
    to_mode VARCHAR,
    triggered_by VARCHAR,            -- which counter triggered the switch
    transitioned_at TIMESTAMP,
    duration_ms BIGINT               -- how long the previous mode lasted
);

-- Observer checks: log each review-mode verification
CREATE TABLE IF NOT EXISTS observer_checks (
    check_id INTEGER PRIMARY KEY,
    task_id VARCHAR,
    check_type VARCHAR,              -- 'file_diff', 'test_run', 'schema_compare'
    agent_claim VARCHAR,
    observed_result VARCHAR,
    divergence BOOLEAN,
    checked_at TIMESTAMP
);
```

### 1. Ratchet rate over time

```sql
-- How fast is the ratchet turning?
-- Each row is a week. Each count is a promotion.
SELECT date_trunc('week', promoted_at) as week,
       count(*) as promotions,
       round(avg(source_frequency), 0) as avg_pattern_frequency,
       round(avg(source_success_rate), 2) as avg_source_success_rate
FROM tool_promotions
GROUP BY 1
ORDER BY 1;
```

Interpretation: A week with zero promotions is a week the ratchet didn't turn. Check whether that's saturation (the repeated patterns query returns few candidates) or neglect (the candidates are there but nobody acted).

### 2. Failure stream composition with trend

```sql
-- Reuse the classification from Post 1, add weekly trend
WITH classified AS (
    SELECT task_id,
           turn_number,
           tool,
           success,
           duration_ms,
           timestamp,
           CASE
               WHEN NOT success AND (
                   result_preview ILIKE '%permission%'
                   OR result_preview ILIKE '%denied%'
                   OR result_preview ILIKE '%EACCES%'
               ) THEN 'permission_denial'
               WHEN NOT success AND duration_ms > 30000
                   THEN 'timeout'
               WHEN tool IN ('Bash', 'bash') AND success
                   AND EXISTS (
                       SELECT 1 FROM tool_calls t2
                       WHERE t2.task_id = tool_calls.task_id
                         AND t2.tool = tool_calls.tool
                         AND t2.arguments = tool_calls.arguments
                         AND t2.turn_number != tool_calls.turn_number
                   ) THEN 'repeated_pattern'
               WHEN NOT success
                   THEN 'other_failure'
               ELSE 'success'
           END as category
    FROM tool_calls
)
SELECT date_trunc('week', timestamp) as week,
       category,
       count(*) as count,
       round(100.0 * count(*) /
           sum(count(*)) OVER (PARTITION BY date_trunc('week', timestamp)),
           1) as pct
FROM classified
GROUP BY 1, 2
ORDER BY 1, count DESC;
```

Interpretation: Watch how the composition shifts week over week. After a promotion, the `repeated_pattern` count for that specific pattern should drop to zero. If the overall `repeated_pattern` percentage is climbing, the ratchet is falling behind the rate at which the agent discovers new patterns.

### 3. Mode utilization

```sql
-- Where does time go? Percentage of session time in each mode.
SELECT mode,
       count(*) as transitions_into,
       sum(duration_ms) / 1000.0 as total_seconds,
       round(100.0 * sum(duration_ms) /
           sum(sum(duration_ms)) OVER (),
           1) as pct_of_total,
       round(avg(duration_ms) / 1000.0, 1) as avg_seconds_per_stay
FROM (
    SELECT to_mode as mode,
           duration_ms
    FROM mode_transitions
    WHERE duration_ms IS NOT NULL
) sub
GROUP BY mode
ORDER BY total_seconds DESC;
```

Interpretation: If debug mode exceeds 40% of total time, implementation tooling needs work. If review mode is below 10%, you're accumulating unverified trust. If plan mode exceeds 20%, tasks need decomposition before they reach the agent.

### 4. Computation channel fraction

```sql
-- The big picture: what fraction of work goes through
-- computation channels vs data channels?
WITH channel_classified AS (
    SELECT date_trunc('week', timestamp) as week,
           CASE
               WHEN tool IN ('Bash', 'bash', 'Execute', 'shell')
                   THEN 'computation'
               WHEN tool IN ('Read', 'Write', 'Edit', 'Grep', 'Glob',
                             'file_read', 'file_write', 'search')
                   THEN 'data'
               ELSE 'data'  -- structured tools default to data channel
           END as channel_type
    FROM tool_calls
)
SELECT week,
       channel_type,
       count(*) as calls,
       round(100.0 * count(*) /
           sum(count(*)) OVER (PARTITION BY week),
           1) as pct
FROM channel_classified
GROUP BY 1, 2
ORDER BY 1, channel_type;
```

Interpretation: The `computation` percentage should decline over time. If it's flat, promotions aren't keeping pace with new computation-channel usage. Plot this weekly and look for the trend line.

### 5. Trust gap: observer divergence rate

```sql
-- How often does the observer catch something the agent got wrong?
SELECT date_trunc('week', checked_at) as week,
       check_type,
       count(*) as total_checks,
       sum(CASE WHEN divergence THEN 1 ELSE 0 END) as divergences,
       round(100.0 * sum(CASE WHEN divergence THEN 1 ELSE 0 END) /
           count(*), 1) as divergence_rate_pct
FROM observer_checks
GROUP BY 1, 2
ORDER BY 1, check_type;
```

Interpretation: A divergence rate above 20% means the agent is unreliable and review mode needs to run more frequently. A divergence rate of exactly 0% over many weeks means you're probably not checking the right things — expand the observer's check types.

### 6. Self-service ratio (for data platforms)

```sql
-- What fraction of data access goes through validated definitions
-- vs ad-hoc queries?
-- Assumes a query_log table with a 'query_type' column
-- ('validated' or 'ad_hoc') and a timestamp
SELECT date_trunc('month', executed_at) as month,
       count(*) FILTER (WHERE query_type = 'validated') as validated_queries,
       count(*) FILTER (WHERE query_type = 'ad_hoc') as ad_hoc_queries,
       round(100.0 * count(*) FILTER (WHERE query_type = 'validated') /
           count(*), 1) as self_service_pct
FROM query_log
GROUP BY 1
ORDER BY 1;
```

Interpretation: `self_service_pct` should be monotonically increasing. A plateau means the promotion pipeline has stalled. A decline means validated definitions aren't meeting user needs — go talk to the people writing ad-hoc queries and find out why.

---

## Reading the dashboard

Run these queries weekly. The numbers tell you three things.

**Where to look.** The failure stream composition points to the bottleneck. The dominant failure category is the thing to fix next. Not the thing that's most interesting, not the thing that's most technically challenging — the thing that's burning the most inference.

**Whether the ratchet is turning.** The ratchet rate, the computation channel fraction, and the self-service ratio all measure the same underlying process from different angles. If all three are moving in the right direction — promotions happening, computation fraction declining, self-service increasing — the system is learning from its own operation. If any of them stalls, find out why before optimizing anything else.

**Whether you can trust the system.** The trust gap metrics — boundary hit rate, observer divergence rate — tell you how much of the system's behavior you can actually verify. A system with great ratchet rate but no observer checks is a system that's getting more powerful without getting more verified. That's the wrong direction.

The metrics interact. A high ratchet rate should produce a declining computation channel fraction. A healthy failure stream composition (mostly repeated patterns) should correlate with a positive ratchet rate (those patterns are getting promoted). A declining observer divergence rate should correlate with increasing self-service ratio (validated definitions are more reliable than ad-hoc queries).

When the metrics disagree — high ratchet rate but stable computation channel fraction, for example — something is wrong. Either the promotions aren't being adopted (the tools got built but the agent isn't using them) or new computation channels are opening as fast as old ones close (new tasks are outpacing the ratchet). The disagreement is the diagnostic.

---

## The metrics tell you where the ratchet should turn next

This series started with a claim: your system will teach itself to need less AI over time, if you instrument it to learn from its own failures.

The failures are the fuel — [Post 1](01-fuel.md). The two-stage mechanism converts exploration into infrastructure — [Post 2](02-the-two-stage-turn.md). The placement of autonomy determines what the system can learn — [Post 3](03-where-the-failures-live.md). The controller watches counters and switches modes — [Post 4](04-the-failure-driven-controller.md). And the organizational star distributes the ratchet across teams — [Post 9](09-the-organizational-star.md).

The metrics close the loop. They tell you whether the ratchet is turning, how fast, and where it should turn next. They convert the qualitative question — "is the system getting better?" — into arithmetic. Numbers you can track. Trends you can plot. Thresholds you can set.

The instrument panel is itself a specified observer. It runs at Layer 0 through Layer 3. No trained judgment in the monitoring pipeline. SQL over structured logs. The thing that measures the system is the simplest thing in the system — because the thing that measures the system must be the thing you trust most.

Build the dashboard. Run it weekly. Let the numbers tell you what to build next.

The ratchet turns when you look at it.

---

*Previously: [The Organizational Star](09-the-organizational-star.md)*
*Back to the beginning: [The Ratchet Review](00-ratchet-review.md)*
*For the formal treatment: [The Ma of Multi-Agent Systems](../ma/00-intro.md)*
*For the experimental program: [experiments/](../../experiments/)*
