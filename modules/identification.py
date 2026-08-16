"""Section 'Identification & localisation' du diagnostic : village, découpage
administratif, contact et coordonnées GPS de l'EFA/OP.

Distinct de l'étoile du conseil (data/schema_etoile_conseil.json) : ce ne sont
pas des données de diagnostic stratégique mais des données d'identification,
stockées séparément dans diagnostic["identification"].

Le contact (adresse, téléphone, email) est une donnée personnelle sensible :
comme pour le nom réel de l'EFA/OP, son affichage est soumis à l'interrupteur
'Afficher les noms' de la barre latérale, avec en plus une case à cocher
'toujours masquer' propre à chaque diagnostic pour une protection renforcée
même quand l'interrupteur global est activé (ex. producteur ayant demandé une
confidentialité stricte de ses coordonnées).
"""
import streamlit as st

from utils.i18n import t


def render_identification_form(diagnostic: dict, lang: str) -> dict:
    ident = diagnostic.setdefault("identification", {})

    col1, col2 = st.columns(2)
    with col1:
        ident["village"] = st.text_input(t("field_village", lang), value=ident.get("village", ""))
        ident["arrondissement"] = st.text_input(t("field_arrondissement", lang),
                                                 value=ident.get("arrondissement", ""))
        ident["code_arrondissement"] = st.text_input(
            t("field_code_arrondissement", lang), value=ident.get("code_arrondissement", ""))
        ident["departement"] = st.text_input(t("field_departement", lang),
                                              value=ident.get("departement", ""))
        ident["code_departement"] = st.text_input(
            t("field_code_departement", lang), value=ident.get("code_departement", ""))
    with col2:
        ident["region"] = st.text_input(t("field_region", lang), value=ident.get("region", ""))
        ident["code_region"] = st.text_input(
            t("field_code_region", lang), value=ident.get("code_region", ""))
        ident["pays"] = st.text_input(t("field_pays", lang), value=ident.get("pays", ""))
        ident["annee"] = st.text_input(t("field_annee", lang), value=ident.get("annee", ""))

    st.markdown(f"**{t('field_gps', lang)}**")
    gps = ident.setdefault("gps", {})
    gcol1, gcol2 = st.columns(2)
    gps["latitude"] = gcol1.number_input(
        t("field_latitude", lang), min_value=-90.0, max_value=90.0,
        value=float(gps.get("latitude") or 0.0), format="%.6f")
    gps["longitude"] = gcol2.number_input(
        t("field_longitude", lang), min_value=-180.0, max_value=180.0,
        value=float(gps.get("longitude") or 0.0), format="%.6f")

    st.markdown(f"**{t('field_contact', lang)}**")
    contact = ident.setdefault("contact", {})
    contact["adresse"] = st.text_input(t("field_contact_adresse", lang), value=contact.get("adresse", ""))
    ccol1, ccol2 = st.columns(2)
    contact["telephone"] = ccol1.text_input(t("field_contact_telephone", lang),
                                             value=contact.get("telephone", ""))
    contact["email"] = ccol2.text_input(t("field_contact_email", lang), value=contact.get("email", ""))
    contact["toujours_masquer"] = st.checkbox(
        t("field_contact_always_mask", lang), value=contact.get("toujours_masquer", False),
        help=t("field_contact_always_mask_help", lang))

    return diagnostic


def identification_completion_ratio(diagnostic: dict) -> float:
    """Estime le taux de remplissage de la section identification (hors GPS/contact,
    facultatifs par nature)."""
    ident = diagnostic.get("identification", {})
    fields = ["village", "arrondissement", "departement", "region", "pays", "annee"]
    filled = sum(1 for f in fields if ident.get(f))
    return round(filled / len(fields), 2)


def contact_is_visible(diagnostic: dict) -> bool:
    """Le contact n'est visible que si le mode 'Afficher les noms' est actif ET
    que le conseiller n'a pas explicitement demandé un masquage permanent pour
    ce diagnostic précis."""
    contact = diagnostic.get("identification", {}).get("contact", {})
    if contact.get("toujours_masquer"):
        return False
    return bool(st.session_state.get("reveal_names"))
