"""Compile les résultats des 4 outils d'analyse en un plan stratégique et un plan
d'actions. Le téléchargement (module export.py) est bloqué tant que le conseiller
n'a pas explicitement validé le contenu (traçabilité horodatée)."""
from datetime import datetime


def generate_draft_plan(diagnostic: dict, pestel: dict, porter: dict, bcg: list,
                         ansoff: dict, swot: dict = None, lang: str = "fr") -> dict:
    """Génère une proposition initiale de plan, éditable ensuite par le conseiller."""
    orientations = []
    swot = swot or {}

    # Orientations issues du SWOT : capitaliser sur une force pour saisir une opportunité,
    # ou traiter en priorité une faiblesse exposée à une menace.
    forces = swot.get("forces", [])
    faiblesses = swot.get("faiblesses", [])
    opportunites = swot.get("opportunites", [])
    menaces = swot.get("menaces", [])
    if forces and opportunites:
        orientations.append(
            (f"S'appuyer sur les forces identifiées ({forces[0]}) pour saisir l'opportunité : {opportunites[0]}"
             if lang == "fr" else
             f"Leverage identified strengths ({forces[0]}) to seize the opportunity: {opportunites[0]}"))
    if faiblesses and menaces:
        orientations.append(
            (f"Traiter en priorité la faiblesse « {faiblesses[0]} », exposée à la menace : {menaces[0]}"
             if lang == "fr" else
             f"Prioritise addressing the weakness '{faiblesses[0]}', exposed to the threat: {menaces[0]}"))

    # Orientation issue d'Ansoff
    reco_key = ansoff.get("recommandation")
    if reco_key:
        reco = ansoff["options"][reco_key]
        if lang == "fr":
            orientations.append(
                f"Privilégier une stratégie de type « {reco['nom']} » : {reco['description']}")
        else:
            orientations.append(
                f"Prioritise a '{reco['nom']}' strategy: {reco['description']}")

    # Orientation issue de BCG
    vedettes = [a["nom"] for a in bcg if a["quadrant"] == "vedette"]
    poids_morts = [a["nom"] for a in bcg if a["quadrant"] == "poids_mort"]
    if vedettes:
        orientations.append(
            (f"Renforcer les investissements sur les activités « vedettes » : {', '.join(vedettes)}"
             if lang == "fr" else
             f"Reinforce investment in 'star' activities: {', '.join(vedettes)}"))
    if poids_morts:
        orientations.append(
            (f"Réexaminer ou réduire les activités peu rentables : {', '.join(poids_morts)}"
             if lang == "fr" else
             f"Reassess or reduce low-performing activities: {', '.join(poids_morts)}"))

    # Orientation issue de Porter (forces fortes = vigilance)
    forces_fortes = [f["label"].get(lang, f["label"]["fr"]) for f in porter.values() if f["niveau"] == "fort"]
    if forces_fortes:
        orientations.append(
            (f"Développer des mesures pour atténuer les pressions suivantes : {', '.join(forces_fortes)}"
             if lang == "fr" else
             f"Develop measures to mitigate the following pressures: {', '.join(forces_fortes)}"))

    if not orientations:
        orientations.append(
            "Compléter le diagnostic pour affiner les orientations stratégiques." if lang == "fr"
            else "Complete the diagnostic to refine strategic orientations.")

    # Plan d'actions initial (à éditer)
    action_plan = []
    for orientation in orientations:
        action_plan.append({
            "action": orientation[:120],
            "responsable": diagnostic.get("conseiller", ""),
            "echeance": "",
            "indicateur": "",
        })

    return {"orientations": orientations, "action_plan": action_plan}


def validate_plan(diagnostic: dict, validator_name: str) -> dict:
    """Enregistre la validation du conseiller (horodatée) sur le diagnostic."""
    diagnostic["validation"] = {
        "validated_by": validator_name,
        "date": datetime.utcnow().isoformat(),
    }
    return diagnostic


def is_validated(diagnostic: dict) -> bool:
    return bool(diagnostic.get("validation"))
