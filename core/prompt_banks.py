"""Custom prompt bank + preset persistence for the OFM settings tab.

Banks are stored under settings.json["prompt_banks"] as {bank_id: bank}.
A bank is a partial override of prompt_bank.py pool names, so it composes
with the built-in bank without breaking existing generation.

Presets are stored under settings.json["presets"] as a list of
{id, name, created, config:{vibe, camera_style, lighting, outfit_style,
time_of_day, count, bank_id}}.
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
    """Delete a bank. Also drops any preset referencing it. Returns {'ok': bool}."""
    settings = _load_settings()
    banks = settings.get("prompt_banks", {})
    if isinstance(banks, dict) and bank_id in banks:
        del banks[bank_id]
        settings["prompt_banks"] = banks
        if settings.get("active_bank") == bank_id:
            settings["active_bank"] = ""
        presets = settings.get("presets", [])
        if isinstance(presets, list):
            settings["presets"] = [p for p in presets if p.get("config", {}).get("bank_id") != bank_id]
        _save_settings(settings)
        return {"ok": True}
    return {"ok": False, "error": f"bank '{bank_id}' not found"}


def list_presets() -> list:
    """Return the presets list."""
    settings = _load_settings()
    presets = settings.get("presets", [])
    return presets if isinstance(presets, list) else []


def create_preset(data) -> dict:
    """Save current generation config as a named preset."""
    name = str(data.get("name", "")).strip()
    if not name:
        return {"ok": False, "error": "missing preset name"}
    config = data.get("config", {})
    if not isinstance(config, dict) or not config:
        return {"ok": False, "error": "missing preset config"}
    preset = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "created": _now(),
        "config": {
            "vibe": str(config.get("vibe", "indoor")),
            "camera_style": str(config.get("camera_style", "handheld")),
            "lighting": str(config.get("lighting", "warm")),
            "outfit_style": str(config.get("outfit_style", "sexy")),
            "time_of_day": str(config.get("time_of_day", "day")),
            "count": int(config.get("count", 6) or 6),
            "bank_id": config.get("bank_id", ""),
        },
    }
    settings = _load_settings()
    presets = settings.get("presets", [])
    if not isinstance(presets, list):
        presets = []
    presets.append(preset)
    settings["presets"] = presets
    _save_settings(settings)
    return {"ok": True, "preset": preset}


def delete_preset(preset_id: str) -> dict:
    settings = _load_settings()
    presets = settings.get("presets", [])
    if not isinstance(presets, list):
        return {"ok": False, "error": "preset not found"}
    new_presets = [p for p in presets if p.get("id") != preset_id]
    if len(new_presets) == len(presets):
        return {"ok": False, "error": "preset not found"}
    settings["presets"] = new_presets
    _save_settings(settings)
    return {"ok": True}
