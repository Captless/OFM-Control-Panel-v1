# Phase 2 Plan — Server API Endpoint

## Files
- `webui/server.py` (MODIFY, ~30 lines)

## Tasks
### T2.1 — Import generator
- `sys.path.insert(0, os.path.join(BASE, "scripts"))`
- `from alina_textgen import batch_generate` (in server.py, near other sys.path inserts at top).

### T2.2 — Endpoint in do_POST
- Add handler for `parsed.path == "/api/captions/generate"` in `do_POST` (after `body = self._read_body()`).
- Read `count` (int, default 10, clamp 1-20), `platform` (str, default "tiktok"), `hook_types` (list, optional), `seed` (int, optional).
- Call `batch_generate(count, platforms=[platform], hook_types=hook_types, seed=seed)`.
- Response: `self._json({"ok": True, "captions": caps})`.
- Wrap in try/except → `self._json({"ok": False, "error": str(e)}, 500)`.
- Validate count/platform types → 400 on invalid.

## Verify
- `python -m py_compile webui/server.py`
- Start server, `curl -X POST localhost:8000/api/captions/generate -H "Content-Type: application/json" -d '{"count":3,"platform":"tiktok"}'` → JSON with 3 captions.
- Bad body `-d '{}'` → valid JSON with captions (defaults).
- Invalid count `-d '{"count":"abc"}'` → 400.

## Acceptance
- Endpoint returns valid JSON; malformed body → 400; py_compile clean.
