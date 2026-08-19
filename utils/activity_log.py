"""Journal d'activité : trace qui fait quoi et quand (connexions, créations
et validations de diagnostics...), stocké dans la table Supabase
`activity_log`. Fonctionne en mode dégradé silencieux si Supabase n'est pas
configuré (pas de journalisation en usage local individuel — pas nécessaire
dans ce contexte)."""
import os
from datetime import datetime


def _supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_KEY"))


def _headers() -> dict:
    key = os.environ["SUPABASE_KEY"]
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _base_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/activity_log"


def log_action(username: str, action: str, details: str = "") -> None:
    """N'échoue jamais bruyamment : la journalisation ne doit jamais bloquer
    l'usage normal de l'application si elle rencontre un problème."""
    if not _supabase_configured():
        return
    try:
        import requests
        payload = {
            "username": username, "action": action, "details": details,
            "created_at": datetime.utcnow().isoformat(),
        }
        requests.post(_base_url(), headers=_headers(), json=payload, timeout=8)
    except Exception:
        pass


def list_recent_actions(limit: int = 200) -> list:
    if not _supabase_configured():
        return []
    import requests
    resp = requests.get(_base_url(), headers=_headers(),
                         params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
                         timeout=15)
    resp.raise_for_status()
    return resp.json()
