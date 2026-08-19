"""Authentification par nom d'utilisateur / mot de passe, avec deux modes :

- Mode hiérarchique (Supabase configuré) : les comptes sont gérés dans la
  table `users` (National/Régional/Départemental, admin, conseiller...) via
  utils.hierarchy — voir ce module pour la logique de rôles et de visibilité.
- Mode simple (pas de Supabase, usage local individuel) : ancien système par
  liste plate dans les secrets Streamlit [auth_users], sans hiérarchie —
  suffisant pour un usage hors-ligne individuel où la hiérarchie n'a pas de
  sens (un seul utilisateur).
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
    from utils.hierarchy import hierarchical_accounts_available
    if hierarchical_accounts_available():
        return True
    return bool(_get_configured_users())


def require_login(title: str, username_label: str, password_label: str,
                   submit_label: str, error_label: str) -> bool:
    """Affiche un formulaire de connexion si des comptes sont configurés et que
    l'utilisateur n'est pas encore authentifié. Retourne True si l'accès est
    autorisé (soit déjà connecté, soit pas d'authentification configurée)."""
    if st.session_state.get("authenticated"):
        return True

    from utils.hierarchy import hierarchical_accounts_available, authenticate

    if hierarchical_accounts_available():
        st.title(title)
        with st.form("login_form"):
            username = st.text_input(username_label)
            password = st.text_input(password_label, type="password")
            submitted = st.form_submit_button(submit_label)

        if submitted:
            connection_failed = False
            try:
                account = authenticate(username, password)
            except Exception:
                connection_failed = True
                account = {}
            if account:
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.session_state.current_account = account
                from utils.activity_log import log_action
                log_action(username, "connexion", "")
                st.rerun()
            elif connection_failed:
                st.error("⚠️ Connexion à la base de comptes impossible pour le moment. "
                         "Réessaie dans un instant. / Unable to reach the accounts database "
                         "right now. Please try again shortly.")
            else:
                st.error(error_label)
        return False

    # --- Mode simple (pas de Supabase) : ancien système ---
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
            st.session_state.current_account = {"username": username, "niveau": None,
                                                  "is_admin": False, "is_conseiller": True}
            st.rerun()
        else:
            st.error(error_label)

    return False


def logout():
    st.session_state.authenticated = False
    st.session_state.pop("current_user", None)
    st.session_state.pop("current_account", None)
