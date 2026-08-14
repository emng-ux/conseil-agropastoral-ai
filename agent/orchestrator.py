"""Orchestrateur agentique : mène une conversation avec le conseiller/producteur,
identifie les branches de l'étoile du conseil encore incomplètes, relance sur les
points manquants, et propose des valeurs à insérer dans le formulaire.

N'est actif QUE si une connexion Internet est disponible ET qu'une clé API est
configurée (variable d'environnement ANTHROPIC_API_KEY). En son absence, ou hors
connexion, l'application retombe automatiquement sur le formulaire guidé classique
(modules/collecte.py) — jamais de blocage de l'outil.

Ce module est une V1 volontairement simple (un seul appel outil-par-tour). Il est
conçu pour être étendu vers un agent multi-tours complet (function calling sur les
4 outils d'analyse) dans une itération suivante.
"""
import json
import os

from modules.collecte import load_schema

_ANTHROPIC_MODEL = "claude-sonnet-4-6"


def agent_available() -> bool:
    """L'agent conversationnel nécessite une clé API. Renvoie False sinon
    (l'appelant doit aussi vérifier la connectivité via utils.connectivity.is_online)."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _missing_fields_summary(diagnostic: dict, lang: str) -> str:
    schema = load_schema()["branches"]
    missing = []
    for branch_key, branch in schema.items():
        branch_data = diagnostic.get("etoile", {}).get(branch_key, {})
        for field in branch["fields"]:
            if field["type"] == "activity_list":
                continue
            if not branch_data.get(field["id"]):
                missing.append(field["label"].get(lang, field["label"]["fr"]))
    return ", ".join(missing) if missing else ("Aucun" if lang == "fr" else "None")


def extract_fields_from_message(message: str, diagnostic: dict, lang: str = "fr") -> dict:
    """Envoie le message du conseiller à l'API Anthropic pour en extraire des valeurs
    de champs de l'étoile du conseil, sous forme JSON structurée.

    Retourne un dict {"updates": {branche: {champ: valeur}}, "reply": "texte pour l'utilisateur"}.
    Lève une exception si l'appel échoue (l'appelant doit gérer le repli gracieux)."""
    import anthropic  # import local : dépendance optionnelle, seulement utile en ligne

    client = anthropic.Anthropic()
    schema = load_schema()["branches"]

    system_prompt = (
        "Tu es un assistant qui aide un conseiller agropastoral à remplir un "
        "diagnostic structuré (l'étoile du conseil, 6 branches). "
        "Voici le schéma des champs disponibles (JSON) : "
        f"{json.dumps(schema, ensure_ascii=False)}. "
        "À partir du message de l'utilisateur, extrait uniquement les informations "
        "explicitement mentionnées et retourne UNIQUEMENT un JSON strict de la forme "
        '{"updates": {"<branche>": {"<champ>": "<valeur>"}}, "reply": "<question de relance ou confirmation>"}. '
        f"Réponds en {'français' if lang == 'fr' else 'anglais'}. "
        "Ne remplis jamais un champ qui n'a pas été mentionné."
    )

    response = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": message}],
    )

    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def apply_updates(diagnostic: dict, updates: dict) -> dict:
    etoile = diagnostic.setdefault("etoile", {})
    for branch_key, fields in updates.items():
        branch_data = etoile.setdefault(branch_key, {})
        branch_data.update(fields)
    return diagnostic
