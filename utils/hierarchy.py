"""Gestion des comptes utilisateurs hiérarchiques (National / Régional /
Départemental), stockés dans la table Supabase `users`. Remplace le système
de comptes à plat (secrets [auth_users]) pour les déploiements en ligne — le
mode local sans Supabase retombe sur l'ancien système simple, sans hiérarchie
(voir utils/auth.py).

Chaque compte a :
- Un niveau : "national", "regional", ou "departemental"
- Une région (si régional ou départemental)
- Un département (si départemental)
- Une fonction libre (ex. "Coordonnateur régional", "Chargé du suivi-évaluation")
- Un indicateur is_admin (compte administrateur central, orthogonal au niveau
  géographique — peut créer/gérer tous les comptes)
- Un indicateur is_conseiller (seuls les comptes conseillers créent des
  diagnostics EFA/OP ; les autres niveaux consultent/supervisent)

Règle de visibilité : un compte voit tous les comptes de son niveau et en
dessous, dans son périmètre géographique (national voit tout ; régional voit
sa région et ses départements ; départemental voit son département).
"""
import hashlib
import os

NIVEAUX = ["national", "regional", "departemental"]


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_KEY"))


def _headers() -> dict:
    key = os.environ["SUPABASE_KEY"]
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _base_url() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/users"


def hierarchical_accounts_available() -> bool:
    return _supabase_configured()


def create_account(username: str, password: str, nom_complet: str, fonction: str,
                    niveau: str, region: str = "", departement: str = "",
                    is_admin: bool = False, is_conseiller: bool = False) -> dict:
    """Crée un compte. Lève une exception si l'appel échoue (ex. identifiant
    déjà pris — contrainte d'unicité sur `username` côté base)."""
    import requests
    payload = {
        "username": username,
        "password_hash": _hash_password(password),
        "nom_complet": nom_complet,
        "fonction": fonction,
        "niveau": niveau,
        "region": region or None,
        "departement": departement or None,
        "is_admin": is_admin,
        "is_conseiller": is_conseiller,
        "actif": True,
        "photo_base64": None,
    }
    resp = requests.post(_base_url(), headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()
    return payload


def update_account(username: str, **fields) -> None:
    import requests
    resp = requests.patch(_base_url(), headers=_headers(), params={"username": f"eq.{username}"},
                           json=fields, timeout=15)
    resp.raise_for_status()


def set_password(username: str, new_password: str) -> None:
    update_account(username, password_hash=_hash_password(new_password))


def set_active(username: str, actif: bool) -> None:
    update_account(username, actif=actif)


def set_photo(username: str, photo_base64: str) -> None:
    update_account(username, photo_base64=photo_base64)


def get_account(username: str) -> dict:
    import requests
    resp = requests.get(_base_url(), headers=_headers(),
                         params={"username": f"eq.{username}", "select": "*"}, timeout=15)
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else {}


def list_all_accounts() -> list:
    import requests
    resp = requests.get(_base_url(), headers=_headers(),
                         params={"select": "*", "order": "niveau,region,departement,username"},
                         timeout=15)
    resp.raise_for_status()
    return resp.json()


def authenticate(username: str, password: str) -> dict:
    """Retourne le compte si les identifiants sont valides et le compte actif,
    sinon un dict vide."""
    account = get_account(username)
    if not account or not account.get("actif", True):
        return {}
    if account.get("password_hash") != _hash_password(password):
        return {}
    return account


def visible_usernames(current_account: dict, all_accounts: list = None) -> set:
    """Calcule l'ensemble des identifiants visibles par `current_account`,
    selon la règle : national voit tout ; régional voit sa région (et ses
    départements) ; départemental voit son département. Un compte admin voit
    aussi tout, indépendamment de son niveau."""
    if current_account.get("is_admin"):
        accounts = all_accounts if all_accounts is not None else list_all_accounts()
        return {a["username"] for a in accounts}

    accounts = all_accounts if all_accounts is not None else list_all_accounts()
    niveau = current_account.get("niveau")
    region = current_account.get("region")
    departement = current_account.get("departement")

    visible = set()
    for a in accounts:
        if niveau == "national":
            visible.add(a["username"])
        elif niveau == "regional":
            if a.get("region") == region or a["username"] == current_account["username"]:
                visible.add(a["username"])
        elif niveau == "departemental":
            if a.get("departement") == departement or a["username"] == current_account["username"]:
                visible.add(a["username"])
    return visible
