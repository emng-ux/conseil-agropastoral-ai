"""Stockage local des diagnostics (JSON), pour un fonctionnement 100% hors-ligne.

Chaque diagnostic est un fichier JSON dans storage/, nommé par son identifiant unique.
Aucune dépendance réseau ici : l'outil doit toujours pouvoir enregistrer/lire en local,
même sans connexion Internet (contrainte "edge computing").

Protection des données : chaque diagnostic reçoit aussi un CODE d'identifiant
lisible (ex. DIAG-2026-0007), généré automatiquement et strictement séquentiel.
Ce code est ce qui doit être affiché dans l'interface et les documents exportés
par défaut, à la place du nom réel de l'EFA/OP — voir generate_diagnostic_code
et modules/export.py.
"""
import json
import os
import uuid
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(_BASE_DIR, "storage")
_COUNTER_PATH = os.path.join(STORAGE_DIR, "_code_counter.json")

os.makedirs(STORAGE_DIR, exist_ok=True)


def new_diagnostic_id() -> str:
    return str(uuid.uuid4())


def _path(diagnostic_id: str) -> str:
    return os.path.join(STORAGE_DIR, f"{diagnostic_id}.json")


def _load_counters() -> dict:
    if not os.path.exists(_COUNTER_PATH):
        return {}
    with open(_COUNTER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_counters(counters: dict) -> None:
    with open(_COUNTER_PATH, "w", encoding="utf-8") as f:
        json.dump(counters, f)


def generate_diagnostic_code() -> str:
    """Génère un code d'identifiant lisible et séquentiel (ex. DIAG-2026-0007),
    à afficher à la place du nom réel de l'EFA/OP dans l'interface et les exports."""
    year = datetime.utcnow().year
    counters = _load_counters()
    key = f"DIAG-{year}"
    counters[key] = counters.get(key, 0) + 1
    _save_counters(counters)
    return f"{key}-{counters[key]:04d}"


def ensure_code(diagnostic: dict) -> dict:
    """Garantit qu'un diagnostic (même ancien, créé avant l'introduction des
    codes) dispose d'un code d'identifiant. Ne modifie pas le fichier sur disque
    ici : c'est à l'appelant de sauvegarder si besoin."""
    if not diagnostic.get("code"):
        diagnostic["code"] = generate_diagnostic_code()
    return diagnostic


def save_diagnostic(diagnostic_id: str, data: dict) -> None:
    ensure_code(data)
    data["updated_at"] = datetime.utcnow().isoformat()
    with open(_path(diagnostic_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_diagnostic(diagnostic_id: str) -> dict:
    path = _path(diagnostic_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_diagnostic(diagnostic_id: str) -> None:
    path = _path(diagnostic_id)
    if os.path.exists(path):
        os.remove(path)


def list_diagnostics() -> list:
    """Retourne la liste des diagnostics triés du plus récent au plus ancien."""
    items = []
    for filename in os.listdir(STORAGE_DIR):
        if filename.endswith(".json") and not filename.startswith("_"):
            diagnostic_id = filename[:-5]
            data = load_diagnostic(diagnostic_id)
            items.append({
                "id": diagnostic_id,
                "code": data.get("code") or f"DIAG-{diagnostic_id[:8].upper()}",
                "nom": data.get("nom", "(sans nom)"),
                "type": data.get("type", ""),
                "conseiller": data.get("conseiller", ""),
                "updated_at": data.get("updated_at", ""),
                "validated": bool(data.get("validation")),
            })
    items.sort(key=lambda x: x["updated_at"], reverse=True)
    return items
