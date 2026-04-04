# The Error That Fixes Itself

*Your past fixes help your future self and your team — automatically, without you doing anything.*

---

## Tuesday, 2 PM

CI fails. blq captures the error:

```
build:run_347:error_891
  File: src/auth/tokens.py
  Function: validate_token
  Line: 47
  Error: TypeError: expected str, got None
  Input: token=None, strict=True
```

A developer looks at it. The fix is obvious — `validate_token` returns `None` on one path instead of raising. They write a pluckit chain:

```javascript
blq.event('build:run_347:error_891')
    .select()
    .replaceWith('return None', 'raise ValueError("invalid")')
    .test('tests/test_auth.py')
    .save('fix: validate_token raises instead of returning None')
```

Five lines. The error event's metadata IS the selector — file, function, line, error text. No manual targeting. `.select()` auto-generates the compound selector from the event data.

The fix takes three minutes. The developer moves on.

---

## What happened underneath

The chain executed. blq captured the trace:

```
event:    build:run_347:error_891
chain:    select → replaceWith → test(pass) → save
diff:     -return None / +raise ValueError("invalid")
result:   pass
```

Agent Riggs sees the trace. It fingerprints the pattern:

```
TypeError:None:validate_token → replaceWith('return None', 'raise ValueError')
```

More abstractly: "a TypeError caused by a function returning None instead of raising gets fixed by replacing the return-None with a raise." The fingerprint captures the error shape and the fix shape, not the specific function.

---

## Thursday, next month

A different module. A different developer. CI fails:

```
build:run_412:error_023
  File: src/api/parsers.py
  Function: parse_header
  Line: 91
  Error: TypeError: expected str, got None
  Input: header=None, required=True
```

Same error shape. Different function, different file, different developer. But the fingerprint matches: `TypeError:None:* → replaceWith('return None', 'raise ...')`.

Riggs recognizes it. Serves the fix from Tier 0 — no model call, no human:

```javascript
blq.event('build:run_412:error_023')
    .select()
    .replaceWith('return None', 'raise TypeError("expected str")')
    .test('tests/test_api.py')
    .save('fix: parse_header raises instead of returning None')
```

The chain executes. Tests pass. The fix lands.

The developer who fixed `validate_token` last month doesn't know their fix just saved someone else twenty minutes. They didn't create a template. They didn't write documentation. They fixed a bug, and the system learned from the fix.

---

## Error events as compound selectors

The key insight: error events from blq and duck_hunt already contain everything a pluckit selector needs.

| Event field | Selector component |
|---|---|
| File path | `source('src/auth/tokens.py')` |
| Function name | `.find('.fn#validate_token')` |
| Line number | `.at_line(47)` |
| Error text | `.containing('return None')` |

The selector for an error can be computed deterministically from the event ID. No model needed to target the fix — only to generate it.

And for batch fixing:

```javascript
blq.run('build:347')
    .events({ type: 'TypeError', pattern: 'expected str, got None' })
    .select()
    .ancestor('.fn')
    .replaceWith('return None', 'raise TypeError("expected str")')
    .test()
    .save('fix: handle None returns causing TypeErrors')
```

A build run's error list becomes a batch of selectors. Every error of the same type gets the same fix. One chain.

---

## The fingerprint ratchet

The ratchet turns on error patterns, not individual errors.

```
First occurrence:
    Error event → human/agent writes pluckit chain → fix → trace stored
    Cost: human time + chain generation (lackpy, 3B, $0)

Second occurrence (same pattern):
    Error event → Riggs matches fingerprint → serves chain from Tier 0
    Cost: $0. No model. No human.

Third, fourth, fifth:
    Same. The fix is a lookup, not a computation.
```

The fingerprint isn't the specific error ("TypeError in validate_token at line 47"). It's the error SHAPE ("TypeError caused by returning None where a value was expected"). The fix isn't specific to validate_token — it's a pattern: replace return-None with a raise.

Riggs promotes when confidence is high: frequency ≥ 5 occurrences, across ≥ 3 sessions, with success rate ≥ 0.8. Below that threshold, the pattern is a candidate — suggested but not automatic. Above it, Tier 0.

---

## The token economics

A pluckit chain is ~50 tokens. The same fix through a frontier model generating raw code is 500-2000 tokens — plus the context window cost of sending the file contents, the error message, the test output.

But the Tier 0 fix is zero tokens. No model call at all. The chain is served from a template, executed locally, verified by tests. The only cost is the CPU time to run the chain and the test suite.

```
First fix (human + lackpy):  ~50 tokens + human time
Second fix (Tier 0):         0 tokens, 0 human time
Every subsequent fix:         0 tokens, 0 human time
```

The first fix is an investment. Every subsequent occurrence is a dividend. And the investment is small — a 5-line chain, not a library or a framework.

---

## What this means

The ratchet has been an abstract mechanism for most of this series. Templates promote. Costs decrease. Systems improve.

This is the concrete version. A specific error. A specific fix. A specific re-occurrence. A specific automatic resolution. The developer's three minutes of work last month is saving twenty minutes this month — and will keep saving them for every future occurrence of that error pattern, across every codebase that uses the same tool suite.

Your past fixes help your future self and your team. Automatically. Without you doing anything.

That's the ratchet. It only turns one direction.

---

```{seealso}
- [Code as a Queryable Material](01-code-as-queryable-material) — The vision for pluckit
- [The pluckit API](03-the-api) — blq integration and compound selectors
- [Training Before Shipping](04-training-before-shipping) — Error fingerprint training data
- [The Tool That Teaches Itself to Disappear](../lackey/03-the-tool-that-teaches-itself-to-disappear) — Template promotion from traces
```
