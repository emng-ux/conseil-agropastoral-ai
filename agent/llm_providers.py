"""Abstraction multi-fournisseurs pour l'agent conversationnel : Anthropic
(par défaut), DeepSeek (API compatible OpenAI), ou Ollama en local (serveur
auto-hébergé, également compatible OpenAI depuis les versions récentes).

Le choix du fournisseur est un réglage non sensible (stocké dans
utils.org_settings, modifiable par l'administrateur). Les clés API et
paramètres de connexion, eux, restent dans les secrets Streamlit — jamais
dans la base de données — comme pour ANTHROPIC_API_KEY/SUPABASE_KEY.

Toutes les fonctions de ce module retournent un objet de réponse normalisé
compatible avec le format déjà utilisé par agent/orchestrator.py : un attribut
`.content` (liste de blocs ayant chacun `.type`, et selon le type `.text` ou
`.name`/`.input`/`.id`), et un attribut `.stop_reason` ("tool_use" ou autre).
Le SDK Anthropic renvoie déjà nativement cette forme ; les fournisseurs
compatibles OpenAI (DeepSeek, Ollama) sont convertis vers ce même format.
"""
import json
import os


class _Block:
    def __init__(self, type_, text=None, name=None, input=None, id=None):
        self.type = type_
        self.text = text
        self.name = name
        self.input = input
        self.id = id


class _NormalizedResponse:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


def get_provider() -> str:
    """Fournisseur actif : 'anthropic' (défaut), 'deepseek', ou 'ollama'.

    Priorité à la variable d'environnement LLM_PROVIDER (secrets.toml) si elle
    est explicitement définie — c'est le seul levier disponible en usage local
    sans Supabase (le panneau Administration n'existe alors pas). Sinon, le
    réglage choisi par l'administrateur (utils.org_settings, partagé en ligne)
    prend le relais."""
    env_provider = os.environ.get("LLM_PROVIDER")
    if env_provider:
        return env_provider.lower()
    try:
        from utils.org_settings import get_org_settings
        configured = get_org_settings().get("llm_provider")
        if configured:
            return configured
    except Exception:
        pass
    return "anthropic"


def provider_available() -> bool:
    provider = get_provider()
    if provider == "deepseek":
        return bool(os.environ.get("DEEPSEEK_API_KEY"))
    if provider == "ollama":
        return bool(os.environ.get("OLLAMA_HOST"))
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Conversion du format Anthropic (blocs) vers le format OpenAI-compatible
# ---------------------------------------------------------------------------
def _anthropic_tools_to_openai(tools: list) -> list:
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                               "parameters": t["input_schema"]}} for t in tools]


def _block_type(b):
    return b.get("type") if isinstance(b, dict) else getattr(b, "type", None)


def _block_attr(b, key):
    return b.get(key) if isinstance(b, dict) else getattr(b, key, None)


def _anthropic_messages_to_openai(messages: list, system: str) -> list:
    openai_messages = [{"role": "system", "content": system}]
    for m in messages:
        role, content = m["role"], m["content"]
        if isinstance(content, str):
            openai_messages.append({"role": role, "content": content})
            continue

        tool_result_blocks = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]
        if tool_result_blocks:
            for tr in tool_result_blocks:
                tr_content = tr["content"]
                openai_messages.append({
                    "role": "tool", "tool_call_id": tr["tool_use_id"],
                    "content": tr_content if isinstance(tr_content, str) else json.dumps(tr_content),
                })
            continue

        text_parts, tool_calls = [], []
        for b in content:
            b_type = _block_type(b)
            if b_type == "text":
                text_parts.append(_block_attr(b, "text") or "")
            elif b_type == "tool_use":
                tool_calls.append({
                    "id": _block_attr(b, "id"), "type": "function",
                    "function": {"name": _block_attr(b, "name"),
                                 "arguments": json.dumps(_block_attr(b, "input") or {})},
                })
        msg = {"role": "assistant", "content": "\n".join(text_parts) if text_parts else None}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        openai_messages.append(msg)
    return openai_messages


def _openai_response_to_normalized(resp_json: dict) -> _NormalizedResponse:
    message = resp_json["choices"][0]["message"]
    blocks = []
    if message.get("content"):
        blocks.append(_Block("text", text=message["content"]))
    for tc in message.get("tool_calls") or []:
        try:
            args = json.loads(tc["function"]["arguments"])
        except (json.JSONDecodeError, TypeError):
            args = {}
        blocks.append(_Block("tool_use", name=tc["function"]["name"], input=args, id=tc["id"]))
    stop_reason = "tool_use" if message.get("tool_calls") else "end_turn"
    return _NormalizedResponse(blocks, stop_reason)


def _call_openai_compatible(base_url: str, api_key: str, model: str,
                             system: str, tools: list, messages: list) -> _NormalizedResponse:
    import requests
    payload = {
        "model": model,
        "messages": _anthropic_messages_to_openai(messages, system),
        "tools": _anthropic_tools_to_openai(tools),
        "max_tokens": 1000,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = requests.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers,
                          json=payload, timeout=60)
    resp.raise_for_status()
    return _openai_response_to_normalized(resp.json())


def _call_anthropic(system: str, tools: list, messages: list, model: str):
    import anthropic
    client = anthropic.Anthropic()
    return client.messages.create(model=model, max_tokens=1000, system=system, tools=tools, messages=messages)


def call_model(system: str, tools: list, messages: list):
    """Point d'entrée unique utilisé par agent/orchestrator.py — bascule
    automatiquement selon le fournisseur configuré, sans que le reste du
    code de l'orchestrateur ait à connaître le fournisseur actif."""
    provider = get_provider()
    if provider == "deepseek":
        return _call_openai_compatible(
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            system=system, tools=tools, messages=messages)
    if provider == "ollama":
        return _call_openai_compatible(
            base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/") + "/v1",
            api_key=None,
            model=os.environ.get("OLLAMA_MODEL", "llama3.1"),
            system=system, tools=tools, messages=messages)
    return _call_anthropic(system, tools, messages, model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"))
