"""Gestion simple des traductions FR/EN."""
import json
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_I18N_DIR = os.path.join(_BASE_DIR, "i18n")

_cache = {}


def load_translations(lang: str) -> dict:
    """Charge (avec cache) le dictionnaire de traductions pour une langue."""
    if lang not in _cache:
        path = os.path.join(_I18N_DIR, f"{lang}.json")
        if not os.path.exists(path):
            lang = "fr"
            path = os.path.join(_I18N_DIR, "fr.json")
        with open(path, "r", encoding="utf-8") as f:
            _cache[lang] = json.load(f)
    return _cache[lang]


def t(key: str, lang: str = "fr") -> str:
    """Retourne la traduction d'une clé, ou la clé elle-même si absente."""
    translations = load_translations(lang)
    return translations.get(key, key)
