"""Analyse des 5 forces de Porter, à partir des branches 'Marché' et
'Performances technico-économiques'. Heuristiques simples, ajustables par le conseiller."""

_LEVEL_LABELS = {
    "fr": {"faible": "Faible", "moyen": "Moyen", "fort": "Fort"},
    "en": {"faible": "Low", "moyen": "Moderate", "fort": "High"},
}


def _level_label(level: str, lang: str) -> str:
    return _LEVEL_LABELS.get(lang, _LEVEL_LABELS["fr"]).get(level, level)


def compute_porter(diagnostic: dict, lang: str = "fr") -> dict:
    marche = diagnostic.get("etoile", {}).get("marche", {})

    # Intensité concurrentielle
    concurrents = marche.get("nombre_concurrents", "")
    concurrence_level = {"Peu nombreux": "faible", "Few": "faible",
                          "Nombre moyen": "moyen", "Moderate number": "moyen",
                          "Très nombreux": "fort", "Very many": "fort"}.get(concurrents, "moyen")

    # Pouvoir de négociation des clients (acheteurs) = inverse du pouvoir de négo du producteur
    pouvoir_prod = marche.get("pouvoir_negociation", "")
    pouvoir_clients = {"Fort": "faible", "Strong": "faible",
                        "Moyen": "moyen", "Moderate": "moyen",
                        "Faible": "fort", "Weak": "fort"}.get(pouvoir_prod, "moyen")

    # Menace des nouveaux entrants : approximée par la facilité d'accès au marché (peu de données -> moyen par défaut)
    volatilite = marche.get("volatilite_prix", "")
    nouveaux_entrants = "fort" if volatilite in ("Très volatile", "Highly volatile") else "moyen"

    # Produits de substitution : approximée par la diversification déclarée
    produits_substitution = "moyen"

    # Pouvoir de négociation des fournisseurs (intrants) : approximé via accès aux intrants
    acces_intrants = diagnostic.get("etoile", {}).get("moyens_production", {}).get("acces_intrants", "")
    pouvoir_fournisseurs = {"Facile": "faible", "Easy": "faible",
                             "Moyen": "moyen", "Moderate": "moyen",
                             "Difficile": "fort", "Difficult": "fort"}.get(acces_intrants, "moyen")

    forces = {
        "concurrence": {
            "label": {"fr": "Intensité concurrentielle", "en": "Competitive rivalry"},
            "niveau": concurrence_level,
            "niveau_label": _level_label(concurrence_level, lang),
        },
        "nouveaux_entrants": {
            "label": {"fr": "Menace des nouveaux entrants", "en": "Threat of new entrants"},
            "niveau": nouveaux_entrants,
            "niveau_label": _level_label(nouveaux_entrants, lang),
        },
        "produits_substitution": {
            "label": {"fr": "Menace des produits de substitution", "en": "Threat of substitutes"},
            "niveau": produits_substitution,
            "niveau_label": _level_label(produits_substitution, lang),
        },
        "pouvoir_clients": {
            "label": {"fr": "Pouvoir de négociation des clients", "en": "Bargaining power of buyers"},
            "niveau": pouvoir_clients,
            "niveau_label": _level_label(pouvoir_clients, lang),
        },
        "pouvoir_fournisseurs": {
            "label": {"fr": "Pouvoir de négociation des fournisseurs", "en": "Bargaining power of suppliers"},
            "niveau": pouvoir_fournisseurs,
            "niveau_label": _level_label(pouvoir_fournisseurs, lang),
        },
    }
    return forces
