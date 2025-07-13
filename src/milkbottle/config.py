import logging
import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger("milkbottle.config")

DEFAULT_CONFIG = {
    "global": {
        "outdir": "~/MilkBottleOutput",
        "log_level": "info",
        "dry": False,
    }
}

CONFIG_PATHS = [
    Path("/etc/milkbottle.toml"),
    Path.home() / ".config/milkbottle.toml",
    Path.cwd() / "milkbottle.toml",
]

ENV_PREFIX = "MILKBOTTLE_"

_config_cache: Optional[Dict[str, Any]] = None


def _load_toml(path: Path) -> Dict[str, Any]:
    """
    Load a TOML file and return its contents as a dict.
    Returns an empty dict if the file does not exist or is invalid.
    """
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {path}: {e}")
        return {}


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dicts, with override taking precedence.
    """
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _merge_dicts(result[k], v)
        else:
            result[k] = v
    return result


def _load_env_vars() -> Dict[str, Any]:
    """
    Load config overrides from environment variables with MILKBOTTLE_ prefix.
    """
    env_config = {}
    for k, v in os.environ.items():
        if k.startswith(ENV_PREFIX):
            key = k[len(ENV_PREFIX) :].lower()
            env_config[key] = v
    return {"global": env_config} if env_config else {}


def get_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load and merge MilkBottle configuration from all sources.
    Returns the merged config as a dict.
    """
    global _config_cache
    if _config_cache is not None and not force_reload:
        return _config_cache

    # Load .env if present
    load_dotenv(override=True)

    config = DEFAULT_CONFIG.copy()
    for path in CONFIG_PATHS:
        config = _merge_dicts(config, _load_toml(path))
    config = _merge_dicts(config, _load_env_vars())
    _config_cache = config
    logger.debug(f"Loaded config: {_config_cache}")
    return _config_cache
