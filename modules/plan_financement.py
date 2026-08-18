"""Plan de financement (Ressources / Emplois), saisi par catégories détaillées,
avec calcul automatique des totaux, du solde de financement, de 10 indicateurs
financiers, et d'une qualification automatique de la situation.

Distinct du 'tableau de financement' du module bilan.py (qui, lui, est dérivé
automatiquement de la comparaison entre deux bilans). Celui-ci est renseigné
directement par le conseiller selon des catégories de ressources et d'emplois
plus larges (financement, investissement, exploitation, trésorerie...), pour
une vision de type plan de financement de projet/exercice.
"""
import streamlit as st

RESSOURCES_SCHEMA = {
    "r1": ["epargne", "autofinancement", "benefices_excedents", "apports", "cotisations"],
    "r2": ["banque", "microfinance", "credit_campagne", "credit_fournisseur"],
    "r3": ["etat", "ong", "ptf", "programmes_projets", "dons"],
    "r4": ["ventes", "avances_clients", "cessions_actifs", "autres_recettes"],
    "r5": ["diminution_stocks", "diminution_creances", "augmentation_dettes_fournisseurs"],
}
EMPLOIS_SCHEMA = {
    "e1": ["terrain", "batiments", "materiel", "equipements", "plantations", "cheptel", "infrastructures"],
    "e2": ["stocks", "creances", "avances", "fonds_campagne"],
    "e3": ["remboursement_principal", "remboursement_comptes_associes", "interets"],
    "e4": ["prelevements_familiaux_efa", "ristournes", "distributions_membres_op"],
}

_GROUP_TITLES = {
    "fr": {
        "r1": "R1 — Ressources propres", "r2": "R2 — Crédits et emprunts",
        "r3": "R3 — Subventions et financements de projets", "r4": "R4 — Ressources de l'exploitation",
        "r5": "R5 — Ressources libérées du cycle d'exploitation",
        "e1": "E1 — Investissements", "e2": "E2 — Besoin en fonds de roulement",
        "e3": "E3 — Service de la dette et autres emplois financiers",
        "e4": "E4 — Distribution et prélèvements", "e5": "E5 — Trésorerie",
    },
    "en": {
        "r1": "R1 — Own resources", "r2": "R2 — Loans and credit",
        "r3": "R3 — Subsidies and project funding", "r4": "R4 — Operating resources",
        "r5": "R5 — Working capital cycle resources released",
        "e1": "E1 — Investments", "e2": "E2 — Working capital requirement",
        "e3": "E3 — Debt service and other financial uses",
        "e4": "E4 — Distributions and withdrawals", "e5": "E5 — Cash position",
    },
}

_ITEM_LABELS = {
    "fr": {
        "epargne": "Épargne", "autofinancement": "Autofinancement",
        "benefices_excedents": "Bénéfices/excédents", "apports": "Apports", "cotisations": "Cotisations",
        "banque": "Banque", "microfinance": "Microfinance", "credit_campagne": "Crédit de campagne",
        "credit_fournisseur": "Crédit fournisseur",
        "etat": "État", "ong": "ONG", "ptf": "PTF", "programmes_projets": "Programmes/projets", "dons": "Dons",
        "ventes": "Ventes", "avances_clients": "Avances clients", "cessions_actifs": "Cessions d'actifs",
        "autres_recettes": "Autres recettes",
        "diminution_stocks": "Diminution des stocks", "diminution_creances": "Diminution des créances",
        "augmentation_dettes_fournisseurs": "Augmentation des dettes fournisseurs",
        "terrain": "Terrain", "batiments": "Bâtiments", "materiel": "Matériel", "equipements": "Équipements",
        "plantations": "Plantations", "cheptel": "Cheptel", "infrastructures": "Infrastructures",
        "stocks": "Stocks", "creances": "Créances", "avances": "Avances", "fonds_campagne": "Fonds de campagne",
        "remboursement_principal": "Remboursement du principal",
        "remboursement_comptes_associes": "Remboursement des comptes associés", "interets": "Intérêts",
        "prelevements_familiaux_efa": "Prélèvements familiaux (EFA)", "ristournes": "Ristournes",
        "distributions_membres_op": "Distributions aux membres (OP)",
        "variation_tresorerie": "Variation de trésorerie (positive ou négative)",
    },
    "en": {
        "epargne": "Savings", "autofinancement": "Self-financing",
        "benefices_excedents": "Profits/surpluses", "apports": "Contributions", "cotisations": "Membership fees",
        "banque": "Bank", "microfinance": "Microfinance", "credit_campagne": "Seasonal credit",
        "credit_fournisseur": "Supplier credit",
        "etat": "Government", "ong": "NGO", "ptf": "Technical & financial partners",
        "programmes_projets": "Programmes/projects", "dons": "Donations",
        "ventes": "Sales", "avances_clients": "Customer advances", "cessions_actifs": "Asset disposals",
        "autres_recettes": "Other income",
        "diminution_stocks": "Decrease in stocks", "diminution_creances": "Decrease in receivables",
        "augmentation_dettes_fournisseurs": "Increase in supplier debt",
        "terrain": "Land", "batiments": "Buildings", "materiel": "Equipment", "equipements": "Machinery",
        "plantations": "Plantations", "cheptel": "Livestock", "infrastructures": "Infrastructure",
        "stocks": "Stocks", "creances": "Receivables", "avances": "Advances",
        "fonds_campagne": "Seasonal working capital",
        "remboursement_principal": "Principal repayment",
        "remboursement_comptes_associes": "Associate account repayment", "interets": "Interest",
        "prelevements_familiaux_efa": "Family withdrawals (AFF)", "ristournes": "Rebates",
        "distributions_membres_op": "Distributions to members (PO)",
        "variation_tresorerie": "Cash position change (positive or negative)",
    },
}


def _pf(diagnostic: dict) -> dict:
    ent = diagnostic.setdefault("entreprise", {})
    pf = ent.setdefault("plan_financement", {})
    pf.setdefault("ressources", {g: {} for g in RESSOURCES_SCHEMA})
    pf.setdefault("emplois", {g: {} for g in EMPLOIS_SCHEMA})
    pf["emplois"].setdefault("e5", {})
    return pf


def render_plan_financement(diagnostic: dict, lang: str):
    pf = _pf(diagnostic)
    labels = _ITEM_LABELS.get(lang, _ITEM_LABELS["fr"])
    titles = _GROUP_TITLES.get(lang, _GROUP_TITLES["fr"])

    st.markdown("#### " + ("💰 Ressources" if lang == "fr" else "💰 Resources"))
    for group_key, items in RESSOURCES_SCHEMA.items():
        with st.expander(titles[group_key], expanded=False):
            group_data = pf["ressources"].setdefault(group_key, {})
            cols = st.columns(2)
            for i, item in enumerate(items):
                col = cols[i % 2]
                group_data[item] = col.number_input(
                    labels.get(item, item), value=float(group_data.get(item, 0.0)),
                    step=1000.0, key=f"pf_r_{group_key}_{item}")

    st.markdown("#### " + ("📤 Emplois" if lang == "fr" else "📤 Uses"))
    for group_key, items in EMPLOIS_SCHEMA.items():
        with st.expander(titles[group_key], expanded=False):
            group_data = pf["emplois"].setdefault(group_key, {})
            cols = st.columns(2)
            for i, item in enumerate(items):
                col = cols[i % 2]
                group_data[item] = col.number_input(
                    labels.get(item, item), value=float(group_data.get(item, 0.0)),
                    step=1000.0, key=f"pf_e_{group_key}_{item}")

    with st.expander(titles["e5"], expanded=False):
        results_preview = compute_plan_financement(diagnostic)
        st.caption(
            ("Suggestion automatique : solde de financement avant trésorerie = "
             f"{results_preview['solde_financement']:,.0f} (tu peux ajuster manuellement)")
            if lang == "fr" else
            ("Automatic suggestion: funding balance before cash = "
             f"{results_preview['solde_financement']:,.0f} (you can override manually)"))
        e5 = pf["emplois"]["e5"]
        default_val = e5.get("variation_tresorerie")
        if default_val is None:
            default_val = results_preview["solde_financement"]
        e5["variation_tresorerie"] = st.number_input(
            labels["variation_tresorerie"], value=float(default_val), step=1000.0, key="pf_e5_variation")


def _sum_group(container: dict, key: str) -> float:
    return sum(float(v or 0) for v in container.get(key, {}).values())


def compute_plan_financement(diagnostic: dict) -> dict:
    pf = diagnostic.get("entreprise", {}).get("plan_financement", {})
    ressources = pf.get("ressources", {})
    emplois = pf.get("emplois", {})

    r1 = _sum_group(ressources, "r1")
    r2 = _sum_group(ressources, "r2")
    r3 = _sum_group(ressources, "r3")
    r4 = _sum_group(ressources, "r4")
    r5 = _sum_group(ressources, "r5")
    total_ressources = r1 + r2 + r3 + r4 + r5

    e1 = _sum_group(emplois, "e1")
    e2 = _sum_group(emplois, "e2")
    e3 = _sum_group(emplois, "e3")
    e4 = _sum_group(emplois, "e4")
    variation_tresorerie = float(emplois.get("e5", {}).get("variation_tresorerie", 0) or 0)

    total_emplois_hors_tresorerie = e1 + e2 + e3 + e4
    solde_financement = total_ressources - total_emplois_hors_tresorerie
    total_emplois = total_emplois_hors_tresorerie + variation_tresorerie

    autofinancement = float(ressources.get("r1", {}).get("autofinancement", 0) or 0)
    besoins_financement = e1 + e2
    taux_autofinancement = (autofinancement / besoins_financement * 100) if besoins_financement else None

    financements_externes = r2 + r3
    taux_financement_externe = (financements_externes / total_ressources * 100) if total_ressources else None

    caf = r1  # capacité d'autofinancement approximée par le total des ressources propres
    annuites_emprunt = e3  # service de la dette (principal + comptes associés + intérêts)
    capacite_remboursement = (caf / annuites_emprunt) if annuites_emprunt else None

    dettes_financieres = r2
    poids_financement_externe = (dettes_financieres / total_ressources) if total_ressources else None

    part_investissements = (e1 / total_emplois) if total_emplois else None
    part_bfr = (e2 / total_emplois) if total_emplois else None

    return {
        "r1": r1, "r2": r2, "r3": r3, "r4": r4, "r5": r5, "total_ressources": total_ressources,
        "e1": e1, "e2": e2, "e3": e3, "e4": e4, "variation_tresorerie": variation_tresorerie,
        "total_emplois_hors_tresorerie": total_emplois_hors_tresorerie, "total_emplois": total_emplois,
        "solde_financement": solde_financement,
        "taux_autofinancement": taux_autofinancement,
        "taux_financement_externe": taux_financement_externe,
        "capacite_remboursement": capacite_remboursement,
        "poids_financement_externe": poids_financement_externe,
        "part_investissements": part_investissements,
        "part_bfr": part_bfr,
    }


def qualifier_situation(results: dict, lang: str = "fr") -> list:
    """Qualification indicative de la situation financière, basée sur des
    seuils usuels d'analyse financière. Reste indicatif : le jugement du
    conseiller prévaut toujours sur ces règles automatiques."""
    qualifs = []
    fr = lang == "fr"

    ta = results["taux_autofinancement"]
    tfe = results["taux_financement_externe"]
    if ta is not None and ta >= 60:
        qualifs.append("Autonomie financière forte" if fr else "Strong financial autonomy")
    elif tfe is not None and tfe >= 60:
        qualifs.append("Dépendance aux financements externes" if fr else "Dependence on external financing")

    if results["solde_financement"] < 0 and results["e1"] > 0:
        qualifs.append("Sous-financement des investissements" if fr else "Underfunded investments")

    if results["variation_tresorerie"] < 0:
        qualifs.append("Tension de trésorerie" if fr else "Cash flow strain")

    pb = results["part_bfr"]
    if pb is not None and pb > 0.4:
        qualifs.append("BFR excessif" if fr else "Excessive working capital requirement")

    cr = results["capacite_remboursement"]
    if cr is not None and cr < 1:
        qualifs.append("Capacité de remboursement insuffisante" if fr else "Insufficient repayment capacity")

    pi = results["part_investissements"]
    if pi is not None and pi < 0.10 and results["total_emplois"] > 0:
        qualifs.append("Capacité d'investissement insuffisante" if fr else "Insufficient investment capacity")

    if not qualifs:
        qualifs.append("Situation financière équilibrée" if fr else "Balanced financial situation")

    return qualifs


def render_resultats_plan_financement(diagnostic: dict, lang: str):
    results = compute_plan_financement(diagnostic)
    fr = lang == "fr"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total ressources" if fr else "Total resources", f"{results['total_ressources']:,.0f}")
    c2.metric("Total emplois" if fr else "Total uses", f"{results['total_emplois']:,.0f}")
    c3.metric("Solde de financement" if fr else "Funding balance", f"{results['solde_financement']:,.0f}")

    c4, c5 = st.columns(2)
    c4.metric("Variation de trésorerie" if fr else "Cash position change",
              f"{results['variation_tresorerie']:,.0f}")
    if round(results['total_ressources'], 2) != round(results['total_emplois'], 2):
        ecart = results['total_ressources'] - results['total_emplois']
        c5.warning((f"Plan non équilibré (écart de {ecart:,.0f})" if fr
                    else f"Plan not balanced (gap of {ecart:,.0f})"))

    st.markdown("##### " + ("Indicateurs" if fr else "Indicators"))
    i1, i2 = st.columns(2)
    ta = results["taux_autofinancement"]
    i1.metric("Taux d'autofinancement" if fr else "Self-financing rate",
              f"{ta:.1f} %" if ta is not None else "—")
    tfe = results["taux_financement_externe"]
    i2.metric("Taux de financement externe" if fr else "External financing rate",
              f"{tfe:.1f} %" if tfe is not None else "—")

    i3, i4 = st.columns(2)
    cr = results["capacite_remboursement"]
    i3.metric("Capacité de remboursement" if fr else "Repayment capacity",
              f"{cr:.2f}" if cr is not None else "—")
    pfe = results["poids_financement_externe"]
    i4.metric("Poids du financement externe" if fr else "External financing weight",
              f"{pfe:.1%}" if pfe is not None else "—")

    i5, i6 = st.columns(2)
    pi = results["part_investissements"]
    i5.metric("Part des investissements" if fr else "Share of investments",
              f"{pi:.1%}" if pi is not None else "—")
    pb = results["part_bfr"]
    i6.metric("Part du financement du cycle d'exploitation" if fr else "Share of working capital financing",
              f"{pb:.1%}" if pb is not None else "—")

    st.markdown("##### " + ("Qualification de la situation" if fr else "Situation assessment"))
    for q in qualifier_situation(results, lang):
        st.markdown(f"- {q}")
    st.caption("⚠️ " + ("Qualification indicative basée sur des seuils standards — le jugement "
                        "professionnel du conseiller reste déterminant." if fr else
                        "Indicative assessment based on standard thresholds — the advisor's "
                        "professional judgement remains essential."))
