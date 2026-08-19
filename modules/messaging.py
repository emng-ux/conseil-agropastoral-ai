"""Messagerie bidirectionnelle entre comptes, stockée dans la table Supabase
`messages`. Un message est adressé soit à un destinataire précis, soit à
'TOUS' (diffusion à tout le périmètre visible de l'expéditeur — calculé via
utils.hierarchy.visible_usernames). Actualisation quasi-instantanée côté
interface via un rafraîchissement automatique périodique (voir app.py).
"""
import os
from datetime import datetime

BROADCAST = "TOUS"


def _supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_KEY"))


def _headers() -> dict:
    key = os.environ["SUPABASE_KEY"]
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _base_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/messages"


def messaging_available() -> bool:
    return _supabase_configured()


def send_message(sender: str, recipient: str, body: str) -> None:
    import requests
    payload = {
        "sender": sender,
        "recipient": recipient,  # nom d'utilisateur précis, ou BROADCAST ("TOUS")
        "body": body,
        "created_at": datetime.utcnow().isoformat(),
    }
    resp = requests.post(_base_url(), headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()


def list_messages_for(username: str, current_account: dict = None, all_accounts: list = None) -> list:
    """Messages reçus par `username` : adressés directement à lui, ou en
    diffusion (BROADCAST) par un expéditeur dont le périmètre visible inclut
    `username` (ex. un compte national diffuse vers tout le monde, un compte
    régional diffuse vers sa région). Inclut aussi les messages qu'il a
    lui-même envoyés (pour afficher le fil complet)."""
    import requests
    from utils.hierarchy import visible_usernames

    resp = requests.get(_base_url(), headers=_headers(),
                         params={"select": "*", "order": "created_at.desc", "limit": "200"},
                         timeout=15)
    resp.raise_for_status()
    all_messages = resp.json()

    accounts_by_username = {a["username"]: a for a in (all_accounts or [])}

    result = []
    for m in all_messages:
        if m["sender"] == username or m["recipient"] == username:
            result.append(m)
        elif m["recipient"] == BROADCAST:
            sender_account = accounts_by_username.get(m["sender"])
            if sender_account and all_accounts is not None:
                if username in visible_usernames(sender_account, all_accounts):
                    result.append(m)
    result.sort(key=lambda m: m["created_at"])
    return result
