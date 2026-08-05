import os
from pathlib import Path
import json


_identity_path = Path(__file__).resolve().parent.parent / "docs" / "wavespeed_identity_alina.md"
SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"


def _load_settings() -> dict:
    if SETTINGS_PATH.is_file():
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_settings(data: dict) -> None:
    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _parse_identity_file() -> dict[str, str]:
    result: dict[str, str] = {}
    if not _identity_path.is_file():
        return result
    text = _identity_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "**API Key:**" in line:
            result["api_key"] = line.split("**API Key:**")[1].strip()
        elif "**Avatar URL:**" in line:
            result["avatar_url"] = line.split("**Avatar URL:**")[1].strip()
        elif "**Name:**" in line:
            result["name"] = line.split("**Name:**")[1].strip()
    return result


def get_identity() -> dict:
    """Return identity from settings.json, migrating from the markdown identity file on first read."""
    settings = _load_settings()
    identity = settings.get("identity")
    if isinstance(identity, dict):
        return {
            "name": str(identity.get("name", "")),
            "avatar_url": str(identity.get("avatar_url", "")),
        }
    identity = _parse_identity_file()
    migrated = {
        "name": identity.get("name", ""),
        "avatar_url": identity.get("avatar_url", ""),
    }
    if migrated["avatar_url"] or migrated["name"]:
        settings["identity"] = migrated
        _save_settings(settings)
    return migrated


def set_identity(name=None, avatar_url=None) -> dict:
    """Merge name/avatar_url into settings.json identity key; persists unchanged fields."""
    settings = _load_settings()
    identity = settings.get("identity", {})
    if not isinstance(identity, dict):
        identity = {}
    if name is not None:
        identity["name"] = str(name)
    if avatar_url is not None:
        identity["avatar_url"] = str(avatar_url)
    settings["identity"] = identity
    _save_settings(settings)
    return {
        "name": identity.get("name", ""),
        "avatar_url": identity.get("avatar_url", ""),
    }


def list_wavespeed_accounts() -> dict:
    """Returns {label: masked_key} from wavespeed_accounts settings."""
    settings = _load_settings()
    accounts = settings.get("wavespeed_accounts", {})
    result = {}
    for label, key in accounts.items():
        if len(key) > 8:
            result[label] = key[:4] + "****" + key[-4:]
        elif key:
            result[label] = "****"
        else:
            result[label] = ""
    return result


def set_wavespeed_account(label: str, key: str) -> None:
    """Store a wavespeed account key."""
    settings = _load_settings()
    if "wavespeed_accounts" not in settings:
        settings["wavespeed_accounts"] = {}
    settings["wavespeed_accounts"][label] = key
    _save_settings(settings)


def remove_wavespeed_account(label: str) -> None:
    """Remove a wavespeed account; reselect active if the removed one was active."""
    settings = _load_settings()
    accounts = settings.get("wavespeed_accounts", {})
    removed = accounts.pop(label, None)
    if removed is not None:
        if settings.get("active_wavespeed_account") == label:
            if accounts:
                settings["active_wavespeed_account"] = next(iter(accounts))
            else:
                settings["active_wavespeed_account"] = ""
        _save_settings(settings)


def rename_wavespeed_account(old_label: str, new_label: str) -> dict:
    """Rename a wavespeed account label. Returns dict with ok/error."""
    settings = _load_settings()
    accounts = settings.get("wavespeed_accounts", {})
    if old_label not in accounts:
        return {"ok": False, "error": f"Account '{old_label}' not found"}
    if new_label in accounts:
        return {"ok": False, "error": f"Account '{new_label}' already exists"}
    if not new_label.strip():
        return {"ok": False, "error": "New label cannot be empty"}
    key = accounts.pop(old_label)
    accounts[new_label] = key
    if settings.get("active_wavespeed_account") == old_label:
        settings["active_wavespeed_account"] = new_label
    _save_settings(settings)
    return {"ok": True}


def get_active_wavespeed_key() -> str:
    """Return the key for the active wavespeed account."""
    settings = _load_settings()
    active_label = settings.get("active_wavespeed_account", "")
    accounts = settings.get("wavespeed_accounts", {})
    return accounts.get(active_label, "")


def set_active_wavespeed_account(label: str) -> None:
    """Set the active wavespeed account label in settings."""
    settings = _load_settings()
    settings["active_wavespeed_account"] = label
    _save_settings(settings)


def test_wavespeed_account(label: str) -> dict:
    """Test a wavespeed account key via GET /models; returns {'ok': bool, 'error': str}."""
    import sys, os
    sys.path.insert(
        0,
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "api",
        ),
    )
    from wavespeed_client import WaveSpeedClient  # noqa: E402 — lazy import avoids circular dep

    settings = _load_settings()
    accounts = settings.get("wavespeed_accounts", {})
    key = accounts.get(label)
    if not key:
        return {"ok": False, "error": f"No key found for account '{label}'"}
    try:
        client = WaveSpeedClient(key)
        client.validate()
        return {"ok": True, "error": ""}
    except Exception as e:
        return {"ok": False, "error": str(e)}


PHOTO_PRICE = 0.07
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "stable-diffusion-v1.5")
VIDEO_MODEL = os.environ.get("VIDEO_MODEL", "wavespeed-i2v")