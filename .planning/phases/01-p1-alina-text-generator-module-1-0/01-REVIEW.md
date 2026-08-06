---
phase: 01-alina-caption-generator
reviewed: 2026-08-06T16:30:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - scripts/alina_textgen.py
findings:
  critical: 0
  major: 2
  minor: 3
  nit: 2
  total: 7
status: issues
---

# Phase 01: Code Review Report

**Reviewed:** 2026-08-06T16:30:00Z
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues

## Summary

Reviewed `scripts/alina_textgen.py` (676 lines, pool-based caption generator, stdlib only) against PLAN 01-01 intent, the SUMMARY's stated contracts, and the modeled pattern in `core/text_generator.py`. All runtime claims verified by execution: pool sizes (5x20/5x12/5x12), platform hashtag counts (8/9/8/3/0), seed reproducibility (`seed=7` twice → identical), and dedup (5 unique). No security vulnerabilities found — pools are static strings printed verbatim to stdout; no subprocess/eval/HTML/file-path usage exists, so no injection vector today (note: when Phase 3 renders these into the web UI DOM, HTML-escape first; currently all strings are HTML-metacharacter-free).

Two substantive defects: (1) the 200-attempt dedup cap makes `batch_generate` deterministically return fewer captions than requested for `count > 200` with no error signal, and (2) seeding via global `random.seed()` mutates the process-wide RNG, which is shared with `core/text_generator.py` and `pipeline/prompt_bank.py` — a hazard for the Phase 2-4 server wiring (threaded requests, downstream randomness). Plus a visible output defect: double periods in ~33% of generated captions.

## Major Issues

### MA-01: Global `random.seed()` mutates process-wide RNG — cross-module pollution + thread hazard

**File:** `scripts/alina_textgen.py:366, 406`
**Issue:** Both `generate_caption(seed=...)` and `batch_generate(seed=...)` call `random.seed(seed)` on the shared global RNG. Verified: after `generate_caption(seed=12345)`, the global stream differs. This module is not alone in the process — `core/text_generator.py` and `pipeline/prompt_bank.py` draw from the same global `random`. Any seeded call from the Phase 2-4 server endpoint will re-seed the RNG for photo/video prompt generation (making downstream draws deterministic/repetitive), and under `ThreadingHTTPServer` concurrent seeded requests race on shared state. The plan explicitly permitted an isolated instance ("Use random.Random instance optionally but seed must be honored") — the model file `core/text_generator.py` also uses global state, but it never re-seeds, so this file introduces the pollution where the model didn't.
**Fix:**
```python
def generate_caption(hook_type=None, platform="tiktok", seed=None):
    rng = random.Random(seed) if seed is not None else random
    ...
    opener = rng.choice(OPENERS[hook_type])
    num_middles = rng.randint(0, 2)
    middles = rng.sample(MIDDLES[hook_type], num_middles)
    closer = rng.choice(CLOSERS[hook_type])
```
(batch_generate similarly: `rng = random.Random(seed) if seed is not None else random`, and pass the rng into generate_caption instead of re-seeding globals.)

### MA-02: Dedup cap silently truncates output — `batch_generate(count>200)` returns 200 with no signal

**File:** `scripts/alina_textgen.py:411`
**Issue:** The `attempts < 200` cap makes the `while` loop exit before `len(results) == count` whenever `count > 200` (deterministic — 1000 is never satisfiable) or on pathological collision runs. Verified: `batch_generate(1000, platforms=['stories'], seed=1)` returns 200 items. The docstring documents "len == count unless cap exhausted", but the caller gets no error, warning, or partial flag — a Phase 2 server endpoint asking for a 1000-caption batch will silently receive 200 and cannot distinguish truncation from success. This is a data-loss-style contract violation for the stated follow-up phases.
**Fix:** Either raise when the cap is hit (`if len(results) < count: raise RuntimeError(f"dedup cap {_MAX_DEDUP_ATTEMPTS} exhausted, got {len(results)}/{count}")`) or return `(results, truncated)` so callers can detect partial output. Consider also validating `count` up front.

## Minor Issues

### MI-01: Double periods in generated caption text

**File:** `scripts/alina_textgen.py:380` (pools: 27 of 220 segments)
**Issue:** 27 segments end with `.` (e.g. opener `"sent the text. instantly regretted it. classic."`, middle `"and somehow i still look unbothered. amazing."`, closer `"and that is the tea. cold. like me."`). `". ".join(...) + "."` then produces `classic.. and ...` mid-caption and `... like me..` at the end. Verified: 65 of 200 generated captions contain `..`. These captions go straight to published social posts — visible formatting defect.
**Fix:** Strip before joining: `text = ". ".join(seg.rstrip(".") for seg in [opener] + middles + [closer]) + "."`

### MI-02: `platforms=[]` raises unhandled IndexError

**File:** `scripts/alina_textgen.py:413`
**Issue:** `random.choice(platforms)` on an empty list raises `IndexError: Cannot choose from an empty sequence` with no context. Callers passing `[]` (e.g. a config-driven Phase 2 endpoint) get a raw crash instead of a clear error.
**Fix:**
```python
if not platforms:
    return []
```
or raise `ValueError("platforms must not be empty")` with a message.

### MI-03: `random.sample` unguarded against shrunk MIDDLES pool

**File:** `scripts/alina_textgen.py:377`
**Issue:** `random.sample(MIDDLES[hook_type], num_middles)` raises `ValueError: Sample larger than population` if a pool ever has fewer than `num_middles` items. The model file this is "structured after" guards this — `core/text_generator.py:243` uses `min(num_middles, len(topic["middles"]))`; the guard was dropped here. This matters because the repo already has an overridable-pool mechanism (`core/prompt_banks.py` OVERRIDABLE_POOLS), and Phase 2-4 may wire caption pools through it — a bank override with <2 middles would crash generation. Empty OPENERS/CLOSERS pools would similarly crash `random.choice`.
**Fix:** Mirror the model file: `middles = rng.sample(MIDDLES[hook_type], min(num_middles, len(MIDDLES[hook_type])))`, and guard pool emptiness.

## Nit

### NI-01: Magic number 200

**File:** `scripts/alina_textgen.py:411`
**Issue:** Dedup cap hardcoded; only documented in the docstring.
**Fix:** Module constant, e.g. `_MAX_DEDUP_ATTEMPTS = 200`, referenced in both the loop and the docstring.

### NI-02: CLI accepts n <= 0 with silent no-op

**File:** `scripts/alina_textgen.py:433, 442`
**Issue:** `python scripts/alina_textgen.py 0` (or negative) prints nothing and exits 0 — no feedback. Plan truth says "CLI prints N captions"; N=0 contradicts the contract silently.
**Fix:** Validate in `main()`: `if args.n <= 0: parser.error("n must be a positive integer")`.

---

_Reviewed: 2026-08-06T16:30:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
