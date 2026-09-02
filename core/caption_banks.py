"""Caption bank persistence for the OFM caption generator.

Banks are stored under settings.json["caption_banks"] as {bank_id: bank}.
A bank is a full replacement of the 7 pool structures in alina_textgen.py.

Export produces a .py file the user can edit in any code editor.
Import parses the .py file via ast.literal_eval (no eval).
"""

import ast
import json
import os
import re
import time
import uuid
from datetime import datetime

from core.config import _load_settings, _save_settings

OVERRIDABLE_POOLS = (
    "OPENERS",
    "MIDDLES",
    "CLOSERS",
    "CONTEXT_KEYWORDS",
    "CONTEXT_PHRASES",
)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def list_banks() -> dict:
    """Return {bank_id: bank} from settings.json."""
    settings = _load_settings()
    banks = settings.get("caption_banks", {})
    return banks if isinstance(banks, dict) else {}


def get_bank(bank_id: str):
    """Return a single bank dict or None."""
    return list_banks().get(bank_id)


def create_bank(data: dict) -> dict:
    """Create a bank. Returns {'ok': True, 'bank': bank} or {'ok': False, 'error'}."""
    name = str(data.get("name", "")).strip()
    if not name:
        return {"ok": False, "error": "missing bank name"}
    pools = _sanitize_pools(data.get("pools", {}))
    if not pools:
        return {"ok": False, "error": "bank has no valid pools"}
    bank = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "description": str(data.get("description", "")).strip(),
        "created": _now(),
        "updated": _now(),
        "pools": pools,
    }
    settings = _load_settings()
    if "caption_banks" not in settings or not isinstance(settings["caption_banks"], dict):
        settings["caption_banks"] = {}
    settings["caption_banks"][bank["id"]] = bank
    _save_settings(settings)
    return {"ok": True, "bank": bank}


def update_bank(bank_id: str, data: dict) -> dict:
    """Merge name/description/pools into an existing bank."""
    banks = list_banks()
    if bank_id not in banks:
        return {"ok": False, "error": f"bank '{bank_id}' not found"}
    bank = dict(banks[bank_id])
    if data.get("name") is not None:
        name = str(data["name"]).strip()
        if not name:
            return {"ok": False, "error": "missing bank name"}
        bank["name"] = name
    if data.get("description") is not None:
        bank["description"] = str(data["description"]).strip()
    if "pools" in data:
        pools = _sanitize_pools(data["pools"])
        if not pools:
            return {"ok": False, "error": "bank has no valid pools"}
        bank["pools"] = pools
    bank["updated"] = _now()
    settings = _load_settings()
    settings["caption_banks"][bank_id] = bank
    _save_settings(settings)
    return {"ok": True, "bank": bank}


def delete_bank(bank_id: str) -> dict:
    settings = _load_settings()
    banks = settings.get("caption_banks", {})
    if isinstance(banks, dict) and bank_id in banks:
        del banks[bank_id]
        settings["caption_banks"] = banks
        if settings.get("active_caption_bank") == bank_id:
            settings["active_caption_bank"] = ""
        _save_settings(settings)
        return {"ok": True}
    return {"ok": False, "error": f"bank '{bank_id}' not found"}


# ---------------------------------------------------------------------------
# Active bank
# ---------------------------------------------------------------------------

def get_active_bank_id() -> str:
    """Return the active caption bank id ('' = built-in defaults)."""
    settings = _load_settings()
    active = settings.get("active_caption_bank", "")
    if active and active in list_banks():
        return str(active)
    return ""


def set_active_bank_id(bank_id: str) -> dict:
    """Set the active caption bank ('' = built-in)."""
    bank_id = str(bank_id or "")
    if bank_id and bank_id not in list_banks():
        return {"ok": False, "error": f"bank '{bank_id}' not found"}
    settings = _load_settings()
    settings["active_caption_bank"] = bank_id
    _save_settings(settings)
    return {"ok": True, "active": bank_id}


# ---------------------------------------------------------------------------
# Export as .py file
# ---------------------------------------------------------------------------

def export_bank(bank_id: str) -> dict:
    """Return {'ok': True, 'filename': ..., 'content': ...} for download.

    bank_id='' or 'default' → export built-in pools.
    """
    if not bank_id or bank_id == "default":
        pools = get_builtin_pools()
        name = "Default"
    else:
        banks = list_banks()
        bank = banks.get(bank_id)
        if not bank:
            return {"ok": False, "error": f"bank '{bank_id}' not found"}
        pools = bank.get("pools", {})
        name = bank.get("name", "caption_bank")
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_") or "caption_bank"

    lines = [
        f"# OFM Caption Bank — \"{name}\"",
        f"# Exported: {datetime.now().isoformat(timespec='seconds')}",
        "# Edit pools below, then import back into OFM.",
        "",
    ]

    for key in OVERRIDABLE_POOLS:
        val = pools.get(key)
        if val is None:
            continue
        lines.append(f"{key} = {_pprint_value(val)}")
        lines.append("")

    content = "\n".join(lines)
    filename = f"{safe_name}.py"

    return {"ok": True, "filename": filename, "content": content, "name": name}


def _pprint_value(val, indent=4):
    """Pretty-print a pool value as readable multi-line Python.

    - dict[str, list[str]] → nested, one item per line per key
    - list[str]           → one string per line
    - str                 → quoted on one line
    """
    pad = " " * indent
    if isinstance(val, dict):
        items = []
        for k, v in val.items():
            inner = _pprint_value(v, indent + 4)
            items.append(f"{pad}{k!r}: {inner}")
        if len(items) == 1:
            return "{\n" + items[0] + ",\n" + pad + "}"
        body = ",\n".join(items)
        return "{\n" + body + ",\n" + pad + "}"
    if isinstance(val, list):
        if not val:
            return "[]"
        if all(isinstance(s, str) for s in val) and len(val) <= 8 and all("," not in s and "\\" not in s for s in val):
            joined = ", ".join(repr(s) for s in val)
            return "[" + joined + "]"
        body = ",\n".join(f"{pad}{v!r}" for v in val)
        return "[\n" + body + ",\n" + pad + "]"
    return repr(val)


# ---------------------------------------------------------------------------
# Import from .py file
# ---------------------------------------------------------------------------

def import_bank(name: str, py_content: str) -> dict:
    """Parse a .py file, extract pool variables, create a bank.

    Uses ast.literal_eval — no eval, no imports, safe.
    """
    name = str(name or "").strip()
    if not name:
        return {"ok": False, "error": "missing bank name"}

    if not py_content or not isinstance(py_content, str):
        return {"ok": False, "error": "empty file content"}

    try:
        tree = ast.parse(py_content, mode="eval")
    except SyntaxError:
        try:
            tree = ast.parse(py_content, mode="exec")
        except SyntaxError as e:
            return {"ok": False, "error": f"Python syntax error: {e}"}

    pools = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in OVERRIDABLE_POOLS:
                    try:
                        val = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        continue
                    clean = _validate_pool(target.id, val)
                    if clean is not None:
                        pools[target.id] = clean

    if not pools:
        return {"ok": False, "error": "no valid pools found in file (expected OPENERS, MIDDLES, etc.)"}

    return create_bank({"name": name, "pools": pools})


def import_bank_from_file(filename: str, py_content: str) -> dict:
    """Import using filename as bank name (strip path/extension)."""
    base = os.path.splitext(os.path.basename(filename))[0]
    name = re.sub(r"[_-]+", " ", base).strip() or "Imported Bank"
    return import_bank(name, py_content)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_pools(pools: dict) -> dict:
    """Keep only valid pool keys with valid values."""
    if not isinstance(pools, dict):
        return {}
    clean = {}
    for key, val in pools.items():
        if key not in OVERRIDABLE_POOLS:
            continue
        validated = _validate_pool(key, val)
        if validated is not None:
            clean[key] = validated
    return clean


def _validate_pool(key: str, val):
    """Validate a single pool value matches expected type."""
    if key in ("OPENERS", "MIDDLES", "CLOSERS"):
        # dict of {hook_type: [strings]}
        if not isinstance(val, dict):
            return None
        clean = {}
        for hook, items in val.items():
            if isinstance(items, list) and all(isinstance(s, str) for s in items):
                clean[str(hook)] = items
        return clean if clean else None

    if key in ("CTA_POOL", "HASHTAG_POOL"):
        # list of strings
        if isinstance(val, list) and all(isinstance(s, str) for s in val):
            return val
        return None

    if key in ("CONTEXT_KEYWORDS", "CONTEXT_PHRASES"):
        # dict of {tag: [strings]}
        if not isinstance(val, dict):
            return None
        clean = {}
        for tag, items in val.items():
            if isinstance(items, list) and all(isinstance(s, str) for s in items):
                clean[str(tag)] = items
        return clean if clean else None

    return None


def get_builtin_pools() -> dict:
    """Return the built-in pools from alina_textgen.py."""
    import sys
    scripts_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "scripts"
    )
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from alina_textgen import (
            OPENERS, MIDDLES, CLOSERS, CTA_POOL, HASHTAG_POOL,
            CONTEXT_KEYWORDS, CONTEXT_PHRASES,
        )
        return {
            "OPENERS": OPENERS,
            "MIDDLES": MIDDLES,
            "CLOSERS": CLOSERS,
            "CTA_POOL": CTA_POOL,
            "HASHTAG_POOL": HASHTAG_POOL,
            "CONTEXT_KEYWORDS": CONTEXT_KEYWORDS,
            "CONTEXT_PHRASES": CONTEXT_PHRASES,
        }
    except ImportError:
        return {}


def get_active_pools() -> dict:
    """Return the active bank's pools, or built-in pools if no bank active.

    Always returns a complete dict with all 7 keys. If a bank is active
    but missing a key, the built-in value fills the gap.
    """
    bank_id = get_active_bank_id()
    return get_pools_for(bank_id)


def get_pools_for(bank_id: str) -> dict:
    """Return complete 7-key pools for a specific bank (falling back to built-ins)."""
    if not bank_id:
        return get_builtin_pools()

    bank = get_bank(bank_id)
    if not bank:
        return get_builtin_pools()

    builtin = get_builtin_pools()
    bank_pools = bank.get("pools", {})
    merged = {}
    for key in builtin:
        merged[key] = bank_pools.get(key, builtin.get(key))
    return merged
