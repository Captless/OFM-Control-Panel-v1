import os
from pathlib import Path
import json


_identity_path = Path(__file__).resolve().parent.parent / "wavespeed_identity_alina.md"
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


def set_api_key(key: str, provider: str = "wavespeed") -> None:
    global API_KEY
    settings = _load_settings()
    if "api_keys" not in settings:
        settings["api_keys"] = {}
    settings["api_keys"][provider] = key
    _save_settings(settings)
    if provider == "wavespeed":
        API_KEY = key


def get_api_key(provider: str = "wavespeed") -> str:
    # 1. Check env var for this provider
    env_var = f"{provider.upper()}_API_KEY"
    key = os.environ.get(env_var)
    if key:
        return key
    # 2. Check settings.json for this provider
    settings = _load_settings()
    api_keys = settings.get("api_keys", {})
    key = api_keys.get(provider)
    if key:
        return key
    # 3. For wavespeed only, check identity file
    if provider == "wavespeed":
        identity = _parse_identity_file()
        return identity.get("api_key", "")
    return ""


def remove_api_key(provider: str = "wavespeed") -> None:
    global API_KEY
    settings = _load_settings()
    if "api_keys" in settings:
        settings["api_keys"].pop(provider, None)
        _save_settings(settings)
    if provider == "wavespeed":
        identity = _parse_identity_file()
        env_key = os.environ.get("WAVESPEED_API_KEY")
        API_KEY = env_key or identity.get("api_key", "")


def list_api_keys() -> dict:
    """Returns {provider_name: masked_preview}"""
    settings = _load_settings()
    api_keys = settings.get("api_keys", {})
    result = {}
    for provider, key in api_keys.items():
        if len(key) > 8:
            result[provider] = key[:4] + "****" + key[-4:]
        elif key:
            result[provider] = "****"
        else:
            result[provider] = ""
    # Also include wavespeed from env/identity if not in settings
    if "wavespeed" not in result:
        ws = get_api_key("wavespeed")
        if ws:
            if len(ws) > 8:
                result["wavespeed"] = ws[:4] + "****" + ws[-4:]
            else:
                result["wavespeed"] = "****"
    return result


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
    return result


def _identity_name() -> str:
    """Extract the name from the identity markdown file (e.g. 'Alina')."""
    if not _identity_path.is_file():
        return ""
    text = _identity_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "**Name:**" in line:
            return line.split("**Name:**")[1].strip()
    return ""


def _maybe_migrate_identity() -> None:
    """Auto-migrate identity/env key into wavespeed_accounts if it's empty.

    This ensures the default WaveSpeed key from wavespeed_identity_alina.md
    or WAVESPEED_API_KEY env var appears as a regular account in the UI.
    Runs once — after migration, settings.json has the account permanently.
    """
    settings = _load_settings()
    accounts = settings.get("wavespeed_accounts", {})
    if accounts:
        return  # Already has accounts, no migration needed

    env_key = os.environ.get("WAVESPEED_API_KEY", "")
    identity = _parse_identity_file()
    id_key = identity.get("api_key", "")
    raw_key = env_key or id_key
    if not raw_key:
        return  # No key to migrate

    name = _identity_name() or "default"
    settings["wavespeed_accounts"] = {name: raw_key}
    settings["active_wavespeed_account"] = name
    _save_settings(settings)


def _get_config() -> tuple[str, str]:
    api_key = os.environ.get("WAVESPEED_API_KEY")
    avatar_url = os.environ.get("WAVESPEED_AVATAR_URL")
    if api_key and avatar_url:
        return api_key, avatar_url
    identity = _parse_identity_file()
    if not api_key:
        api_key = identity.get("api_key", "")
    if not avatar_url:
        avatar_url = identity.get("avatar_url", "")
    return api_key, avatar_url


API_KEY, AVATAR_URL = _get_config()
# Allow settings.json to override at runtime
_settings = _load_settings()
_api_keys = _settings.get("api_keys", {})
if _api_keys.get("wavespeed"):
    API_KEY = _api_keys["wavespeed"]

PHOTO_PRICE = 0.07
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "stable-diffusion-v1.5")
VIDEO_MODEL = os.environ.get("VIDEO_MODEL", "wavespeed-i2v")

# ── WaveSpeed multi-account support ──


def list_wavespeed_accounts() -> dict:
    """Returns {label: masked_key} from wavespeed_accounts settings.
    Auto-migrates identity/env key if accounts are empty."""
    _maybe_migrate_identity()
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
    """Store a wavespeed account key; auto-migrates identity first; auto-sets as active only if truly first."""
    _maybe_migrate_identity()
    settings = _load_settings()
    if "wavespeed_accounts" not in settings:
        settings["wavespeed_accounts"] = {}
    is_first = len(settings["wavespeed_accounts"]) == 0
    settings["wavespeed_accounts"][label] = key
    if is_first:
        settings["active_wavespeed_account"] = label
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
    """Return the key for the active wavespeed account; fallback to get_api_key."""
    _maybe_migrate_identity()
    settings = _load_settings()
    active_label = settings.get("active_wavespeed_account", "")
    accounts = settings.get("wavespeed_accounts", {})
    key = accounts.get(active_label)
    if key:
        return key
    return get_api_key("wavespeed")


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
            "..", "wavespeed-batch-api",
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
