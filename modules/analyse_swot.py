"""Analyse SWOT / FFOM (Forces, Faiblesses, Opportunités, Menaces).

Combine :
- des données brutes du diagnostic (branches Moyens de production, Performances
  technico-économiques, Finances pour l'interne ; Milieu local, Marché,
  Politiques publiques pour l'externe),
- et, quand ils sont disponibles, les résultats déjà calculés de PESTEL et Porter,
  pour éviter de dupliquer la logique et garder les 4 outils cohérents entre eux.

Fonctionne 100% localement, aucune dépendance réseau.
"""

_LABELS = {
    "forces": {"fr": "Forces", "en": "Strengths"},
    "faiblesses": {"fr": "Faiblesses", "en": "Weaknesses"},
    "opportunites": {"fr": "Opportunités", "en": "Opportunities"},
    "menaces": {"fr": "Menaces", "en": "Threats"},
}


def compute_swot(diagnostic: dict, lang: str = "fr", pestel: dict | None = None,
                  porter: dict | None = None) -> dict:
    etoile = diagnostic.get("etoile", {})
    moyens = etoile.get("moyens_production", {})
    perfs = etoile.get("performances_technico_eco", {})
    finances = etoile.get("finances", {})
    marche = etoile.get("marche", {})
    milieu = etoile.get("milieu_local", {})
    politiques = etoile.get("politiques_publiques", {})

    # Si un diagnostic Word importé contenait déjà une analyse SWOT explicite
    # (sections Forces/Faiblesses/Opportunités/Menaces), on part de celle-ci en
    # priorité, puis on complète avec les déductions automatiques ci-dessous.
    imported = diagnostic.get("swot_import", {})
    forces = list(imported.get("forces", []))
    faiblesses = list(imported.get("faiblesses", []))
    opportunites = list(imported.get("opportunites", []))
    menaces = list(imported.get("menaces", []))

    # --- Interne : Moyens de production ---
    if moyens.get("acces_eau") in ("Irrigation disponible", "Irrigation available"):
        forces.append("Accès à l'irrigation" if lang == "fr" else "Access to irrigation")
    if moyens.get("acces_intrants") in ("Difficile", "Difficult"):
        faiblesses.append("Accès difficile aux intrants" if lang == "fr" else "Difficult access to inputs")
    if moyens.get("equipements"):
        forces.append(
            f"Équipements disponibles : {moyens['equipements']}" if lang == "fr"
            else f"Available equipment: {moyens['equipements']}")

    # --- Interne : Performances technico-économiques ---
    if perfs.get("itineraires_techniques") in ("Non conforme", "Not compliant"):
        faiblesses.append(
            "Itinéraires techniques non conformes aux bonnes pratiques" if lang == "fr"
            else "Technical itineraries not compliant with best practice")
    elif perfs.get("itineraires_techniques") in ("Conforme aux bonnes pratiques",
                                                  "Compliant with best practice"):
        forces.append(
            "Bonnes pratiques techniques respectées" if lang == "fr"
            else "Good technical practices followed")
    taux_perte = perfs.get("taux_perte_post_recolte", 0)
    try:
        if float(taux_perte) >= 15:
            faiblesses.append(
                f"Pertes post-récolte élevées ({taux_perte}%)" if lang == "fr"
                else f"High post-harvest losses ({taux_perte}%)")
    except (TypeError, ValueError):
        pass

    # --- Interne : Finances ---
    if finances.get("tresorerie") in ("Excédentaire", "Surplus"):
        forces.append("Trésorerie excédentaire" if lang == "fr" else "Cash surplus")
    elif finances.get("tresorerie") in ("Tendue", "Tight"):
        faiblesses.append("Trésorerie tendue" if lang == "fr" else "Tight cash flow")
    if finances.get("acces_financement") in ("Faible/inexistant", "Low/none"):
        faiblesses.append(
            "Accès au financement faible ou inexistant" if lang == "fr"
            else "Low or no access to financing")

    # --- Externe : Marché ---
    if marche.get("pouvoir_negociation") in ("Fort", "Strong"):
        forces.append(
            "Bon pouvoir de négociation face aux acheteurs" if lang == "fr"
            else "Strong bargaining power against buyers")
    elif marche.get("pouvoir_negociation") in ("Faible", "Weak"):
        faiblesses.append(
            "Faible pouvoir de négociation face aux acheteurs" if lang == "fr"
            else "Weak bargaining power against buyers")
    if marche.get("volatilite_prix") in ("Très volatile", "Highly volatile"):
        menaces.append("Forte volatilité des prix" if lang == "fr" else "High price volatility")
    if marche.get("nombre_concurrents") in ("Très nombreux", "Very many"):
        menaces.append("Concurrence locale très forte" if lang == "fr" else "Very strong local competition")
    if marche.get("debouches"):
        opportunites.append(
            f"Débouchés identifiés : {marche['debouches']}" if lang == "fr"
            else f"Identified outlets: {marche['debouches']}")

    # --- Externe : Milieu local ---
    if milieu.get("climat"):
        menaces.append(milieu["climat"])
    if milieu.get("securite_fonciere") in ("Précaire/en litige", "Precarious/disputed"):
        menaces.append(
            "Sécurité foncière précaire" if lang == "fr" else "Precarious land tenure")
    if milieu.get("infrastructures_locales"):
        opportunites.append(milieu["infrastructures_locales"])

    # --- Externe : Politiques publiques ---
    if politiques.get("subventions"):
        opportunites.append(politiques["subventions"])
    if politiques.get("programmes_appui"):
        opportunites.append(politiques["programmes_appui"])
    if politiques.get("fiscalite") in ("Contraignante", "Restrictive"):
        menaces.append("Fiscalité contraignante" if lang == "fr" else "Restrictive taxation")

    # --- Recoupement avec Porter (si déjà calculé) : les forces concurrentielles fortes
    #     deviennent des menaces externes, pour rester cohérent entre les outils ---
    if porter:
        for force in porter.values():
            if force.get("niveau") == "fort":
                label = force["label"].get(lang, force["label"]["fr"])
                menaces.append(label)

    # --- Recoupement avec PESTEL (si déjà calculé) : items légaux/écologiques comme menaces ou opportunités ---
    if pestel:
        for item in pestel.get("ecologique", []):
            if item not in menaces:
                menaces.append(item)
        for item in pestel.get("politique", []):
            if item not in opportunites:
                opportunites.append(item)

    def _dedup(items):
        seen, result = set(), []
        for it in items:
            if it and it not in seen:
                seen.add(it)
                result.append(it)
        return result

    return {
        "forces": _dedup(forces),
        "faiblesses": _dedup(faiblesses),
        "opportunites": _dedup(opportunites),
        "menaces": _dedup(menaces),
    }


def label(key: str, lang: str = "fr") -> str:
    return _LABELS[key].get(lang, _LABELS[key]["fr"])
