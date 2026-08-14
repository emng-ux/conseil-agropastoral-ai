"""Matrice d'Ansoff : propose les 4 options de croissance et une recommandation
indicative basée sur le diagnostic (marché, finances, performances)."""

_OPTIONS = {
    "penetration": {
        "fr": {"nom": "Pénétration de marché", "desc": "Vendre plus des produits actuels sur les marchés actuels."},
        "en": {"nom": "Market penetration", "desc": "Sell more of current products in current markets."},
    },
    "developpement_marche": {
        "fr": {"nom": "Développement de marché", "desc": "Trouver de nouveaux marchés/débouchés pour les produits actuels."},
        "en": {"nom": "Market development", "desc": "Find new markets/outlets for current products."},
    },
    "developpement_produit": {
        "fr": {"nom": "Développement de produit", "desc": "Créer de nouveaux produits/activités pour les marchés actuels."},
        "en": {"nom": "Product development", "desc": "Create new products/activities for current markets."},
    },
    "diversification": {
        "fr": {"nom": "Diversification", "desc": "Nouveaux produits sur de nouveaux marchés (le plus risqué)."},
        "en": {"nom": "Diversification", "desc": "New products in new markets (the riskiest option)."},
    },
}


def compute_ansoff(diagnostic: dict, lang: str = "fr") -> dict:
    etoile = diagnostic.get("etoile", {})
    marche = etoile.get("marche", {})
    finances = etoile.get("finances", {})

    concurrence = marche.get("nombre_concurrents", "")
    tresorerie = finances.get("tresorerie", "")
    acces_financement = finances.get("acces_financement", "")

    recommandation = "penetration"
    if concurrence in ("Très nombreux", "Very many") and tresorerie in ("Excédentaire", "Surplus"):
        recommandation = "developpement_marche"
    elif acces_financement in ("Bon (crédit/épargne accessible)", "Good (credit/savings accessible)"):
        recommandation = "developpement_produit"
    elif tresorerie in ("Tendue", "Tight"):
        recommandation = "penetration"

    options = {}
    for key, val in _OPTIONS.items():
        content = val.get(lang, val["fr"])
        options[key] = {
            "nom": content["nom"],
            "description": content["desc"],
            "recommande": key == recommandation,
        }

    return {"options": options, "recommandation": recommandation}
