"""Custom prompt bank persistence for the OFM settings tab.

Banks are stored under settings.json["prompt_banks"] as {bank_id: bank}.
A bank is a partial override of prompt_bank.py pool names, so it composes
with the built-in bank without breaking existing generation.
"""

import json
import time
import uuid
from datetime import datetime
from datetime import datetime

from core.config import _load_settings, _save_settings
# Pool names in prompt_bank.py that a bank may override.
OVERRIDABLE_POOLS = (
    "INDOOR_SCENES",
    "MIRROR_SCENES",
    "OUTDOOR_SCENES",
    "FRAMING",
    "HAIR",
    "POSES",
    "QUALITY",
    "OUTFIT_TOPS_POOLS",
    "OUTFIT_BOTTOMS_POOLS",
    "LIGHTING_POOLS",
    "DEFAULT_NEGATIVE",
    "MIRROR_NEGATIVE",
    "IDENTITY_LOCK",
)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def list_banks() -> dict:
    """Return {bank_id: bank} from settings.json."""
    settings = _load_settings()
    banks = settings.get("prompt_banks", {})
    return banks if isinstance(banks, dict) else {}


def get_bank(bank_id: str):
    """Return a single bank dict or None."""
    return list_banks().get(bank_id)


def clone_bank(source_id: str, new_name: str) -> dict:
    """Copy an existing bank into a new bank. When source_id is empty/not a
    saved bank, the new bank starts empty (edits to built-in pools only).

    Returns {'ok': True, 'bank': bank} or {'ok': False, 'error'}.
    """
    new_name = str(new_name or "").strip()
    if not new_name:
        return {"ok": False, "error": "missing bank name"}
    source = get_bank(source_id) if source_id else None
    if source_id and source is None:
        return {"ok": False, "error": f"bank '{source_id}' not found"}
    bank = {
        "id": uuid.uuid4().hex[:12],
        "name": new_name,
        "description": str(source.get("description", "")) if source else "",
        "created": _now(),
        "updated": _now(),
        "pools": dict(source.get("pools", {})) if source else {},
    }
    settings = _load_settings()
    if "prompt_banks" not in settings or not isinstance(settings["prompt_banks"], dict):
        settings["prompt_banks"] = {}
    settings["prompt_banks"][bank["id"]] = bank
    _save_settings(settings)
    return {"ok": True, "bank": bank}


def _sanitize_bank(data) -> dict:
    """Keep only known pool keys; drop empty/invalid overrides."""
    pools = data.get("pools", {})
    if not isinstance(pools, dict):
        pools = {}
    clean = {}
    for key in OVERRIDABLE_POOLS:
        if key in pools:
            val = pools[key]
            if isinstance(val, (list, dict, str)) and (val or isinstance(val, str)):
                clean[key] = val
    return clean


def create_bank(data) -> dict:
    """Create a bank. Returns {'ok': True, 'bank': bank} or {'ok': False, 'error'}."""
    name = str(data.get("name", "")).strip()
    if not name:
        return {"ok": False, "error": "missing bank name"}
    pools = _sanitize_bank(data)
    if not pools:
        return {"ok": False, "error": "bank has no overridable pools"}
    bank = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "description": str(data.get("description", "")).strip(),
        "created": _now(),
        "updated": _now(),
        "pools": pools,
    }
    settings = _load_settings()
    if "prompt_banks" not in settings or not isinstance(settings["prompt_banks"], dict):
        settings["prompt_banks"] = {}
    settings["prompt_banks"][bank["id"]] = bank
    _save_settings(settings)
    return {"ok": True, "bank": bank}


def update_bank(bank_id: str, data) -> dict:
    """Merge name/description/pools into an existing bank. Returns {'ok': bool, ...}."""
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
        pools = _sanitize_bank(data)
        if not pools:
            return {"ok": False, "error": "bank has no overridable pools"}
        bank["pools"] = pools
    bank["updated"] = _now()
    settings = _load_settings()
    settings["prompt_banks"][bank_id] = bank
    _save_settings(settings)
    return {"ok": True, "bank": bank}


def get_active_bank_id() -> str:
    """Return the active prompt bank id ('' = built-in)."""
    settings = _load_settings()
    active = settings.get("active_bank", "")
    if active and active in list_banks():
        return str(active)
    return ""


def set_active_bank_id(bank_id: str) -> dict:
    """Set the active prompt bank ('' = built-in). Returns {'ok': bool, 'error'}."""
    bank_id = str(bank_id or "")
    if bank_id and bank_id not in list_banks():
        return {"ok": False, "error": f"bank '{bank_id}' not found"}
    settings = _load_settings()
    settings["active_bank"] = bank_id
    _save_settings(settings)
    return {"ok": True, "active": bank_id}


def delete_bank(bank_id: str) -> dict:
    settings = _load_settings()
    banks = settings.get("prompt_banks", {})
    if isinstance(banks, dict) and bank_id in banks:
        del banks[bank_id]
        settings["prompt_banks"] = banks
        if settings.get("active_bank") == bank_id:
            settings["active_bank"] = ""
        _save_settings(settings)
        return {"ok": True}
    return {"ok": False, "error": f"bank '{bank_id}' not found"}


def export_banks() -> dict:
    """Return all custom banks + active bank as an exportable dict."""
    return {
        "version": 1,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "active_bank": get_active_bank_id(),
        "banks": list_banks(),
    }


def import_banks(data) -> dict:
    """Merge banks from an export dict into settings (existing IDs preserved).

    Returns {'ok': True, 'imported': int, 'skipped': int, 'active_bank_set': bool}.
    """
    imported = 0
    skipped = 0
    if not isinstance(data, dict):
        return {"ok": False, "error": "invalid export data"}
    banks = data.get("banks")
    if not isinstance(banks, dict):
        return {"ok": False, "error": "missing 'banks' object"}
    settings = _load_settings()
    if "prompt_banks" not in settings or not isinstance(settings["prompt_banks"], dict):
        settings["prompt_banks"] = {}
    for bank_id, bank in banks.items():
        if not isinstance(bank, dict) or not str(bank.get("name", "")).strip():
            skipped += 1
            continue
        if bank_id in settings["prompt_banks"]:
            skipped += 1
            continue
        clean = {
            "id": bank_id,
            "name": str(bank.get("name", "")).strip(),
            "description": str(bank.get("description", "")).strip(),
            "created": str(bank.get("created", _now())),
            "updated": str(bank.get("updated", _now())),
            "pools": _sanitize_bank(bank),
        }
        if not clean["pools"]:
            skipped += 1
            continue
        settings["prompt_banks"][bank_id] = clean
        imported += 1
    active_bank_set = False
    active = data.get("active_bank")
    if active and active in settings["prompt_banks"]:
        settings["active_bank"] = active
        active_bank_set = True
    if imported or active_bank_set:
        _save_settings(settings)
    return {"ok": True, "imported": imported, "skipped": skipped, "active_bank_set": active_bank_set}


def export_banks() -> dict:
    """Return all custom banks + active bank as an exportable dict."""
    return {
        "version": 1,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "active_bank": get_active_bank_id(),
        "banks": list_banks(),
    }


def import_banks(data) -> dict:
    """Merge banks from an export dict into settings.

    Returns {'ok': True, 'imported': int, 'skipped': int, 'active_bank_set': bool}.
    Validation:
    - data must be a dict; banks must be dict of {bank_id: bank}.
    - Skip entries that aren't dicts or have no valid name.
    - Sanitize each bank's pools with _sanitize_bank(); if sanitized pools empty, skip.
    - MERGE MODE: if bank_id already exists in settings, SKIP it (keep existing). Otherwise insert
      the bank as-is (preserving its id/name/description/created/updated/pools).
    - After merge, if data["active_bank"] non-empty AND that id now exists in settings, call
      set_active_bank_id() and set active_bank_set=True.
    """
    if not isinstance(data, dict):
        return {"ok": False, "error": "export data must be an object"}
    banks = data.get("banks")
    if not isinstance(banks, dict):
        return {"ok": False, "error": "export data missing 'banks' object"}

    settings = _load_settings()
    if "prompt_banks" not in settings or not isinstance(settings["prompt_banks"], dict):
        settings["prompt_banks"] = {}

    imported = 0
    skipped = 0
    for bank_id, bank in banks.items():
        if not isinstance(bank, dict):
            skipped += 1
            continue
        name = str(bank.get("name", "")).strip()
        if not name:
            skipped += 1
            continue
        pools = _sanitize_bank(bank)
        if not pools:
            skipped += 1
            continue
        if bank_id in settings["prompt_banks"]:
            skipped += 1
            continue
        entry = {
            "id": str(bank_id),
            "name": name,
            "description": str(bank.get("description", "")),
            "created": str(bank.get("created", "")),
            "updated": str(bank.get("updated", "")),
            "pools": pools,
        }
        settings["prompt_banks"][bank_id] = entry
        imported += 1

    _save_settings(settings)

    active_bank_set = False
    active = data.get("active_bank")
    if active and str(active) in settings["prompt_banks"]:
        set_active_bank_id(str(active))
        active_bank_set = True

    return {"ok": True, "imported": imported, "skipped": skipped, "active_bank_set": active_bank_set}

