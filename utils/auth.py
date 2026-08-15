"""Authentification simple par nom d'utilisateur / mot de passe, pour protéger
l'accès à l'app en ligne (Streamlit Cloud). Les comptes autorisés sont définis
dans les secrets Streamlit sous une section [auth_users], sous la forme :

    [auth_users]
    emmanuel = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    conseiller2 = "..."

Chaque valeur est le hash SHA-256 du mot de passe (jamais le mot de passe en
clair). Pour générer un hash à partir d'un mot de passe, exécuter en local :

    python -c "import hashlib; print(hashlib.sha256('votre_mot_de_passe'.encode()).hexdigest())"

Si aucun compte n'est configuré (ex. usage local sans secrets.toml), l'accès
reste ouvert — c'est le comportement attendu pour un usage local/hors-ligne
individuel, où l'authentification n'a pas de sens.
"""
import hashlib

import streamlit as st


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_configured_users() -> dict:
    try:
        return dict(st.secrets.get("auth_users", {}))
    except Exception:
        return {}


def auth_configured() -> bool:
    return bool(_get_configured_users())


def require_login(title: str, username_label: str, password_label: str,
                   submit_label: str, error_label: str) -> bool:
    """Affiche un formulaire de connexion si des comptes sont configurés et que
    l'utilisateur n'est pas encore authentifié. Retourne True si l'accès est
    autorisé (soit déjà connecté, soit pas d'authentification configurée)."""
    if st.session_state.get("authenticated"):
        return True

    users = _get_configured_users()
    if not users:
        return True  # pas d'authentification configurée : usage local, accès ouvert

    st.title(title)
    with st.form("login_form"):
        username = st.text_input(username_label)
        password = st.text_input(password_label, type="password")
        submitted = st.form_submit_button(submit_label)

    if submitted:
        expected_hash = users.get(username)
        if expected_hash and _hash_password(password) == expected_hash:
            st.session_state.authenticated = True
            st.session_state.current_user = username
            st.rerun()
        else:
            st.error(error_label)

    return False


def logout():
    st.session_state.authenticated = False
    st.session_state.pop("current_user", None)
