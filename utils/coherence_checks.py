"""Détecte les données incohérentes ou aberrantes dans un diagnostic — 100%
Python déterministe, sans IA, pour une fiabilité et une reproductibilité
totales. Complète les calculs financiers déjà entièrement réalisés en Python
pur ailleurs dans l'application (marges, EBE, bilan, FDR/BFR, plan de
financement — voir modules/entreprise.py, modules/bilan.py,
modules/plan_financement.py, modules/amortissements.py).

Chaque vérification retourne une liste d'anomalies {niveau, message}, où
niveau est "erreur" (incohérence logique/mathématique certaine) ou
"avertissement" (valeur suspecte, à vérifier mais pas nécessairement fausse).
"""
from datetime import datetime


def _add(anomalies: list, niveau: str, message: str) -> None:
    anomalies.append({"niveau": niveau, "message": message})


def check_parcelles(diagnostic: dict) -> list:
    anomalies = []
    parcelles = (diagnostic.get("entreprise") or {}).get("parcelles") or []
    noms_vus = {}
    for p in parcelles:
        nom = p.get("nom") or "(sans nom)"
        surface = p.get("surface")
        try:
            surface = float(surface or 0)
        except (TypeError, ValueError):
            surface = 0.0
        if surface < 0:
            _add(anomalies, "erreur", f"Parcelle « {nom} » : surface négative ({surface} ha) — impossible.")
        elif surface == 0:
            _add(anomalies, "avertissement", f"Parcelle « {nom} » : surface à zéro — à vérifier.")
        elif surface > 1000:
            _add(anomalies, "avertissement",
                 f"Parcelle « {nom} » : surface très élevée ({surface:g} ha) — à confirmer.")
        noms_vus[nom] = noms_vus.get(nom, 0) + 1
    for nom, count in noms_vus.items():
        if count > 1 and nom != "(sans nom)":
            _add(anomalies, "avertissement", f"Parcelle « {nom} » apparaît {count} fois — doublon possible.")
    return anomalies


def check_activites(diagnostic: dict) -> list:
    from modules.entreprise import compute_marge_brute, compute_marge_brute_avec_mo_tiers, compute_valeur_ajoutee
    anomalies = []
    activites = (diagnostic.get("entreprise") or {}).get("activites") or []
    for a in activites:
        nom = a.get("nom") or "(activité sans nom)"
        produit_brut = float(a.get("produit_brut", 0) or 0)
        if produit_brut < 0:
            _add(anomalies, "erreur", f"Activité « {nom} » : produit brut négatif — impossible.")

        mb_avant = compute_marge_brute(a)
        mb_avec = compute_marge_brute_avec_mo_tiers(a)
        va = compute_valeur_ajoutee(a)
        # Cohérence mathématique attendue entre les 3 indicateurs (voir
        # modules/entreprise.py) : mb_avec ≤ va ≤ mb_avant, toujours.
        if not (mb_avec <= va + 0.01 and va <= mb_avant + 0.01):
            _add(anomalies, "erreur",
                 f"Activité « {nom} » : incohérence entre marge brute, valeur ajoutée et marge "
                 f"brute avec main d'œuvre — vérifier les charges saisies.")
        if produit_brut > 0 and mb_avant > produit_brut:
            _add(anomalies, "erreur",
                 f"Activité « {nom} » : la marge brute dépasse le produit brut — impossible "
                 f"(charges négatives ?).")
    return anomalies


def check_immobilisations(diagnostic: dict) -> list:
    anomalies = []
    immos = (diagnostic.get("entreprise") or {}).get("immobilisations") or []
    annee_courante = datetime.now().year
    for im in immos:
        categorie = im.get("categorie") or "(catégorie inconnue)"
        annee_acq = im.get("annee_acquisition")
        try:
            annee_acq_int = int(annee_acq)
            if annee_acq_int > annee_courante:
                _add(anomalies, "erreur",
                     f"Immobilisation « {categorie} » : année d'acquisition ({annee_acq_int}) dans le futur.")
            elif annee_acq_int < 1950:
                _add(anomalies, "avertissement",
                     f"Immobilisation « {categorie} » : année d'acquisition ({annee_acq_int}) très ancienne.")
        except (TypeError, ValueError):
            pass

        valeur_achat = float(im.get("valeur_achat", 0) or 0)
        valeur_actuelle = float(im.get("valeur_actuelle", 0) or 0)
        if valeur_actuelle > valeur_achat > 0:
            _add(anomalies, "avertissement",
                 f"Immobilisation « {categorie} » : valeur actuelle ({valeur_actuelle:g}) supérieure "
                 f"à la valeur d'achat ({valeur_achat:g}) — plausible seulement en cas de forte "
                 f"plus-value (foncier), à confirmer sinon.")

        duree = im.get("duree_vie_restante")
        try:
            if float(duree) < 0:
                _add(anomalies, "erreur",
                     f"Immobilisation « {categorie} » : durée de vie restante négative.")
        except (TypeError, ValueError):
            pass
    return anomalies


def check_bilan(diagnostic: dict) -> list:
    from modules.bilan import _get_periode, compute_totals
    anomalies = []
    for periode_key, periode_label in (("debut", "début (N-1)"), ("fin", "fin (N)")):
        bilan_data = (diagnostic.get("entreprise") or {}).get("bilan") or {}
        p = bilan_data.get(periode_key)
        if not isinstance(p, dict) or "actif" not in p:
            continue
        totals = compute_totals(p)
        ecart = round(totals["total_actif"] - totals["total_passif"], 2)
        if ecart != 0:
            _add(anomalies, "erreur",
                 f"Bilan {periode_label} : déséquilibré (actif − passif = {ecart:,.0f}) — "
                 f"un bilan doit toujours être équilibré (actif = passif).")
    return anomalies


def check_plan_financement(diagnostic: dict) -> list:
    from modules.plan_financement import compute_plan_financement
    anomalies = []
    pf = (diagnostic.get("entreprise") or {}).get("plan_financement")
    if not pf:
        return anomalies
    results = compute_plan_financement(diagnostic)
    ecart = round(results["total_ressources"] - results["total_emplois"], 2)
    if abs(ecart) > 1:
        _add(anomalies, "avertissement",
             f"Plan de financement : ressources et emplois ne s'équilibrent pas (écart de "
             f"{ecart:,.0f}) — vérifier la ligne 'Variation de trésorerie' (E5).")
    return anomalies


def run_all_checks(diagnostic: dict) -> list:
    """Exécute l'ensemble des vérifications et retourne la liste complète des
    anomalies détectées, triées (erreurs d'abord)."""
    anomalies = []
    anomalies += check_parcelles(diagnostic)
    anomalies += check_activites(diagnostic)
    anomalies += check_immobilisations(diagnostic)
    anomalies += check_bilan(diagnostic)
    anomalies += check_plan_financement(diagnostic)
    anomalies.sort(key=lambda a: 0 if a["niveau"] == "erreur" else 1)
    return anomalies
