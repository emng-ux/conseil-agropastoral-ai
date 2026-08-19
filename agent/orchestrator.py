"""Orchestrateur agentique V2 : mène une VRAIE conversation multi-tours avec le
conseiller/producteur (texte, et audio transcrit en amont), en utilisant le
tool-calling de l'API Anthropic. L'agent :

1. Reçoit l'historique complet de la conversation + l'état actuel du diagnostic
2. Décide lui-même, à chaque tour, s'il doit :
   - appeler l'outil `update_diagnostic_fields` pour enregistrer des informations
     explicitement mentionnées,
   - appeler l'outil `mark_diagnostic_ready` s'il juge le diagnostic assez complet
     pour lancer l'analyse stratégique,
   - ou simplement répondre en texte (relance, clarification, confirmation).
3. Ne remplit jamais un champ qui n'a pas été mentionné (contrainte donnée au modèle).

N'est actif QUE si une connexion Internet est disponible ET qu'une clé API est
configurée (variable d'environnement ANTHROPIC_API_KEY). En son absence, ou hors
connexion, l'application retombe automatiquement sur le formulaire guidé classique
(modules/collecte.py) — jamais de blocage de l'outil. Rien n'est jamais sauvegardé
sur le diagnostic final sans relecture/validation humaine explicite (voir
modules/plan_strategique.py::validate_plan pour l'étape équivalente côté plan).
"""
import json
import os

from modules.collecte import load_schema

_ANTHROPIC_MODEL = "claude-sonnet-5"
_MAX_TURNS_TOOL_LOOP = 4  # garde-fou : jamais plus de 4 aller-retours d'outils dans un même tour utilisateur


def agent_available() -> bool:
    """L'agent conversationnel nécessite une clé API. Renvoie False sinon
    (l'appelant doit aussi vérifier la connectivité via utils.connectivity.is_online)."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _branch_field_ids(branch: dict) -> list:
    return [f["id"] for f in branch["fields"] if f["type"] != "activity_list"]


def _build_tools() -> list:
    """Construit la définition des outils exposés au modèle. Un outil pour
    `update_diagnostic_fields` (schéma JSON générique branche + champs), plus un
    outil sans argument pour signaler la fin de la collecte."""
    schema = load_schema()["branches"]
    branch_enum = list(schema.keys())

    update_tool = {
        "name": "update_diagnostic_fields",
        "description": (
            "Enregistre une ou plusieurs valeurs de champs de l'étoile du conseil, "
            "UNIQUEMENT pour des informations explicitement mentionnées par l'utilisateur "
            "dans la conversation. N'invente et ne déduis jamais une valeur non dite."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "branch": {"type": "string", "enum": branch_enum,
                           "description": "Branche de l'étoile du conseil concernée."},
                "fields": {
                    "type": "object",
                    "description": "Dictionnaire {id_du_champ: valeur} pour cette branche.",
                },
            },
            "required": ["branch", "fields"],
        },
    }

    ready_tool = {
        "name": "mark_diagnostic_ready",
        "description": (
            "À appeler UNE FOIS que les branches essentielles (au minimum Marché, "
            "Milieu local et Politiques publiques) sont suffisamment renseignées pour "
            "lancer l'analyse stratégique. Ne pas appeler prématurément."
        ),
        "input_schema": {"type": "object", "properties": {}},
    }

    return [update_tool, ready_tool]


def _system_prompt(diagnostic: dict, lang: str) -> str:
    schema = load_schema()["branches"]
    schema_summary = {
        key: {"label": branch["label"].get(lang, branch["label"]["fr"]),
              "fields": _branch_field_ids(branch)}
        for key, branch in schema.items()
    }
    etat_actuel = diagnostic.get("etoile") or {}

    return (
        "Tu es un agent IA qui aide un conseiller agropastoral à mener un entretien "
        "de collecte de diagnostic avec un producteur, selon l'étoile du conseil "
        "(6 branches). Voici le schéma des champs disponibles par branche : "
        f"{json.dumps(schema_summary, ensure_ascii=False)}. "
        f"Voici l'état actuel déjà renseigné du diagnostic : {json.dumps(etat_actuel, ensure_ascii=False)}. "
        "À chaque message, utilise l'outil update_diagnostic_fields pour enregistrer "
        "toute information explicitement mentionnée, puis pose UNE seule question de "
        "relance claire et concrète sur la branche la plus prioritaire encore incomplète. "
        "N'invente jamais de valeur non mentionnée. Reste concis, chaleureux et concret : "
        "tu t'adresses à un conseiller sur le terrain, pas à un développeur. "
        "Quand tu juges que les branches essentielles sont assez renseignées pour lancer "
        "l'analyse stratégique, appelle l'outil mark_diagnostic_ready puis dis-le clairement "
        f"à l'utilisateur. Réponds toujours en {'français' if lang == 'fr' else 'anglais'}."
    )


def run_turn(conversation_history: list, user_message: str, diagnostic: dict,
             lang: str = "fr") -> dict:
    """Exécute un tour complet de conversation agentique.

    `conversation_history` : liste de messages au format API Anthropic
    (accumulée par l'appelant entre les tours, ex. st.session_state.chat_history).

    Retourne {"reply": str, "updates_applied": {branche: {champ: valeur}, ...},
              "ready_for_analysis": bool, "conversation_history": list_mise_a_jour}.

    Lève une exception si l'appel API échoue (l'appelant doit gérer le repli gracieux
    vers le formulaire classique — voir modules/collecte.py)."""
    import anthropic  # import local : dépendance optionnelle, seulement utile en ligne

    client = anthropic.Anthropic()
    tools = _build_tools()
    messages = list(conversation_history) + [{"role": "user", "content": user_message}]

    updates_applied = {}
    ready_for_analysis = False
    reply_text = ""

    for _ in range(_MAX_TURNS_TOOL_LOOP):
        response = client.messages.create(
            model=_ANTHROPIC_MODEL,
            max_tokens=1000,
            system=_system_prompt(diagnostic, lang),
            tools=tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        text_blocks = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        reply_text += ("\n".join(text_blocks))

        tool_use_blocks = [b for b in response.content if getattr(b, "type", "") == "tool_use"]

        if not tool_use_blocks:
            break  # le modèle a fini de répondre pour ce tour

        tool_results = []
        for block in tool_use_blocks:
            if block.name == "update_diagnostic_fields":
                branch = block.input.get("branch")
                fields = block.input.get("fields", {})
                if branch:
                    updates_applied.setdefault(branch, {}).update(fields)
                    diagnostic.setdefault("etoile", {}).setdefault(branch, {}).update(fields)
                result_text = "OK, champs enregistrés."
            elif block.name == "mark_diagnostic_ready":
                ready_for_analysis = True
                result_text = "OK, diagnostic marqué prêt pour analyse."
            else:
                result_text = "Outil inconnu."

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })

        messages.append({"role": "user", "content": tool_results})

        if response.stop_reason != "tool_use":
            break

    return {
        "reply": reply_text.strip(),
        "updates_applied": updates_applied,
        "ready_for_analysis": ready_for_analysis,
        "conversation_history": messages,
    }
