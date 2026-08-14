"""Rendu du formulaire de collecte selon le schéma de l'étoile du conseil (6 branches)."""
import json
import os
import streamlit as st

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCHEMA_PATH = os.path.join(_BASE_DIR, "data", "schema_etoile_conseil.json")

_schema_cache = None


def load_schema() -> dict:
    global _schema_cache
    if _schema_cache is None:
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
            _schema_cache = json.load(f)
    return _schema_cache


def branch_keys() -> list:
    return list(load_schema()["branches"].keys())


def branch_label(branch_key: str, lang: str) -> str:
    branch = load_schema()["branches"][branch_key]
    return f"{branch.get('icon', '')} {branch['label'].get(lang, branch['label']['fr'])}"


def _field_key(branch_key: str, field_id: str) -> str:
    return f"{branch_key}.{field_id}"


def render_activity_list(branch_data: dict, field, lang: str) -> list:
    """Champ spécial : liste d'activités/produits pour la matrice BCG."""
    label = field["label"].get(lang, field["label"]["fr"])
    st.markdown(f"**{label}**")
    activities = branch_data.get(field["id"], [])
    if not isinstance(activities, list):
        activities = []

    from utils.i18n import t
    for i, act in enumerate(list(activities)):
        cols = st.columns([3, 2, 2, 1])
        act["nom"] = cols[0].text_input(t("activity_name", lang), value=act.get("nom", ""),
                                         key=f"{field['id']}_nom_{i}")
        act["part_marche_relative"] = cols[1].number_input(
            t("activity_market_share", lang), min_value=0.0, max_value=5.0, step=0.1,
            value=float(act.get("part_marche_relative", 1.0)), key=f"{field['id']}_pm_{i}")
        act["taux_croissance"] = cols[2].number_input(
            t("activity_growth", lang), step=1.0, value=float(act.get("taux_croissance", 0.0)),
            key=f"{field['id']}_tc_{i}")
        if cols[3].button(t("remove", lang), key=f"{field['id']}_rm_{i}"):
            activities.pop(i)
            st.rerun()

    if st.button(t("add_activity", lang), key=f"{field['id']}_add"):
        activities.append({"nom": "", "part_marche_relative": 1.0, "taux_croissance": 0.0})
        st.rerun()

    return activities


def render_branch_form(branch_key: str, diagnostic: dict, lang: str) -> dict:
    """Affiche les champs d'une branche et renvoie les valeurs saisies."""
    schema = load_schema()["branches"][branch_key]
    branch_data = diagnostic.setdefault("etoile", {}).setdefault(branch_key, {})

    for field in schema["fields"]:
        fid = field["id"]
        label = field["label"].get(lang, field["label"]["fr"])
        unit = field.get(f"unit_{lang}") or field.get("unit_fr", "")
        widget_key = _field_key(branch_key, fid)

        if field["type"] == "number":
            full_label = f"{label} ({unit})" if unit else label
            branch_data[fid] = st.number_input(
                full_label, value=float(branch_data.get(fid, 0.0)), key=widget_key)
        elif field["type"] == "textarea":
            branch_data[fid] = st.text_area(
                label, value=branch_data.get(fid, ""), key=widget_key)
        elif field["type"] == "select":
            options = field["options"].get(lang, field["options"]["fr"])
            current = branch_data.get(fid, options[0])
            index = options.index(current) if current in options else 0
            branch_data[fid] = st.selectbox(label, options, index=index, key=widget_key)
        elif field["type"] == "activity_list":
            branch_data[fid] = render_activity_list(branch_data, field, lang)
        else:
            branch_data[fid] = st.text_input(label, value=branch_data.get(fid, ""), key=widget_key)

    return branch_data


def branch_completion_ratio(branch_key: str, diagnostic: dict) -> float:
    """Estime le taux de remplissage d'une branche (pour la visualisation en étoile)."""
    schema = load_schema()["branches"][branch_key]
    branch_data = diagnostic.get("etoile", {}).get(branch_key, {})
    total = len(schema["fields"])
    if total == 0:
        return 0.0
    filled = 0
    for field in schema["fields"]:
        value = branch_data.get(field["id"])
        if field["type"] == "activity_list":
            if value:
                filled += 1
        elif value not in (None, "", 0, 0.0):
            filled += 1
    return round(filled / total, 2)
