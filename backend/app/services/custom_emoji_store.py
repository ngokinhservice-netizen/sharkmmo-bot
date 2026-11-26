import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger("sharkmmo.emojis")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
EMOJI_FILE = os.path.join(DATA_DIR, "custom_emojis.json")

_CACHE: Dict[str, str] = {}
_LOADED = False


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_custom_emojis() -> Dict[str, str]:
    global _CACHE, _LOADED
    _ensure_dir()
    if os.path.exists(EMOJI_FILE):
        try:
            with open(EMOJI_FILE, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
                _LOADED = True
                return _CACHE
        except Exception as e:
            logger.error(f"Failed to load custom emojis from {EMOJI_FILE}: {e}")
            _CACHE = {}
    _CACHE = {}
    _LOADED = True
    return _CACHE


def save_custom_emojis():
    _ensure_dir()
    try:
        with open(EMOJI_FILE, "w", encoding="utf-8") as f:
            json.dump(_CACHE, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(_CACHE)} custom emoji mappings to {EMOJI_FILE}")
    except Exception as e:
        logger.error(f"Failed to save custom emojis: {e}")


def get_custom_emoji_id(slug: str) -> Optional[str]:
    global _LOADED
    if not _LOADED:
        load_custom_emojis()
    return _CACHE.get(slug)


def set_custom_emoji(slug: str, emoji_id: str):
    global _LOADED
    if not _LOADED:
        load_custom_emojis()
    _CACHE[slug] = str(emoji_id).strip()
    save_custom_emojis()


def bulk_set_custom_emojis(mapping: Dict[str, str]):
    global _LOADED
    if not _LOADED:
        load_custom_emojis()
    for k, v in mapping.items():
        if v:
            _CACHE[k] = str(v).strip()
    save_custom_emojis()


def get_all_custom_emojis() -> Dict[str, str]:
    global _LOADED
    if not _LOADED:
        load_custom_emojis()
    return dict(_CACHE)
