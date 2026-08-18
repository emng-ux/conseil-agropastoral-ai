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

    if st.button(t("histoire_add", lang), key="ent_histoire_add"):
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
        cols = st.columns([2, 2, 2, 2])
        p["nom"] = cols[0].text_input(t("parcelle_nom", lang), value=p.get("nom", ""), key=f"pc_nom_{i}")
        p["site"] = cols[1].text_input(t("parcelle_site", lang), value=p.get("site", ""),
                                        help=t("parcelle_site_help", lang), key=f"pc_site_{i}")
        p["zonage"] = cols[2].text_input(t("parcelle_zonage", lang), value=p.get("zonage", ""),
                                          key=f"pc_zonage_{i}")
        p["utilisation"] = cols[3].text_input(t("parcelle_utilisation", lang), value=p.get("utilisation", ""),
                                               key=f"pc_util_{i}")
        cols2 = st.columns([2, 2, 2, 1])
        p["production"] = cols2[0].text_input(t("parcelle_production", lang), value=p.get("production", ""),
                                               key=f"pc_prod_{i}")
        p["surface"] = cols2[1].number_input(t("parcelle_surface", lang), min_value=0.0,
                                              value=float(p.get("surface", 0.0)), key=f"pc_surf_{i}")
        statut_options = t("parcelle_statut_options", lang).split(",")
        current = p.get("statut", statut_options[0])
        idx = statut_options.index(current) if current in statut_options else 0
        p["statut"] = cols2[2].selectbox(t("parcelle_statut", lang), statut_options, index=idx,
                                          key=f"pc_statut_{i}")
        p["mise_en_valeur"] = cols2[3].checkbox(t("parcelle_mise_en_valeur", lang),
                                                 value=p.get("mise_en_valeur", True), key=f"pc_mev_{i}")
        if st.button(t("remove", lang), key=f"pc_rm_{i}"):
            parcelles.pop(i)
            st.rerun()
        st.markdown("---")

    if st.button(t("parcelle_add", lang), key="ent_parcelle_add"):
        parcelles.append({"nom": "", "site": "", "zonage": "", "utilisation": "", "production": "",
                           "surface": 0.0, "statut": t("parcelle_statut_options", lang).split(",")[0],
                           "mise_en_valeur": True})
        st.rerun()


def render_siege_batiments_paysage(diagnostic: dict, lang: str):
    """Siège de l'EFA/OP, bâtiments d'exploitation, et éléments du paysage —
    utilisés par le générateur de schéma pour positionner l'exploitation dans
    son environnement (au-delà des seules parcelles cultivées)."""
    ent = _entreprise(diagnostic)

    st.markdown(f"**{t('siege_title', lang)}**")
    st.caption(t("siege_help", lang))
    siege = ent.setdefault("siege", {})
    sc1, sc2 = st.columns(2)
    siege["nom"] = sc1.text_input(t("siege_nom", lang), value=siege.get("nom", ""), key="siege_nom")
    siege["site"] = sc2.text_input(t("parcelle_site", lang), value=siege.get("site", ""),
                                    help=t("parcelle_site_help", lang), key="siege_site")
    siege["description"] = st.text_area(t("siege_description", lang), value=siege.get("description", ""),
                                         key="siege_desc")

    st.markdown(f"**{t('batiments_title', lang)}**")
    st.caption(t("batiments_help", lang))
    batiments = ent.setdefault("batiments", [])
    for i, b in enumerate(list(batiments)):
        cols = st.columns([2, 2, 2, 1])
        b["type"] = cols[0].text_input(t("batiment_type", lang), value=b.get("type", ""), key=f"bat_type_{i}")
        usage_options = t("batiment_usage_options", lang).split(",")
        cur = b.get("usage", usage_options[0])
        idx = usage_options.index(cur) if cur in usage_options else 0
        b["usage"] = cols[1].selectbox(t("batiment_usage", lang), usage_options, index=idx, key=f"bat_usage_{i}")
        b["site"] = cols[2].text_input(t("parcelle_site", lang), value=b.get("site", ""), key=f"bat_site_{i}")
        if cols[3].button(t("remove", lang), key=f"bat_rm_{i}"):
            batiments.pop(i)
            st.rerun()
    if st.button(t("batiment_add", lang), key="ent_batiment_add"):
        batiments.append({"type": "", "usage": t("batiment_usage_options", lang).split(",")[0], "site": ""})
        st.rerun()

    st.markdown(f"**{t('paysage_title', lang)}**")
    st.caption(t("paysage_help", lang))
    paysage = ent.setdefault("paysage", [])
    for i, pa in enumerate(list(paysage)):
        cols = st.columns([2, 2, 2, 1])
        pa["element"] = cols[0].text_input(t("paysage_element", lang), value=pa.get("element", ""),
                                            key=f"pay_elem_{i}")
        pa["utilisation"] = cols[1].text_input(t("paysage_utilisation", lang), value=pa.get("utilisation", ""),
                                                key=f"pay_util_{i}")
        pa["site"] = cols[2].text_input(t("parcelle_site", lang), value=pa.get("site", ""), key=f"pay_site_{i}")
        if cols[3].button(t("remove", lang), key=f"pay_rm_{i}"):
            paysage.pop(i)
            st.rerun()
    if st.button(t("paysage_add", lang), key="ent_paysage_add"):
        paysage.append({"element": "", "utilisation": "", "site": ""})
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

    if st.button(t("calendrier_add", lang), key="ent_calendrier_add"):
        calendrier.append({"activite": "", "type": t("calendrier_type_options", lang).split(",")[0], "mois": []})
        st.rerun()


# ---------------------------------------------------------------------------
# 5 & 6. Activités de l'entreprise (schéma de fonctionnement + description +
# performances technico-économiques, avec calcul automatique des marges)
# ---------------------------------------------------------------------------
def compute_marge_brute(act: dict) -> float:
    """Marge brute de l'activité, hors coût de la main d'œuvre (propre) et hors
    coût du travail par entreprise/tiers — ces deux coûts sont saisis
    séparément et jamais inclus dans les charges opérationnelles."""
    return float(act.get("produit_brut", 0) or 0) - float(act.get("charges_operationnelles", 0) or 0)


def compute_marge_directe(act: dict) -> float:
    return float(act.get("produit_brut", 0) or 0) - float(act.get("charges_directes", 0) or 0)


def compute_valeur_ajoutee(act: dict) -> float:
    """Valeur ajoutée de l'activité = Produits - Charges opérationnelles -
    Coût du travail par entreprise/tiers (consommation intermédiaire externe).
    Le coût de la main d'œuvre PROPRE n'est volontairement PAS déduit : il
    s'agit d'une rémunération financée par la valeur ajoutée, pas d'une
    consommation intermédiaire — logique standard de l'analyse économique
    agricole (conseil de gestion)."""
    produit_brut = float(act.get("produit_brut", 0) or 0)
    charges_operationnelles = float(act.get("charges_operationnelles", 0) or 0)
    cout_travail_tiers = float(act.get("cout_travail_tiers", 0) or 0)
    return produit_brut - charges_operationnelles - cout_travail_tiers


def compute_marge_brute_avec_mo_tiers(act: dict) -> float:
    """Marge brute 'stricte', formule de base du référentiel officiel de
    l'observatoire des EFA (ex. Moungo) : Produit brut - Charges
    opérationnelles, où la main d'œuvre ET le travail par entreprise/tiers
    SONT inclus dans la soustraction (contrairement à compute_marge_brute,
    qui présente la variante 'avant main d'œuvre et travaux par tiers'
    utilisée pour comparer des EFA aux structures de main d'œuvre différentes)."""
    produit_brut = float(act.get("produit_brut", 0) or 0)
    charges_operationnelles = float(act.get("charges_operationnelles", 0) or 0)
    cout_main_oeuvre = float(act.get("cout_main_oeuvre", 0) or 0)
    cout_travail_tiers = float(act.get("cout_travail_tiers", 0) or 0)
    return produit_brut - charges_operationnelles - cout_main_oeuvre - cout_travail_tiers


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
                value=float(act.get("produit_brut", 0.0)), help=t("activite_produit_brut_help", lang),
                key=f"act_pb_{i}")
            act["charges_operationnelles"] = mcol1.number_input(
                t("activite_charges_operationnelles", lang), min_value=0.0,
                value=float(act.get("charges_operationnelles", 0.0)),
                help=t("activite_charges_operationnelles_help", lang), key=f"act_co_{i}")
            act["charges_directes"] = mcol2.number_input(
                t("activite_charges_directes", lang), min_value=0.0,
                value=float(act.get("charges_directes", 0.0)), key=f"act_cd_{i}")
            act["cout_main_oeuvre"] = mcol1.number_input(
                t("activite_cout_mo", lang), min_value=0.0,
                value=float(act.get("cout_main_oeuvre", 0.0)), help=t("activite_cout_mo_help", lang),
                key=f"act_cmo_{i}")
            act["cout_travail_tiers"] = mcol2.number_input(
                t("activite_cout_tiers", lang), min_value=0.0,
                value=float(act.get("cout_travail_tiers", 0.0)), help=t("activite_cout_tiers_help", lang),
                key=f"act_ctiers_{i}")

            marge_brute_avant = compute_marge_brute(act)
            marge_brute_avec = compute_marge_brute_avec_mo_tiers(act)
            marge_directe = compute_marge_directe(act)
            valeur_ajoutee = compute_valeur_ajoutee(act)

            st.caption(t("activite_marge_brute_avant_label", lang))
            r1, r2 = st.columns(2)
            r1.metric(t("activite_marge_brute", lang), f"{marge_brute_avant:,.0f}")
            r2.metric(t("activite_valeur_ajoutee", lang), f"{valeur_ajoutee:,.0f}")

            st.caption(t("activite_marge_brute_avec_label", lang))
            r3, r4 = st.columns(2)
            r3.metric(t("activite_marge_brute_avec_mo", lang), f"{marge_brute_avec:,.0f}")
            r4.metric(t("activite_marge_directe", lang), f"{marge_directe:,.0f}")

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

    if st.button(t("activite_add", lang), key="ent_activite_add"):
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

    if st.button(t("immo_add", lang), key="ent_immo_add"):
        immos.append({"categorie": t("immo_categories", lang).split(",")[0]})
        st.rerun()


def compute_diagnostic_financier(diagnostic: dict) -> dict:
    ent = diagnostic.get("entreprise", {})
    activites = ent.get("activites", [])
    marge_brute_globale = sum(compute_marge_brute(a) for a in activites)
    marge_brute_avec_mo_globale = sum(compute_marge_brute_avec_mo_tiers(a) for a in activites)
    valeur_ajoutee_globale = sum(compute_valeur_ajoutee(a) for a in activites)
    df = ent.setdefault("diagnostic_financier", {})
    charges_structure = float(df.get("charges_structure", 0) or 0)
    annuites = float(df.get("annuites_remboursement", 0) or 0)
    ebe = marge_brute_globale - charges_structure
    marge_securite = ebe - annuites
    return {
        "marge_brute_globale": marge_brute_globale,
        "marge_brute_avec_mo_globale": marge_brute_avec_mo_globale,
        "valeur_ajoutee_globale": valeur_ajoutee_globale,
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
    r4, r5 = st.columns(2)
    r4.metric(t("diag_fin_marge_brute_avec_mo_globale", lang), f"{results['marge_brute_avec_mo_globale']:,.0f}")
    r5.metric(t("diag_fin_valeur_ajoutee_globale", lang), f"{results['valeur_ajoutee_globale']:,.0f}")
    st.metric(t("diag_fin_valeur_ajoutee_globale", lang), f"{results['valeur_ajoutee_globale']:,.0f}")

    render_immobilisations(diagnostic, lang)


# La fonction render_bilan (bilan comptable structuré, FDR/BFR, tableau de
# financement) a été déplacée dans modules/bilan.py pour plus de clarté,
# vu son ampleur. Voir app.py : `from modules.bilan import render_bilan`.
