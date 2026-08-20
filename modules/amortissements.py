"""Tableau des amortissements, généré automatiquement à partir des
immobilisations déjà saisies dans la section Entreprise (diagnostic
financier). Ne ressaisit rien : agrège et présente les données existantes,
catégorie par catégorie.

Règle comptable appliquée : le foncier (terrains) ne s'amortit pas — la
colonne Amortissement est donc toujours neutralisée pour cette catégorie,
quelle que soit la valeur éventuellement saisie par erreur.
"""
import streamlit as st

from utils.org_settings import format_money

from utils.i18n import t

CATEGORIES_ORDER = ["Foncier", "Plantations", "Matériel", "Équipements", "Bâtiments",
                    "Infrastructures", "Autre"]
_NON_AMORTISSABLE = {"Foncier", "Land"}


def compute_tableau_amortissements(diagnostic: dict) -> dict:
    """Retourne {"lignes": [...], "totaux": {...}} à partir de
    diagnostic["entreprise"]["immobilisations"], groupées par catégorie,
    dans l'ordre Foncier/Plantations/Matériel/Équipements/Bâtiments/
    Infrastructures/Autre."""
    ent = diagnostic.get("entreprise", {})
    immos = ent.get("immobilisations", [])

    by_category = {}
    for im in immos:
        cat = im.get("categorie", "Autre") or "Autre"
        by_category.setdefault(cat, []).append(im)

    lignes = []
    total_valeur_achat = 0.0
    total_valeur_actuelle = 0.0
    total_amortissement = 0.0

    ordered_categories = [c for c in CATEGORIES_ORDER if c in by_category]
    ordered_categories += [c for c in by_category if c not in CATEGORIES_ORDER]

    for cat in ordered_categories:
        non_amortissable = cat in _NON_AMORTISSABLE
        for im in by_category[cat]:
            valeur_achat = float(im.get("valeur_achat", 0) or 0)
            valeur_actuelle = float(im.get("valeur_actuelle", 0) or 0)
            amortissement = 0.0 if non_amortissable else float(im.get("amortissement", 0) or 0)
            lignes.append({
                "categorie": cat,
                "valeur_achat": valeur_achat,
                "annee_acquisition": im.get("annee_acquisition", ""),
                "quantite": im.get("quantite", 0),
                "valeur_actuelle": valeur_actuelle,
                "duree_vie_restante": im.get("duree_vie_restante", 0),
                "amortissement": amortissement,
                "non_amortissable": non_amortissable,
            })
            total_valeur_achat += valeur_achat
            total_valeur_actuelle += valeur_actuelle
            total_amortissement += amortissement

    return {
        "lignes": lignes,
        "totaux": {
            "valeur_achat": total_valeur_achat,
            "valeur_actuelle": total_valeur_actuelle,
            "amortissement": total_amortissement,
        },
    }


def render_tableau_amortissements(diagnostic: dict, lang: str):
    ent = diagnostic.get("entreprise", {})
    immos = ent.get("immobilisations", [])

    st.markdown(f"### {t('amortissements_title', lang)}")
    st.caption(t("amortissements_help", lang))

    if not immos:
        st.info(t("amortissements_no_data", lang))
        return

    if st.button(t("amortissements_generate_button", lang), key="amort_generate_btn"):
        st.session_state["amortissements_generated"] = True

    if not st.session_state.get("amortissements_generated"):
        return

    results = compute_tableau_amortissements(diagnostic)

    headers = [
        t("immo_categorie", lang), t("immo_valeur_achat", lang), t("immo_annee", lang),
        t("immo_quantite", lang), t("immo_valeur_actuelle", lang), t("immo_duree", lang),
        t("immo_amortissement", lang),
    ]

    rows = []
    for l in results["lignes"]:
        amort_display = t("amortissements_non_amortissable", lang) if l["non_amortissable"] \
            else f"{format_money(l['amortissement'])}"
        rows.append({
            headers[0]: l["categorie"],
            headers[1]: f"{format_money(l['valeur_achat'])}",
            headers[2]: l["annee_acquisition"],
            headers[3]: l["quantite"],
            headers[4]: f"{format_money(l['valeur_actuelle'])}",
            headers[5]: l["duree_vie_restante"],
            headers[6]: amort_display,
        })

    st.table(rows)

    totaux = results["totaux"]
    c1, c2, c3 = st.columns(3)
    c1.metric(t("amortissements_total_valeur_achat", lang), f"{format_money(totaux['valeur_achat'])}")
    c2.metric(t("amortissements_total_valeur_actuelle", lang), f"{format_money(totaux['valeur_actuelle'])}")
    c3.metric(t("amortissements_total_amortissement", lang), f"{format_money(totaux['amortissement'])}")
    st.caption(t("amortissements_foncier_note", lang))
