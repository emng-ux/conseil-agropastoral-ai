"""Section 'Entreprise' du diagnostic : histoire, environnement externe, plan de
localisation (parcelles), calendrier des activités, description détaillée de
chaque activité (avec calcul automatique des marges), immobilisations et bilan.

Distinct de l'étoile du conseil : ces éléments décrivent l'entreprise (EFA/OP)
en tant que telle, en amont/complément de l'analyse stratégique. Stocké dans
diagnostic["entreprise"].
"""
import streamlit as st

from utils.i18n import t

MOIS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"]
MOIS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _entreprise(diagnostic: dict) -> dict:
    return diagnostic.setdefault("entreprise", {})


# ---------------------------------------------------------------------------
# 1. Histoire de l'entreprise
# ---------------------------------------------------------------------------
def render_histoire(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    st.caption(t("histoire_help", lang))
    histoire = ent.setdefault("histoire", [])

    for i, event in enumerate(list(histoire)):
        cols = st.columns([2, 3, 3, 1])
        event["date"] = cols[0].text_input(t("histoire_date", lang), value=event.get("date", ""),
                                            key=f"hist_date_{i}")
        event["quoi"] = cols[1].text_input(t("histoire_quoi", lang), value=event.get("quoi", ""),
                                            key=f"hist_quoi_{i}")
        event["pourquoi"] = cols[2].text_input(t("histoire_pourquoi", lang), value=event.get("pourquoi", ""),
                                                key=f"hist_pourquoi_{i}")
        if cols[3].button(t("remove", lang), key=f"hist_rm_{i}"):
            histoire.pop(i)
            st.rerun()

    if st.button(t("histoire_add", lang)):
        histoire.append({"date": "", "quoi": "", "pourquoi": ""})
        st.rerun()


# ---------------------------------------------------------------------------
# 2. Entreprise et environnement
# ---------------------------------------------------------------------------
def render_environnement(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    env = ent.setdefault("environnement", {})
    env["marche_clients_concurrents"] = st.text_area(
        t("env_marche", lang), value=env.get("marche_clients_concurrents", ""), height=120)
    env["partenaires_fournisseurs_milieu"] = st.text_area(
        t("env_partenaires", lang), value=env.get("partenaires_fournisseurs_milieu", ""), height=120)


# ---------------------------------------------------------------------------
# 3. Plan de localisation (parcelles)
# ---------------------------------------------------------------------------
def render_parcelles(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    st.caption(t("parcelles_help", lang))
    parcelles = ent.setdefault("parcelles", [])

    for i, p in enumerate(list(parcelles)):
        cols = st.columns([2, 2, 2, 2, 1, 2, 1])
        p["nom"] = cols[0].text_input(t("parcelle_nom", lang), value=p.get("nom", ""), key=f"pc_nom_{i}")
        p["zonage"] = cols[1].text_input(t("parcelle_zonage", lang), value=p.get("zonage", ""),
                                          key=f"pc_zonage_{i}")
        p["utilisation"] = cols[2].text_input(t("parcelle_utilisation", lang), value=p.get("utilisation", ""),
                                               key=f"pc_util_{i}")
        p["production"] = cols[3].text_input(t("parcelle_production", lang), value=p.get("production", ""),
                                              key=f"pc_prod_{i}")
        p["surface"] = cols[4].number_input(t("parcelle_surface", lang), min_value=0.0,
                                             value=float(p.get("surface", 0.0)), key=f"pc_surf_{i}")
        statut_options = t("parcelle_statut_options", lang).split(",")
        current = p.get("statut", statut_options[0])
        idx = statut_options.index(current) if current in statut_options else 0
        p["statut"] = cols[5].selectbox(t("parcelle_statut", lang), statut_options, index=idx,
                                         key=f"pc_statut_{i}")
        p["mise_en_valeur"] = cols[6].checkbox(t("parcelle_mise_en_valeur", lang),
                                                value=p.get("mise_en_valeur", True), key=f"pc_mev_{i}")
        if st.button(t("remove", lang), key=f"pc_rm_{i}"):
            parcelles.pop(i)
            st.rerun()
        st.markdown("---")

    if st.button(t("parcelle_add", lang)):
        parcelles.append({"nom": "", "zonage": "", "utilisation": "", "production": "",
                           "surface": 0.0, "statut": t("parcelle_statut_options", lang).split(",")[0],
                           "mise_en_valeur": True})
        st.rerun()


# ---------------------------------------------------------------------------
# 4. Calendrier annuel des activités
# ---------------------------------------------------------------------------
def render_calendrier(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    st.caption(t("calendrier_help", lang))
    calendrier = ent.setdefault("calendrier", [])
    mois_labels = MOIS if lang == "fr" else MOIS_EN

    for i, act in enumerate(list(calendrier)):
        cols = st.columns([2, 2, 5, 1])
        act["activite"] = cols[0].text_input(t("calendrier_activite", lang), value=act.get("activite", ""),
                                              key=f"cal_act_{i}")
        type_options = t("calendrier_type_options", lang).split(",")
        cur_type = act.get("type", type_options[0])
        idx = type_options.index(cur_type) if cur_type in type_options else 0
        act["type"] = cols[1].selectbox(t("calendrier_type", lang), type_options, index=idx, key=f"cal_type_{i}")
        act["mois"] = cols[2].multiselect(t("calendrier_mois", lang), mois_labels,
                                           default=act.get("mois", []), key=f"cal_mois_{i}")
        if cols[3].button(t("remove", lang), key=f"cal_rm_{i}"):
            calendrier.pop(i)
            st.rerun()

    if st.button(t("calendrier_add", lang)):
        calendrier.append({"activite": "", "type": t("calendrier_type_options", lang).split(",")[0], "mois": []})
        st.rerun()


# ---------------------------------------------------------------------------
# 5 & 6. Activités de l'entreprise (schéma de fonctionnement + description +
# performances technico-économiques, avec calcul automatique des marges)
# ---------------------------------------------------------------------------
def compute_marge_brute(act: dict) -> float:
    return float(act.get("produit_brut", 0) or 0) - float(act.get("charges_operationnelles", 0) or 0)


def compute_marge_directe(act: dict) -> float:
    return float(act.get("produit_brut", 0) or 0) - float(act.get("charges_directes", 0) or 0)


def render_activites(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    st.caption(t("activites_help", lang))
    activites = ent.setdefault("activites", [])

    for i, act in enumerate(list(activites)):
        title = act.get("nom") or t("activite_sans_nom", lang)
        with st.expander(f"🔹 {title}", expanded=not act.get("nom")):
            act["nom"] = st.text_input(t("activite_nom", lang), value=act.get("nom", ""), key=f"act_nom_{i}")
            act["quantites_cles"] = st.text_input(t("activite_quantites_cles", lang),
                                                   value=act.get("quantites_cles", ""), key=f"act_qc_{i}")

            st.markdown(f"**{t('activite_flux', lang)}**")
            fcol1, fcol2 = st.columns(2)
            act["flux_entrants"] = fcol1.text_area(
                t("activite_flux_entrants", lang), value=act.get("flux_entrants", ""),
                help=t("activite_flux_entrants_help", lang), key=f"act_fe_{i}", height=100)
            act["flux_sortants"] = fcol2.text_area(
                t("activite_flux_sortants", lang), value=act.get("flux_sortants", ""),
                help=t("activite_flux_sortants_help", lang), key=f"act_fs_{i}", height=100)

            st.markdown(f"**{t('activite_description', lang)}**")
            act["operations_historique"] = st.text_area(
                t("activite_operations", lang), value=act.get("operations_historique", ""), key=f"act_op_{i}")
            act["finalites_objectifs"] = st.text_input(
                t("activite_finalites", lang), value=act.get("finalites_objectifs", ""), key=f"act_fin_{i}")
            act["liens_interactions"] = st.text_area(
                t("activite_liens", lang), value=act.get("liens_interactions", ""), key=f"act_liens_{i}")
            act["clients"] = st.text_area(t("activite_clients", lang), value=act.get("clients", ""),
                                           key=f"act_clients_{i}")
            act["partenaires_fournisseurs"] = st.text_area(
                t("activite_partenaires", lang), value=act.get("partenaires_fournisseurs", ""),
                key=f"act_part_{i}")
            act["moyens_mobilises"] = st.text_area(
                t("activite_moyens", lang), value=act.get("moyens_mobilises", ""), key=f"act_moy_{i}")
            act["organisation"] = st.text_area(
                t("activite_organisation", lang), value=act.get("organisation", ""), key=f"act_org_{i}")

            st.markdown(f"**{t('activite_technique', lang)}**")
            act["itineraire_technique"] = st.text_area(
                t("activite_itineraire", lang), value=act.get("itineraire_technique", ""),
                help=t("activite_itineraire_help", lang), key=f"act_itk_{i}")
            act["chronogramme"] = st.text_area(
                t("activite_chronogramme", lang), value=act.get("chronogramme", ""),
                help=t("activite_chronogramme_help", lang), key=f"act_chrono_{i}")

            st.markdown(f"**{t('activite_chiffres_cles', lang)}**")
            ccol1, ccol2, ccol3, ccol4 = st.columns(4)
            act["surface"] = ccol1.number_input(t("activite_surface", lang), min_value=0.0,
                                                 value=float(act.get("surface", 0.0)), key=f"act_surf_{i}")
            act["rendement"] = ccol2.number_input(t("activite_rendement", lang), min_value=0.0,
                                                   value=float(act.get("rendement", 0.0)), key=f"act_rdt_{i}")
            act["effectif"] = ccol3.number_input(t("activite_effectif", lang), min_value=0.0,
                                                  value=float(act.get("effectif", 0.0)), key=f"act_eff_{i}")
            act["taux_rendement_transfo"] = ccol4.number_input(
                t("activite_taux_transfo", lang), min_value=0.0, max_value=100.0,
                value=float(act.get("taux_rendement_transfo", 0.0)), key=f"act_taux_{i}")

            ccol5, ccol6, ccol7 = st.columns(3)
            act["quantite_produite"] = ccol5.number_input(
                t("activite_qte_produite", lang), min_value=0.0,
                value=float(act.get("quantite_produite", 0.0)), key=f"act_qp_{i}")
            act["quantite_vendue"] = ccol6.number_input(
                t("activite_qte_vendue", lang), min_value=0.0,
                value=float(act.get("quantite_vendue", 0.0)), key=f"act_qv_{i}")
            act["prix_unitaire"] = ccol7.number_input(
                t("activite_prix_unitaire", lang), min_value=0.0,
                value=float(act.get("prix_unitaire", 0.0)), key=f"act_prix_{i}")

            st.markdown(f"**{t('activite_marges', lang)}**")
            mcol1, mcol2 = st.columns(2)
            act["produit_brut"] = mcol1.number_input(
                t("activite_produit_brut", lang), min_value=0.0,
                value=float(act.get("produit_brut", 0.0)), key=f"act_pb_{i}")
            act["charges_operationnelles"] = mcol1.number_input(
                t("activite_charges_operationnelles", lang), min_value=0.0,
                value=float(act.get("charges_operationnelles", 0.0)), key=f"act_co_{i}")
            act["charges_directes"] = mcol2.number_input(
                t("activite_charges_directes", lang), min_value=0.0,
                value=float(act.get("charges_directes", 0.0)), key=f"act_cd_{i}")

            marge_brute = compute_marge_brute(act)
            marge_directe = compute_marge_directe(act)
            r1, r2 = st.columns(2)
            r1.metric(t("activite_marge_brute", lang), f"{marge_brute:,.0f}")
            r2.metric(t("activite_marge_directe", lang), f"{marge_directe:,.0f}")

            st.markdown(f"**{t('activite_analyse', lang)}**")
            act["points_forts"] = st.text_area(t("activite_points_forts", lang),
                                                value=act.get("points_forts", ""), key=f"act_pf_{i}")
            act["points_a_ameliorer"] = st.text_area(t("activite_points_ameliorer", lang),
                                                       value=act.get("points_a_ameliorer", ""), key=f"act_pa_{i}")
            act["cles_reussite"] = st.text_area(t("activite_cles_reussite", lang),
                                                 value=act.get("cles_reussite", ""), key=f"act_cr_{i}")
            act["risques"] = st.text_area(t("activite_risques", lang), value=act.get("risques", ""),
                                           key=f"act_risq_{i}")

            if st.button(t("remove", lang), key=f"act_rm_{i}"):
                activites.pop(i)
                st.rerun()

    if st.button(t("activite_add", lang)):
        activites.append({"nom": ""})
        st.rerun()


# ---------------------------------------------------------------------------
# 7. Diagnostic économique et financier global
# ---------------------------------------------------------------------------
def render_immobilisations(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    st.caption(t("immo_help", lang))
    immos = ent.setdefault("immobilisations", [])

    for i, im in enumerate(list(immos)):
        cols = st.columns([2, 2, 1, 1, 2, 2, 2, 1])
        cat_options = t("immo_categories", lang).split(",")
        cur = im.get("categorie", cat_options[0])
        idx = cat_options.index(cur) if cur in cat_options else 0
        im["categorie"] = cols[0].selectbox(t("immo_categorie", lang), cat_options, index=idx, key=f"im_cat_{i}")
        im["annee_acquisition"] = cols[1].text_input(t("immo_annee", lang), value=im.get("annee_acquisition", ""),
                                                       key=f"im_annee_{i}")
        im["quantite"] = cols[2].number_input(t("immo_quantite", lang), min_value=0.0,
                                               value=float(im.get("quantite", 0.0)), key=f"im_qte_{i}")
        im["duree_vie_restante"] = cols[3].number_input(t("immo_duree", lang), min_value=0.0,
                                                          value=float(im.get("duree_vie_restante", 0.0)),
                                                          key=f"im_duree_{i}")
        im["valeur_achat"] = cols[4].number_input(t("immo_valeur_achat", lang), min_value=0.0,
                                                   value=float(im.get("valeur_achat", 0.0)), key=f"im_va_{i}")
        im["valeur_actuelle"] = cols[5].number_input(t("immo_valeur_actuelle", lang), min_value=0.0,
                                                      value=float(im.get("valeur_actuelle", 0.0)),
                                                      key=f"im_vac_{i}")
        im["amortissement"] = cols[6].number_input(t("immo_amortissement", lang), min_value=0.0,
                                                     value=float(im.get("amortissement", 0.0)), key=f"im_amo_{i}")
        if cols[7].button(t("remove", lang), key=f"im_rm_{i}"):
            immos.pop(i)
            st.rerun()

    if st.button(t("immo_add", lang)):
        immos.append({"categorie": t("immo_categories", lang).split(",")[0]})
        st.rerun()


def compute_diagnostic_financier(diagnostic: dict) -> dict:
    ent = diagnostic.get("entreprise", {})
    activites = ent.get("activites", [])
    marge_brute_globale = sum(compute_marge_brute(a) for a in activites)
    df = ent.setdefault("diagnostic_financier", {})
    charges_structure = float(df.get("charges_structure", 0) or 0)
    annuites = float(df.get("annuites_remboursement", 0) or 0)
    ebe = marge_brute_globale - charges_structure
    marge_securite = ebe - annuites
    return {
        "marge_brute_globale": marge_brute_globale,
        "charges_structure": charges_structure,
        "ebe": ebe,
        "annuites_remboursement": annuites,
        "marge_securite": marge_securite,
    }


def render_diagnostic_financier(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    df = ent.setdefault("diagnostic_financier", {})

    st.caption(t("diag_fin_help", lang))
    col1, col2 = st.columns(2)
    df["charges_structure"] = col1.number_input(
        t("diag_fin_charges_structure", lang), min_value=0.0,
        value=float(df.get("charges_structure", 0.0)), help=t("diag_fin_charges_structure_help", lang))
    df["annuites_remboursement"] = col2.number_input(
        t("diag_fin_annuites", lang), min_value=0.0, value=float(df.get("annuites_remboursement", 0.0)))
    df["consolidation_fdr"] = st.text_area(t("diag_fin_fdr", lang), value=df.get("consolidation_fdr", ""),
                                            help=t("diag_fin_fdr_help", lang))

    results = compute_diagnostic_financier(diagnostic)
    r1, r2, r3 = st.columns(3)
    r1.metric(t("diag_fin_marge_brute_globale", lang), f"{results['marge_brute_globale']:,.0f}")
    r2.metric(t("diag_fin_ebe", lang), f"{results['ebe']:,.0f}")
    r3.metric(t("diag_fin_marge_securite", lang), f"{results['marge_securite']:,.0f}")

    render_immobilisations(diagnostic, lang)


def render_bilan(diagnostic: dict, lang: str):
    ent = _entreprise(diagnostic)
    bilan = ent.setdefault("bilan", {})
    bilan["date_cloture"] = st.text_input(t("bilan_date_cloture", lang), value=bilan.get("date_cloture", ""))

    st.markdown(f"**{t('bilan_actif', lang)}**")
    actif = bilan.setdefault("actif", [])
    for i, poste in enumerate(list(actif)):
        cols = st.columns([3, 2, 1])
        poste["libelle"] = cols[0].text_input(t("bilan_libelle", lang), value=poste.get("libelle", ""),
                                               key=f"actif_lib_{i}")
        poste["valeur"] = cols[1].number_input(t("bilan_valeur", lang), value=float(poste.get("valeur", 0.0)),
                                                key=f"actif_val_{i}")
        if cols[2].button(t("remove", lang), key=f"actif_rm_{i}"):
            actif.pop(i)
            st.rerun()
    if st.button(t("bilan_add_actif", lang)):
        actif.append({"libelle": "", "valeur": 0.0})
        st.rerun()
    total_actif = sum(float(p.get("valeur", 0) or 0) for p in actif)
    st.metric(t("bilan_total_actif", lang), f"{total_actif:,.0f}")

    st.markdown(f"**{t('bilan_passif', lang)}**")
    passif = bilan.setdefault("passif", [])
    for i, poste in enumerate(list(passif)):
        cols = st.columns([3, 2, 1])
        poste["libelle"] = cols[0].text_input(t("bilan_libelle", lang), value=poste.get("libelle", ""),
                                               key=f"passif_lib_{i}")
        poste["valeur"] = cols[1].number_input(t("bilan_valeur", lang), value=float(poste.get("valeur", 0.0)),
                                                key=f"passif_val_{i}")
        if cols[2].button(t("remove", lang), key=f"passif_rm_{i}"):
            passif.pop(i)
            st.rerun()
    if st.button(t("bilan_add_passif", lang)):
        passif.append({"libelle": "", "valeur": 0.0})
        st.rerun()
    total_passif = sum(float(p.get("valeur", 0) or 0) for p in passif)
    st.metric(t("bilan_total_passif", lang), f"{total_passif:,.0f}")

    if actif and passif and round(total_actif, 2) != round(total_passif, 2):
        st.warning(t("bilan_desequilibre", lang).format(ecart=total_actif - total_passif))
