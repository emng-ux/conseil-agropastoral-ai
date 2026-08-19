"""Matrice BCG, à partir de la liste d'activités/produits saisie dans la branche Marché.
Seuils : part de marché relative >= 1 = forte ; taux de croissance >= 10% = forte."""

_QUADRANT_LABELS = {
    "vedette": {"fr": "Vedette", "en": "Star"},
    "vache_lait": {"fr": "Vache à lait", "en": "Cash cow"},
    "dilemme": {"fr": "Dilemme", "en": "Question mark"},
    "poids_mort": {"fr": "Poids mort", "en": "Dog"},
}

GROWTH_THRESHOLD = 10.0
SHARE_THRESHOLD = 1.0


def _classify(part_marche: float, croissance: float) -> str:
    forte_part = part_marche >= SHARE_THRESHOLD
    forte_croissance = croissance >= GROWTH_THRESHOLD
    if forte_part and forte_croissance:
        return "vedette"
    if forte_part and not forte_croissance:
        return "vache_lait"
    if not forte_part and forte_croissance:
        return "dilemme"
    return "poids_mort"


def compute_bcg(diagnostic: dict, lang: str = "fr") -> list:
    activites = (diagnostic.get("etoile") or {}).get("marche", {}).get("activites", [])
    result = []
    for act in activites:
        nom = act.get("nom", "").strip()
        if not nom:
            continue
        part = float(act.get("part_marche_relative", 1.0))
        croissance = float(act.get("taux_croissance", 0.0))
        quadrant = _classify(part, croissance)
        result.append({
            "nom": nom,
            "part_marche_relative": part,
            "taux_croissance": croissance,
            "quadrant": quadrant,
            "quadrant_label": _QUADRANT_LABELS[quadrant].get(lang, _QUADRANT_LABELS[quadrant]["fr"]),
        })
    return result
