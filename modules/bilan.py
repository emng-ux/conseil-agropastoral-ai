"""Bilan comptable structuré de l'EFA/OP, avec calcul automatique du fonds de
roulement (FDR), du besoin en fonds de roulement (BFR), et du tableau de
financement de l'exercice (emplois/ressources) entre le bilan de début
(année N-1) et le bilan de fin (année N).

Structure calquée sur la comptabilité de gestion agricole habituelle (plan
comptable OHADA simplifié pour EFA/OP) :

ACTIF
  Immobilisé
    Corporelles : terrains, aménagements fonciers, bâtiments, matériel,
                  plantations pérennes, immobilisations en cours
    Financières : parts sociales, actions
  Circulant
    Stocks (magasin + en terre) : approvisionnements, produits finis,
            animaux (reproducteurs/jeunes/trait), travaux en cours
    Valeurs réalisables : créances, apports EFA→OP non encaissés,
                           avances aux membres
    Valeurs disponibles : caisse, banque, placements

PASSIF
  Capitaux propres (situation nette) : formule différente EFA / OP
  Dettes long et moyen terme : emprunts fonciers, matériel/bâtiment/
                                plantations, autres emprunts
  Dettes court terme : crédits de campagne/microcrédits, dettes
                        fournisseurs/partenaires/État, dettes envers l'OP
  Dettes aux associés ou membres

Toutes les données sont saisies par le conseiller (rien n'est inventé) ;
seuls les totaux, FDR, BFR et le tableau de financement sont calculés.
"""
import streamlit as st

from utils.org_settings import format_money

from utils.i18n import t


def _empty_bilan_periode() -> dict:
    return {
        "actif": {
            "immobilise": {
                "corporelles": {
                    "terrains": 0.0, "amenagements_fonciers": 0.0,
                    "batiments_installations": 0.0, "materiel_outillage": 0.0,
                    "plantations_perennes": 0.0, "immobilisations_en_cours": 0.0,
                },
                "financieres": {"parts_sociales": 0.0, "actions": 0.0},
            },
            "circulant": {
                "stocks": {
                    "approvisionnements": 0.0, "produits_finis": 0.0,
                    "animaux_reproducteurs": 0.0, "animaux_jeunes": 0.0,
                    "animaux_trait": 0.0, "produits_travaux_en_cours": 0.0,
                },
                "valeurs_realisables": {
                    "creances": 0.0, "apports_efa_op_non_encaisse": 0.0,
                    "avances_aux_membres": 0.0,
                },
                "valeurs_disponibles": {"caisse": 0.0, "banque": 0.0, "placements": 0.0},
            },
        },
        "passif": {
            "capitaux_propres": {
                "capital_debut_exercice": 0.0, "subventions_investissement_nettes": 0.0,
                "resultat_exercice": 0.0, "apports": 0.0, "prelevements_prives": 0.0,
                "capital_social_depart": 0.0, "reserves_provisions": 0.0,
                "reserves_annee_n": 0.0,
            },
            "dettes_lt_mt": {
                "emprunts_fonciers": 0.0, "emprunts_materiel_batiment_plantations": 0.0,
                "autres_emprunts": 0.0,
            },
            "dettes_ct": {
                "credits_campagne_microcredits": 0.0,
                "dettes_fournisseurs_partenaires_etat": 0.0, "dettes_aupres_op": 0.0,
            },
            "dettes_associes_membres": 0.0,
        },
    }


def _get_periode(diagnostic: dict, periode: str) -> dict:
    """periode: 'debut' (N-1) ou 'fin' (N)."""
    ent = diagnostic.setdefault("entreprise", {})
    bilan = ent.setdefault("bilan", {})
    if periode not in bilan or not isinstance(bilan.get(periode), dict) or "actif" not in bilan.get(periode, {}):
        bilan[periode] = _empty_bilan_periode()
    return bilan[periode]


def _num(container: dict, key: str, label_key: str, lang: str, widget_key: str, col=st) -> float:
    container[key] = col.number_input(t(label_key, lang), value=float(container.get(key, 0.0)),
                                       step=1000.0, key=widget_key)
    return container[key]


def render_bilan_periode(diagnostic: dict, lang: str, periode: str):
    """Formulaire de saisie d'un bilan (début ou fin d'exercice)."""
    p = _get_periode(diagnostic, periode)
    type_structure = diagnostic.get("type", "")
    is_op = ("OP" in type_structure) or ("PO" in type_structure)

    st.markdown(f"### {t('bilan_actif', lang)}")
    st.markdown(f"**{t('bilan_actif_immobilise', lang)}**")
    st.caption(t("bilan_corporelles", lang))
    corp = p["actif"]["immobilise"]["corporelles"]
    c1, c2, c3 = st.columns(3)
    _num(corp, "terrains", "bilan_terrains", lang, f"{periode}_terrains", c1)
    _num(corp, "amenagements_fonciers", "bilan_amenagements", lang, f"{periode}_amen", c2)
    _num(corp, "batiments_installations", "bilan_batiments", lang, f"{periode}_bat", c3)
    c4, c5, c6 = st.columns(3)
    _num(corp, "materiel_outillage", "bilan_materiel", lang, f"{periode}_mat", c4)
    _num(corp, "plantations_perennes", "bilan_plantations", lang, f"{periode}_plant", c5)
    _num(corp, "immobilisations_en_cours", "bilan_immo_cours", lang, f"{periode}_immocours", c6)

    st.caption(t("bilan_financieres", lang))
    fin = p["actif"]["immobilise"]["financieres"]
    f1, f2 = st.columns(2)
    _num(fin, "parts_sociales", "bilan_parts_sociales", lang, f"{periode}_parts", f1)
    _num(fin, "actions", "bilan_actions", lang, f"{periode}_actions", f2)

    st.markdown(f"**{t('bilan_actif_circulant', lang)}**")
    st.caption(t("bilan_stocks", lang))
    stocks = p["actif"]["circulant"]["stocks"]
    s1, s2, s3 = st.columns(3)
    _num(stocks, "approvisionnements", "bilan_approvisionnements", lang, f"{periode}_appro", s1)
    _num(stocks, "produits_finis", "bilan_produits_finis", lang, f"{periode}_prodfinis", s2)
    _num(stocks, "animaux_reproducteurs", "bilan_animaux_reprod", lang, f"{periode}_animrep", s3)
    s4, s5, s6 = st.columns(3)
    _num(stocks, "animaux_jeunes", "bilan_animaux_jeunes", lang, f"{periode}_animjeun", s4)
    _num(stocks, "animaux_trait", "bilan_animaux_trait", lang, f"{periode}_animtrait", s5)
    _num(stocks, "produits_travaux_en_cours", "bilan_travaux_cours", lang, f"{periode}_travcours", s6)

    st.caption(t("bilan_valeurs_realisables", lang))
    vr = p["actif"]["circulant"]["valeurs_realisables"]
    v1, v2, v3 = st.columns(3)
    _num(vr, "creances", "bilan_creances", lang, f"{periode}_creances", v1)
    _num(vr, "apports_efa_op_non_encaisse", "bilan_apports_non_encaisse", lang, f"{periode}_apportsne", v2)
    _num(vr, "avances_aux_membres", "bilan_avances_membres", lang, f"{periode}_avmemb", v3)

    st.caption(t("bilan_valeurs_disponibles", lang))
    vd = p["actif"]["circulant"]["valeurs_disponibles"]
    d1, d2, d3 = st.columns(3)
    _num(vd, "caisse", "bilan_caisse", lang, f"{periode}_caisse", d1)
    _num(vd, "banque", "bilan_banque", lang, f"{periode}_banque", d2)
    _num(vd, "placements", "bilan_placements", lang, f"{periode}_placements", d3)

    totals = compute_totals(p)
    st.metric(t("bilan_total_actif", lang), f"{format_money(totals['total_actif'])}")

    st.markdown("---")
    st.markdown(f"### {t('bilan_passif', lang)}")
    st.markdown(f"**{t('bilan_capitaux_propres', lang)}**")
    cp = p["passif"]["capitaux_propres"]
    if is_op:
        st.caption(t("bilan_cp_op_help", lang))
        o1, o2 = st.columns(2)
        _num(cp, "capital_social_depart", "bilan_capital_social_depart", lang, f"{periode}_capsoc", o1)
        _num(cp, "reserves_provisions", "bilan_reserves_provisions", lang, f"{periode}_resprov", o2)
        o3, o4 = st.columns(2)
        _num(cp, "subventions_investissement_nettes", "bilan_subventions", lang, f"{periode}_subvop", o3)
        _num(cp, "reserves_annee_n", "bilan_reserves_annee_n", lang, f"{periode}_resN", o4)
    else:
        st.caption(t("bilan_cp_efa_help", lang))
        e1, e2 = st.columns(2)
        _num(cp, "capital_debut_exercice", "bilan_capital_debut", lang, f"{periode}_capdeb", e1)
        _num(cp, "subventions_investissement_nettes", "bilan_subventions", lang, f"{periode}_subvefa", e2)
        e3, e4 = st.columns(2)
        _num(cp, "resultat_exercice", "bilan_resultat_exercice", lang, f"{periode}_resex", e3)
        _num(cp, "apports", "bilan_apports", lang, f"{periode}_apports", e4)
        _num(cp, "prelevements_prives", "bilan_prelevements", lang, f"{periode}_prelev")

    st.markdown(f"**{t('bilan_dettes_lt_mt', lang)}**")
    dlt = p["passif"]["dettes_lt_mt"]
    l1, l2, l3 = st.columns(3)
    _num(dlt, "emprunts_fonciers", "bilan_emprunts_fonciers", lang, f"{periode}_empf", l1)
    _num(dlt, "emprunts_materiel_batiment_plantations", "bilan_emprunts_materiel", lang, f"{periode}_empm", l2)
    _num(dlt, "autres_emprunts", "bilan_autres_emprunts", lang, f"{periode}_empa", l3)

    st.markdown(f"**{t('bilan_dettes_ct', lang)}**")
    dct = p["passif"]["dettes_ct"]
    ct1, ct2, ct3 = st.columns(3)
    _num(dct, "credits_campagne_microcredits", "bilan_credits_campagne", lang, f"{periode}_credcamp", ct1)
    _num(dct, "dettes_fournisseurs_partenaires_etat", "bilan_dettes_fournisseurs", lang, f"{periode}_dettfourn", ct2)
    _num(dct, "dettes_aupres_op", "bilan_dettes_op", lang, f"{periode}_dettop", ct3)

    p["passif"]["dettes_associes_membres"] = st.number_input(
        t("bilan_dettes_associes", lang), value=float(p["passif"].get("dettes_associes_membres", 0.0)),
        step=1000.0, key=f"{periode}_dettassoc")

    st.metric(t("bilan_total_passif", lang), f"{format_money(totals['total_passif'])}")

    if round(totals["total_actif"], 2) != round(totals["total_passif"], 2):
        st.warning(t("bilan_desequilibre", lang).format(ecart=totals["total_actif"] - totals["total_passif"]))

    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("FDR", f"{format_money(totals['fdr'])}")
    r2.metric("BFR", f"{format_money(totals['bfr'])}")
    r3.metric(t("bilan_tresorerie", lang), f"{format_money(totals['tresorerie'])}")


# ---------------------------------------------------------------------------
# Calculs : totaux, FDR, BFR, tableau de financement
# ---------------------------------------------------------------------------
def _sum_dict(d: dict) -> float:
    return sum(float(v or 0) for v in d.values())


def compute_totals(p: dict) -> dict:
    corp = _sum_dict(p["actif"]["immobilise"]["corporelles"])
    fin_immo = _sum_dict(p["actif"]["immobilise"]["financieres"])
    total_actif_immobilise = corp + fin_immo

    stocks = _sum_dict(p["actif"]["circulant"]["stocks"])
    valeurs_realisables = _sum_dict(p["actif"]["circulant"]["valeurs_realisables"])
    valeurs_disponibles = _sum_dict(p["actif"]["circulant"]["valeurs_disponibles"])
    total_actif_circulant = stocks + valeurs_realisables + valeurs_disponibles

    total_actif = total_actif_immobilise + total_actif_circulant

    total_capitaux_propres = _sum_dict(p["passif"]["capitaux_propres"])
    total_dettes_lt_mt = _sum_dict(p["passif"]["dettes_lt_mt"])
    total_dettes_ct = _sum_dict(p["passif"]["dettes_ct"])
    dettes_associes = float(p["passif"].get("dettes_associes_membres", 0) or 0)

    total_passif = total_capitaux_propres + total_dettes_lt_mt + total_dettes_ct + dettes_associes

    fdr = (total_capitaux_propres + total_dettes_lt_mt) - total_actif_immobilise
    bfr = (stocks + valeurs_realisables) - (total_dettes_ct + dettes_associes)
    tresorerie = valeurs_disponibles

    return {
        "total_actif_immobilise": total_actif_immobilise,
        "total_actif_circulant": total_actif_circulant,
        "total_actif": total_actif,
        "total_capitaux_propres": total_capitaux_propres,
        "total_dettes_lt_mt": total_dettes_lt_mt,
        "total_dettes_ct": total_dettes_ct,
        "dettes_associes": dettes_associes,
        "total_passif": total_passif,
        "fdr": fdr,
        "bfr": bfr,
        "tresorerie": tresorerie,
    }


def _flatten(d: dict, prefix: str = "") -> dict:
    items = {}
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(_flatten(v, path))
        else:
            items[path] = float(v or 0)
    return items


# Postes "stables" (partie 1 du tableau de financement) vs "circulants /
# trésorerie" (partie 2). Les clés de dettes_associes_membres et les valeurs
# disponibles sont scalaires (pas de sous-dictionnaire), gérées séparément.
_STABLE_PREFIXES = ("actif.immobilise", "passif.capitaux_propres", "passif.dettes_lt_mt")
_CIRCULANT_PREFIXES = ("actif.circulant.stocks", "actif.circulant.valeurs_realisables",
                       "passif.dettes_ct", "passif.dettes_associes_membres")
_TRESORERIE_PREFIX = "actif.circulant.valeurs_disponibles"

_LABELS_FR = {
    "terrains": "Terrains", "amenagements_fonciers": "Aménagements fonciers",
    "batiments_installations": "Bâtiments, installations", "materiel_outillage": "Matériel, outillage",
    "plantations_perennes": "Plantations pérennes", "immobilisations_en_cours": "Immobilisations en cours",
    "parts_sociales": "Parts sociales", "actions": "Actions",
    "capital_debut_exercice": "Capital début d'exercice",
    "subventions_investissement_nettes": "Subventions d'investissement nettes",
    "resultat_exercice": "Résultat de l'exercice", "apports": "Apports",
    "prelevements_prives": "Prélèvements privés", "capital_social_depart": "Capital social de départ",
    "reserves_provisions": "Réserves et provisions", "reserves_annee_n": "Réserves de l'année N",
    "emprunts_fonciers": "Emprunts fonciers",
    "emprunts_materiel_batiment_plantations": "Emprunts matériel/bâtiment/plantations",
    "autres_emprunts": "Autres emprunts",
    "approvisionnements": "Approvisionnements", "produits_finis": "Produits finis",
    "animaux_reproducteurs": "Animaux reproducteurs", "animaux_jeunes": "Animaux jeunes",
    "animaux_trait": "Animaux de trait", "produits_travaux_en_cours": "Produits et travaux en cours",
    "creances": "Créances", "apports_efa_op_non_encaisse": "Apports EFA→OP non encaissés",
    "avances_aux_membres": "Avances aux membres",
    "credits_campagne_microcredits": "Crédits de campagne/microcrédits",
    "dettes_fournisseurs_partenaires_etat": "Dettes fournisseurs/partenaires/État",
    "dettes_aupres_op": "Dettes auprès de l'OP", "dettes_associes_membres": "Dettes aux associés/membres",
}
_LABELS_EN = {
    "terrains": "Land", "amenagements_fonciers": "Land improvements",
    "batiments_installations": "Buildings, facilities", "materiel_outillage": "Equipment, tools",
    "plantations_perennes": "Perennial plantations", "immobilisations_en_cours": "Assets under construction",
    "parts_sociales": "Cooperative shares", "actions": "Shares",
    "capital_debut_exercice": "Opening capital",
    "subventions_investissement_nettes": "Net investment subsidies",
    "resultat_exercice": "Net income for the year", "apports": "Contributions",
    "prelevements_prives": "Private withdrawals", "capital_social_depart": "Initial share capital",
    "reserves_provisions": "Reserves and provisions", "reserves_annee_n": "Year N reserves",
    "emprunts_fonciers": "Land loans",
    "emprunts_materiel_batiment_plantations": "Equipment/building/plantation loans",
    "autres_emprunts": "Other loans",
    "approvisionnements": "Supplies", "produits_finis": "Finished goods",
    "animaux_reproducteurs": "Breeding animals", "animaux_jeunes": "Young animals",
    "animaux_trait": "Draft animals", "produits_travaux_en_cours": "Work in progress",
    "creances": "Receivables", "apports_efa_op_non_encaisse": "Uncollected AFF→PO contributions",
    "avances_aux_membres": "Member advances",
    "credits_campagne_microcredits": "Seasonal credit/microcredit",
    "dettes_fournisseurs_partenaires_etat": "Supplier/partner/government debts",
    "dettes_aupres_op": "Debts owed to the PO", "dettes_associes_membres": "Debts owed to associates/members",
}


def _label_for(path: str, lang: str) -> str:
    key = path.rsplit(".", 1)[-1]
    labels = _LABELS_FR if lang == "fr" else _LABELS_EN
    return labels.get(key, key)


def compute_tableau_financement(diagnostic: dict) -> dict:
    """Tableau de financement de l'exercice : compare le bilan de début (N-1)
    et le bilan de fin (N), classe chaque variation en Emploi ou Ressource,
    séparément pour les postes stables (partie 1) et circulants (partie 2)."""
    debut = _get_periode(diagnostic, "debut")
    fin = _get_periode(diagnostic, "fin")

    flat_debut = _flatten(debut)
    flat_fin = _flatten(fin)
    all_paths = sorted(set(flat_debut) | set(flat_fin))

    def _classify(paths_filter):
        emplois, ressources = [], []
        for path in all_paths:
            if not path.startswith(paths_filter):
                continue
            delta = flat_fin.get(path, 0) - flat_debut.get(path, 0)
            if abs(delta) < 0.005:
                continue
            is_actif = path.startswith("actif.")
            if is_actif:
                (emplois if delta > 0 else ressources).append((path, abs(delta)))
            else:
                (ressources if delta > 0 else emplois).append((path, abs(delta)))
        return emplois, ressources

    p1_emplois, p1_ressources = _classify(_STABLE_PREFIXES)
    p2_emplois, p2_ressources = _classify(_CIRCULANT_PREFIXES)

    totals_debut = compute_totals(debut)
    totals_fin = compute_totals(fin)

    tresorerie_debut = totals_debut["tresorerie"]
    tresorerie_fin = totals_fin["tresorerie"]
    delta_tresorerie = tresorerie_fin - tresorerie_debut

    return {
        "partie1_emplois": p1_emplois, "partie1_ressources": p1_ressources,
        "partie2_emplois": p2_emplois, "partie2_ressources": p2_ressources,
        "total_p1_emplois": sum(v for _, v in p1_emplois),
        "total_p1_ressources": sum(v for _, v in p1_ressources),
        "total_p2_emplois": sum(v for _, v in p2_emplois),
        "total_p2_ressources": sum(v for _, v in p2_ressources),
        "delta_fdr": totals_fin["fdr"] - totals_debut["fdr"],
        "delta_bfr": totals_fin["bfr"] - totals_debut["bfr"],
        "delta_tresorerie": delta_tresorerie,
        "totals_debut": totals_debut,
        "totals_fin": totals_fin,
    }


def render_bilan(diagnostic: dict, lang: str):
    sub_tabs = st.tabs([t("bilan_tab_debut", lang), t("bilan_tab_fin", lang),
                        t("bilan_tab_financement", lang)])

    with sub_tabs[0]:
        st.caption(t("bilan_debut_help", lang))
        render_bilan_periode(diagnostic, lang, "debut")

    with sub_tabs[1]:
        st.caption(t("bilan_fin_help", lang))
        render_bilan_periode(diagnostic, lang, "fin")

    with sub_tabs[2]:
        st.caption(t("bilan_financement_help", lang))
        results = compute_tableau_financement(diagnostic)

        r1, r2, r3 = st.columns(3)
        r1.metric(t("bilan_delta_fdr", lang), f"{format_money(results['delta_fdr'])}")
        r2.metric(t("bilan_delta_bfr", lang), f"{format_money(results['delta_bfr'])}")
        r3.metric(t("bilan_delta_tresorerie", lang), f"{format_money(results['delta_tresorerie'])}")

        st.markdown(f"#### {t('bilan_partie1', lang)}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{t('bilan_emplois', lang)}**")
            for path, val in results["partie1_emplois"]:
                st.markdown(f"- {_label_for(path, lang)} : {format_money(val)}")
            st.markdown(f"**{t('bilan_total', lang)} : {format_money(results['total_p1_emplois'])}**")
        with c2:
            st.markdown(f"**{t('bilan_ressources', lang)}**")
            for path, val in results["partie1_ressources"]:
                st.markdown(f"- {_label_for(path, lang)} : {format_money(val)}")
            st.markdown(f"**{t('bilan_total', lang)} : {format_money(results['total_p1_ressources'])}**")

        st.markdown(f"#### {t('bilan_partie2', lang)}")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"**{t('bilan_emplois', lang)}**")
            for path, val in results["partie2_emplois"]:
                st.markdown(f"- {_label_for(path, lang)} : {format_money(val)}")
            st.markdown(f"**{t('bilan_total', lang)} : {format_money(results['total_p2_emplois'])}**")
        with c4:
            st.markdown(f"**{t('bilan_ressources', lang)}**")
            for path, val in results["partie2_ressources"]:
                st.markdown(f"- {_label_for(path, lang)} : {format_money(val)}")
            st.markdown(f"**{t('bilan_total', lang)} : {format_money(results['total_p2_ressources'])}**")
