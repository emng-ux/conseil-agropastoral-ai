"""Analyse PESTEL, alimentée par les branches 'Milieu local' et 'Politiques publiques'
de l'étoile du conseil. Fonctionne 100% localement, sans dépendance réseau."""

PESTEL_LABELS = {
    "politique": {"fr": "Politique", "en": "Political"},
    "economique": {"fr": "Économique", "en": "Economic"},
    "socioculturel": {"fr": "Socioculturel", "en": "Sociocultural"},
    "technologique": {"fr": "Technologique", "en": "Technological"},
    "ecologique": {"fr": "Écologique", "en": "Ecological"},
    "legal": {"fr": "Légal", "en": "Legal"},
}


def compute_pestel(diagnostic: dict, lang: str = "fr") -> dict:
    etoile = diagnostic.get("etoile", {})
    milieu = etoile.get("milieu_local", {})
    politiques = etoile.get("politiques_publiques", {})
    finances = etoile.get("finances", {})

    result = {key: [] for key in PESTEL_LABELS}

    if politiques.get("subventions"):
        result["politique"].append(politiques["subventions"])
    if politiques.get("programmes_appui"):
        result["politique"].append(politiques["programmes_appui"])

    if finances.get("acces_financement"):
        result["economique"].append(
            f"Accès au financement : {finances['acces_financement']}"
            if lang == "fr" else f"Access to financing: {finances['acces_financement']}")
    if politiques.get("fiscalite"):
        result["economique"].append(
            f"Fiscalité : {politiques['fiscalite']}" if lang == "fr"
            else f"Taxation: {politiques['fiscalite']}")

    if milieu.get("organisation_sociale"):
        result["socioculturel"].append(milieu["organisation_sociale"])

    if milieu.get("infrastructures_locales"):
        result["technologique"].append(milieu["infrastructures_locales"])

    if milieu.get("climat"):
        result["ecologique"].append(milieu["climat"])
    if milieu.get("sols"):
        result["ecologique"].append(milieu["sols"])

    if politiques.get("reglementation"):
        result["legal"].append(politiques["reglementation"])
    if milieu.get("securite_fonciere"):
        result["legal"].append(
            f"Sécurité foncière : {milieu['securite_fonciere']}" if lang == "fr"
            else f"Land tenure security: {milieu['securite_fonciere']}")

    return result
