"""Stockage des diagnostics, en mode hybride :

- Par défaut (aucune base configurée) : fichiers JSON locaux dans storage/,
  pour un fonctionnement 100% hors-ligne (contrainte "edge computing"). C'est
  le mode adapté à un usage local, sur la machine du conseiller — les données
  y persistent normalement tant que le dossier n'est pas supprimé.

- Si SUPABASE_URL et SUPABASE_KEY sont configurés (variables d'environnement,
  ou secrets Streamlit Cloud copiés vers os.environ par app.py) : les
  diagnostics sont lus/écrits dans une base Supabase (Postgres) via son API
  REST. C'est le mode recommandé pour la version en ligne partagée entre
  plusieurs conseillers, car le système de fichiers d'un déploiement Streamlit
  Cloud est éphémère (les fichiers locaux peuvent être perdus au redémarrage).

Le choix de backend est entièrement transparent pour le reste de l'application :
toutes les fonctions ci-dessous ont la même signature quel que soit le mode actif.
"""
import json
import os
import uuid
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(_BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

_SUPABASE_TABLE = "diagnostics"
_SYNC_STATE_PATH = os.path.join(STORAGE_DIR, "_sync_state.json")


def new_diagnostic_id() -> str:
    return str(uuid.uuid4())


def generate_diagnostic_code(diagnostic_id: str) -> str:
    """Code d'identifiant lisible, dérivé de l'identifiant unique (pas de
    compteur séquentiel partagé : évite tout conflit si plusieurs conseillers
    créent des diagnostics en même temps sur la base partagée)."""
    return f"DIAG-{diagnostic_id[:8].upper()}"


def ensure_code(diagnostic_id: str, diagnostic: dict) -> dict:
    """Garantit qu'un diagnostic dispose d'un code d'identifiant."""
    if not diagnostic.get("code"):
        diagnostic["code"] = generate_diagnostic_code(diagnostic_id)
    return diagnostic


# ---------------------------------------------------------------------------
# Sélection du backend
# ---------------------------------------------------------------------------

def _supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_KEY"))


def hybrid_sync_enabled() -> bool:
    """Mode conseiller de terrain : stockage local en source de vérité (donc
    utilisable hors ligne), avec synchronisation en tâche de fond vers
    Supabase dès qu'une connexion est disponible. Différent du mode Streamlit
    Cloud (_supabase_configured seul) où Supabase est la SEULE source, car
    le système de fichiers y est éphémère. Activé uniquement si demandé
    explicitement, pour ne jamais changer le comportement par défaut."""
    return (
        os.environ.get("SYNC_LOCAL_TO_SUPABASE", "").strip().lower() in ("1", "true", "yes")
        and _supabase_configured()
    )


def _supabase_headers() -> dict:
    key = os.environ["SUPABASE_KEY"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _supabase_base_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + f"/rest/v1/{_SUPABASE_TABLE}"


# ---------------------------------------------------------------------------
# Backend local (fichiers JSON)
# ---------------------------------------------------------------------------

def _local_path(diagnostic_id: str) -> str:
    return os.path.join(STORAGE_DIR, f"{diagnostic_id}.json")


def _local_save(diagnostic_id: str, data: dict) -> None:
    with open(_local_path(diagnostic_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _local_load(diagnostic_id: str) -> dict:
    path = _local_path(diagnostic_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _local_delete(diagnostic_id: str) -> None:
    path = _local_path(diagnostic_id)
    if os.path.exists(path):
        os.remove(path)


def _local_list() -> list:
    items = []
    for filename in os.listdir(STORAGE_DIR):
        if filename.endswith(".json") and not filename.startswith("_"):
            diagnostic_id = filename[:-5]
            data = _local_load(diagnostic_id)
            items.append(_summarize(diagnostic_id, data))
    return items


# ---------------------------------------------------------------------------
# Synchronisation différée (mode hybride terrain) : local -> Supabase
# ---------------------------------------------------------------------------

def _load_sync_state() -> dict:
    """{diagnostic_id: "updated_at de la dernière synchro réussie"}"""
    if not os.path.exists(_SYNC_STATE_PATH):
        return {}
    try:
        with open(_SYNC_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_sync_state(state: dict) -> None:
    with open(_SYNC_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _pending_sync_ids() -> list:
    """Diagnostics locaux jamais synchronisés, ou modifiés localement depuis
    leur dernière synchro (comparaison sur updated_at)."""
    state = _load_sync_state()
    pending = []
    for filename in os.listdir(STORAGE_DIR):
        if not filename.endswith(".json") or filename.startswith("_"):
            continue
        diagnostic_id = filename[:-5]
        data = _local_load(diagnostic_id)
        last_synced = state.get(diagnostic_id)
        if last_synced != data.get("updated_at"):
            pending.append(diagnostic_id)
    return pending


def sync_pending_local_to_supabase() -> dict:
    """Pousse vers Supabase tous les diagnostics locaux en attente. Ne lève
    jamais d'exception : une panne réseau ne doit jamais casser l'app, le
    diagnostic reste simplement en attente pour la prochaine tentative.
    Retourne un résumé {"synced": [...ids...], "failed": [...ids...]}."""
    if not hybrid_sync_enabled():
        return {"synced": [], "failed": []}
    state = _load_sync_state()
    synced, failed = [], []
    for diagnostic_id in _pending_sync_ids():
        data = _local_load(diagnostic_id)
        try:
            _supabase_save(diagnostic_id, data)
        except Exception:
            failed.append(diagnostic_id)
            continue
        state[diagnostic_id] = data.get("updated_at")
        synced.append(diagnostic_id)
    if synced:
        _save_sync_state(state)
    return {"synced": synced, "failed": failed}


# ---------------------------------------------------------------------------
# Backend Supabase (Postgres via API REST)
# ---------------------------------------------------------------------------

def _supabase_save(diagnostic_id: str, data: dict) -> None:
    import requests
    payload = {
        "id": diagnostic_id,
        "code": data.get("code", ""),
        "data": data,
        "updated_at": data.get("updated_at"),
    }
    headers = dict(_supabase_headers())
    headers["Prefer"] = "resolution=merge-duplicates"
    resp = requests.post(_supabase_base_url(), headers=headers, json=payload, timeout=15)
    resp.raise_for_status()


def _supabase_load(diagnostic_id: str) -> dict:
    import requests
    resp = requests.get(_supabase_base_url(), headers=_supabase_headers(),
                         params={"id": f"eq.{diagnostic_id}", "select": "data"}, timeout=15)
    resp.raise_for_status()
    rows = resp.json()
    return rows[0]["data"] if rows else {}


def _supabase_delete(diagnostic_id: str) -> None:
    import requests
    resp = requests.delete(_supabase_base_url(), headers=_supabase_headers(),
                            params={"id": f"eq.{diagnostic_id}"}, timeout=15)
    resp.raise_for_status()


def _supabase_list() -> list:
    import requests
    resp = requests.get(_supabase_base_url(), headers=_supabase_headers(),
                         params={"select": "id,data,updated_at", "order": "updated_at.desc"},
                         timeout=15)
    resp.raise_for_status()
    items = []
    for row in resp.json():
        items.append(_summarize(row["id"], row["data"]))
    return items


# ---------------------------------------------------------------------------
# API publique (identique quel que soit le backend actif)
# ---------------------------------------------------------------------------

def _summarize(diagnostic_id: str, data: dict) -> dict:
    return {
        "id": diagnostic_id,
        "code": data.get("code") or generate_diagnostic_code(diagnostic_id),
        "nom": data.get("nom", "(sans nom)"),
        "type": data.get("type", ""),
        "conseiller": data.get("conseiller", ""),
        "owner_username": data.get("owner_username", ""),
        "updated_at": data.get("updated_at", ""),
        "validated": bool(data.get("validation")),
    }


def save_diagnostic(diagnostic_id: str, data: dict) -> None:
    ensure_code(diagnostic_id, data)
    data["updated_at"] = datetime.utcnow().isoformat()
    if hybrid_sync_enabled():
        # Source de vérité = local, pour que l'enregistrement marche même
        # hors ligne. La tentative de synchro Supabase est best-effort et
        # ne doit jamais faire échouer l'enregistrement local.
        _local_save(diagnostic_id, data)
        try:
            _supabase_save(diagnostic_id, data)
        except Exception:
            pass  # restera en attente, repris par sync_pending_local_to_supabase()
        else:
            state = _load_sync_state()
            state[diagnostic_id] = data["updated_at"]
            _save_sync_state(state)
    elif _supabase_configured():
        _supabase_save(diagnostic_id, data)
    else:
        _local_save(diagnostic_id, data)


def load_diagnostic(diagnostic_id: str) -> dict:
    if hybrid_sync_enabled():
        return _local_load(diagnostic_id)
    if _supabase_configured():
        return _supabase_load(diagnostic_id)
    return _local_load(diagnostic_id)


def delete_diagnostic(diagnostic_id: str) -> None:
    if hybrid_sync_enabled():
        _local_delete(diagnostic_id)
        try:
            _supabase_delete(diagnostic_id)
        except Exception:
            pass
        return
    if _supabase_configured():
        _supabase_delete(diagnostic_id)
    else:
        _local_delete(diagnostic_id)


def list_diagnostics(visible_owners: set = None) -> list:
    """Retourne la liste des diagnostics triés du plus récent au plus ancien.
    Si `visible_owners` est fourni (ensemble d'identifiants), ne retourne que
    les diagnostics dont le propriétaire (owner_username) y figure — utilisé
    pour le cloisonnement hiérarchique des données entre comptes. Les
    diagnostics anciens sans owner_username restent visibles par tous (pas de
    régression sur les données créées avant l'introduction des comptes)."""
    if hybrid_sync_enabled():
        items = _local_list()
    else:
        items = _supabase_list() if _supabase_configured() else _local_list()
    items.sort(key=lambda x: x["updated_at"], reverse=True)
    if visible_owners is not None:
        items = [it for it in items if not it.get("owner_username") or it["owner_username"] in visible_owners]
    return items


def storage_backend_name() -> str:
    """Utilisé par l'interface pour indiquer où sont stockées les données."""
    if hybrid_sync_enabled():
        return "Fichiers locaux (synchronisés vers Supabase dès que possible)"
    return "Supabase (base partagée en ligne)" if _supabase_configured() else "Fichiers locaux (cet ordinateur)"
