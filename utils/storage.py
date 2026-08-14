"""Stockage local des diagnostics (JSON), pour un fonctionnement 100% hors-ligne.

Chaque diagnostic est un fichier JSON dans storage/, nommé par son identifiant unique.
Aucune dépendance réseau ici : l'outil doit toujours pouvoir enregistrer/lire en local,
même sans connexion Internet (contrainte "edge computing").
"""
import json
import os
import uuid
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(_BASE_DIR, "storage")

os.makedirs(STORAGE_DIR, exist_ok=True)


def new_diagnostic_id() -> str:
    return str(uuid.uuid4())


def _path(diagnostic_id: str) -> str:
    return os.path.join(STORAGE_DIR, f"{diagnostic_id}.json")


def save_diagnostic(diagnostic_id: str, data: dict) -> None:
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
        if filename.endswith(".json"):
            diagnostic_id = filename[:-5]
            data = load_diagnostic(diagnostic_id)
            items.append({
                "id": diagnostic_id,
                "nom": data.get("nom", "(sans nom)"),
                "type": data.get("type", ""),
                "conseiller": data.get("conseiller", ""),
                "updated_at": data.get("updated_at", ""),
                "validated": bool(data.get("validation")),
            })
    items.sort(key=lambda x: x["updated_at"], reverse=True)
    return items
