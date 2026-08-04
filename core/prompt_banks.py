"""Custom prompt bank persistence for the OFM settings tab.

Banks are stored under settings.json["prompt_banks"] as {bank_id: bank}.
A bank is a partial override of prompt_bank.py pool names, so it composes
with the built-in bank without breaking existing generation.
"""

import json
import time
import uuid

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

