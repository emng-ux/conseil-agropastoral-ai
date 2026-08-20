"""Connecteur KoboToolbox : récupère les soumissions du formulaire terrain
(déployé via kobo_form_generator.py) et les remappe directement dans la
structure `etoile` du diagnostic — sans passer par l'IA, puisque les noms de
question du formulaire Kobo correspondent déjà exactement aux identifiants du
schéma. Élimine structurellement la classe de bugs rencontrée avec l'import
Word (l'IA ne peut pas mal interpréter une réponse à choix strict ou un champ
numérique validé à la saisie).
"""
import os

from modules.collecte import load_schema, _safe_float


def _headers() -> dict:
    return {"Authorization": f"Token {os.environ['KOBO_API_TOKEN']}"}


def _base_url() -> str:
    server = os.environ.get("KOBO_SERVER_URL", "https://kf.kobotoolbox.org").rstrip("/")
    asset_uid = os.environ["KOBO_ASSET_UID"]
    return f"{server}/api/v2/assets/{asset_uid}/data/"


def kobo_available() -> bool:
    return bool(os.environ.get("KOBO_API_TOKEN")) and bool(os.environ.get("KOBO_ASSET_UID"))


def list_kobo_submissions(limit: int = 50) -> list:
    """Retourne les soumissions les plus récentes, triées de la plus récente
    à la plus ancienne."""
    import requests
    resp = requests.get(_base_url(), headers=_headers(),
                         params={"format": "json", "sort": '{"_submission_time": -1}', "limit": limit},
                         timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", data if isinstance(data, list) else [])


def _find_choice_label(schema: dict, branch_key: str, field_id: str, code: str, lang: str) -> str:
    """Retrouve le libellé d'origine (FR/EN) à partir du code de choix
    (opt1, opt2...) renvoyé par Kobo pour un champ 'select'."""
    branch = schema["branches"].get(branch_key, {})
    for field in branch.get("fields", []):
        if field["id"] == field_id and field["type"] == "select":
            options = field["options"].get(lang, field["options"]["fr"])
            options_fr = field["options"]["fr"]
            if code and code.startswith("opt"):
                try:
                    idx = int(code[3:]) - 1
                    if 0 <= idx < len(options):
                        return options[idx]
                except ValueError:
                    pass
            return options[0] if options else ""
    return code or ""


def build_diagnostic_from_kobo_submission(submission: dict, nom: str, type_structure: str,
                                          conseiller: str, lang: str = "fr") -> dict:
    """Construit un diagnostic à partir d'une soumission Kobo brute (dict JSON
    tel que renvoyé par l'API — champs à plat sous la forme
    'branche/champ' ou 'branche/repetition' pour les groupes répétés)."""
    schema = load_schema()
    etoile = {}

    for branch_key, branch in schema["branches"].items():
        branch_data = {}
        for field in branch["fields"]:
            fid = field["id"]
            path = f"{branch_key}/{fid}"

            if field["type"] == "activity_list":
                raw_repeat = submission.get(path, [])
                if not isinstance(raw_repeat, list):
                    raw_repeat = []
                activities = []
                for item in raw_repeat:
                    if not isinstance(item, dict):
                        continue
                    activities.append({
                        "nom": str(item.get(f"{path}/nom", "") or ""),
                        "part_marche_relative": _safe_float(item.get(f"{path}/part_marche_relative"), 1.0),
                        "taux_croissance": _safe_float(item.get(f"{path}/taux_croissance"), 0.0),
                    })
                branch_data[fid] = activities
            elif field["type"] == "number":
                branch_data[fid] = _safe_float(submission.get(path), 0.0)
            elif field["type"] == "select":
                raw_code = submission.get(path, "")
                branch_data[fid] = _find_choice_label(schema, branch_key, fid, raw_code, lang)
            else:
                raw_value = submission.get(path, "")
                branch_data[fid] = str(raw_value) if raw_value is not None else ""

        etoile[branch_key] = branch_data

    return {
        "nom": nom,
        "type": type_structure,
        "conseiller": conseiller,
        "etoile": etoile,
        "kobo_submission_id": submission.get("_id"),
    }


def submission_label(submission: dict) -> str:
    """Libellé court pour afficher une soumission dans la liste de sélection."""
    sub_time = submission.get("_submission_time", "")
    sub_id = submission.get("_id", "?")
    return f"Soumission #{sub_id} — {sub_time[:16].replace('T', ' ')}"
