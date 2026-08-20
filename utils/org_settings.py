"""Paramètres globaux de l'organisation : logo affiché sur le tableau de bord,
et devise utilisée pour l'ensemble des valeurs monétaires de l'agent.

Mode hybride, comme utils/storage.py : Supabase si configuré (partagé entre
tous les conseillers en ligne), sinon un fichier JSON local (usage individuel
hors-ligne). Un seul enregistrement global (pas par utilisateur).
"""
import json
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCAL_PATH = os.path.join(_BASE_DIR, "storage", "_org_settings.json")

_DEFAULTS = {"logo_base64": None, "nom_organisation": "", "devise": "FCFA"}

_cache = None


def _supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_KEY"))


def _headers() -> dict:
    key = os.environ["SUPABASE_KEY"]
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _base_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/org_settings"


def _load_local() -> dict:
    if os.path.exists(_LOCAL_PATH):
        with open(_LOCAL_PATH, "r", encoding="utf-8") as f:
            return {**_DEFAULTS, **json.load(f)}
    return dict(_DEFAULTS)


def _save_local(data: dict) -> None:
    with open(_LOCAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_org_settings(force_refresh: bool = False) -> dict:
    """Retourne {"logo_base64", "nom_organisation", "devise"}. Mis en cache
    dans le processus pour éviter un appel réseau à chaque affichage."""
    global _cache
    if _cache is not None and not force_refresh:
        return _cache

    if _supabase_configured():
        try:
            import requests
            resp = requests.get(_base_url(), headers=_headers(),
                                 params={"select": "*", "limit": 1}, timeout=10)
            resp.raise_for_status()
            rows = resp.json()
            _cache = {**_DEFAULTS, **rows[0]} if rows else dict(_DEFAULTS)
        except Exception:
            _cache = dict(_DEFAULTS)
    else:
        _cache = _load_local()
    return _cache


def update_org_settings(**fields) -> None:
    """Met à jour un ou plusieurs champs (logo_base64, nom_organisation,
    devise) — crée l'enregistrement s'il n'existe pas encore."""
    global _cache
    current = get_org_settings()
    current.update(fields)

    if _supabase_configured():
        import requests
        resp = requests.get(_base_url(), headers=_headers(),
                             params={"select": "id", "limit": 1}, timeout=10)
        resp.raise_for_status()
        existing = resp.json()
        if existing:
            row_id = existing[0]["id"]
            r = requests.patch(_base_url(), headers=_headers(),
                                params={"id": f"eq.{row_id}"}, json=fields, timeout=10)
        else:
            r = requests.post(_base_url(), headers=_headers(), json=current, timeout=10)
        r.raise_for_status()
    else:
        _save_local(current)

    _cache = current


def get_devise() -> str:
    return get_org_settings().get("devise") or "FCFA"


def format_money(value, decimals: int = 0) -> str:
    """Formate une valeur monétaire avec la devise configurée par l'organisation
    (ex. '1 250 000 FCFA'). Utiliser cette fonction pour tout affichage d'un
    montant, plutôt que de coder la devise en dur."""
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0.0
    return f"{value:,.{decimals}f} {get_devise()}"
