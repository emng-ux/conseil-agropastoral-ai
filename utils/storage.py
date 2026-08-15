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
        "updated_at": data.get("updated_at", ""),
        "validated": bool(data.get("validation")),
    }


def save_diagnostic(diagnostic_id: str, data: dict) -> None:
    ensure_code(diagnostic_id, data)
    data["updated_at"] = datetime.utcnow().isoformat()
    if _supabase_configured():
        _supabase_save(diagnostic_id, data)
    else:
        _local_save(diagnostic_id, data)


def load_diagnostic(diagnostic_id: str) -> dict:
    if _supabase_configured():
        return _supabase_load(diagnostic_id)
    return _local_load(diagnostic_id)


def delete_diagnostic(diagnostic_id: str) -> None:
    if _supabase_configured():
        _supabase_delete(diagnostic_id)
    else:
        _local_delete(diagnostic_id)


def list_diagnostics() -> list:
    """Retourne la liste des diagnostics triés du plus récent au plus ancien."""
    items = _supabase_list() if _supabase_configured() else _local_list()
    items.sort(key=lambda x: x["updated_at"], reverse=True)
    return items


def storage_backend_name() -> str:
    """Utilisé par l'interface pour indiquer où sont stockées les données."""
    return "Supabase (base partagée en ligne)" if _supabase_configured() else "Fichiers locaux (cet ordinateur)"
