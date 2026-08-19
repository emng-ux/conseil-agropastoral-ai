"""Panneau d'administration, réservé aux comptes is_admin=True : création et
gestion des comptes hiérarchiques, suivi (estimé) des coûts d'usage de l'API
IA, et consultation du journal d'activité.
"""
import streamlit as st

from utils.hierarchy import (create_account, set_password, set_active,
                              list_all_accounts, NIVEAUX)
from utils.activity_log import list_recent_actions

# Estimation grossière du coût par échange conversationnel (ordre de grandeur
# donné lors de la mise en place du chat IA — à ajuster si le tarif du modèle
# change). Affiché comme ESTIMATION, pas comme facturation exacte : seule la
# console Anthropic fait foi pour le coût réel.
_COUT_ESTIME_PAR_MESSAGE_USD = 0.01


def render_admin_panel(lang: str, current_user: str):
    st.title("⚙️ " + ("Administration" if lang == "fr" else "Administration"))

    tabs = st.tabs([
        "👥 " + ("Comptes" if lang == "fr" else "Accounts"),
        "💰 " + ("Coûts API" if lang == "fr" else "API costs"),
        "📋 " + ("Journal d'activité" if lang == "fr" else "Activity log"),
    ])

    accounts = list_all_accounts()

    # -------------------------------------------------------------------
    # Onglet 1 : Comptes
    # -------------------------------------------------------------------
    with tabs[0]:
        st.subheader("➕ " + ("Créer un compte" if lang == "fr" else "Create an account"))
        with st.form("create_account_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nom_complet = c1.text_input("Nom complet" if lang == "fr" else "Full name")
            username = c2.text_input("Identifiant" if lang == "fr" else "Username")
            c3, c4 = st.columns(2)
            password = c3.text_input("Mot de passe" if lang == "fr" else "Password", type="password")
            fonction = c4.text_input("Fonction" if lang == "fr" else "Function")

            niveau = st.selectbox("Niveau" if lang == "fr" else "Level", NIVEAUX)
            c5, c6 = st.columns(2)
            region = c5.text_input("Région (si régional ou départemental)" if lang == "fr"
                                    else "Region (if regional or departmental)")
            departement = c6.text_input("Département (si départemental)" if lang == "fr"
                                         else "Department (if departmental)")

            c7, c8 = st.columns(2)
            is_admin = c7.checkbox("Compte administrateur" if lang == "fr" else "Administrator account")
            is_conseiller = c8.checkbox("Compte conseiller (crée des diagnostics)" if lang == "fr"
                                         else "Advisor account (creates diagnostics)")

            submitted = st.form_submit_button("Créer" if lang == "fr" else "Create")
            if submitted:
                if not username or not password or not nom_complet:
                    st.error("Nom complet, identifiant et mot de passe sont obligatoires."
                              if lang == "fr" else "Full name, username and password are required.")
                else:
                    try:
                        create_account(username, password, nom_complet, fonction, niveau,
                                        region, departement, is_admin, is_conseiller)
                        from utils.activity_log import log_action
                        log_action(current_user, "creation_compte", f"Compte créé : {username}")
                        st.success(("Compte créé : " if lang == "fr" else "Account created: ") + username)
                        st.rerun()
                    except Exception as e:
                        st.error(f"{'Erreur' if lang == 'fr' else 'Error'} : {e}")

        st.markdown("---")
        st.subheader("📋 " + ("Comptes existants" if lang == "fr" else "Existing accounts"))
        for a in accounts:
            statut = "🟢" if a.get("actif", True) else "🔴"
            badge_admin = " 👑" if a.get("is_admin") else ""
            perimetre = a.get("niveau", "")
            if a.get("region"):
                perimetre += f" — {a['region']}"
            if a.get("departement"):
                perimetre += f" / {a['departement']}"
            with st.container(border=True):
                st.markdown(f"**{statut} {a.get('nom_complet', a['username'])}**{badge_admin} "
                            f"(`{a['username']}`) — {a.get('fonction', '')}")
                st.caption(perimetre)
                bc1, bc2, bc3 = st.columns(3)
                if bc1.button(("Désactiver" if a.get("actif", True) else "Réactiver") if lang == "fr"
                              else ("Deactivate" if a.get("actif", True) else "Reactivate"),
                              key=f"toggle_{a['username']}"):
                    set_active(a["username"], not a.get("actif", True))
                    st.rerun()
                with bc2.popover("🔑 " + ("Réinitialiser" if lang == "fr" else "Reset password")):
                    new_pw = st.text_input("Nouveau mot de passe" if lang == "fr" else "New password",
                                            type="password", key=f"newpw_{a['username']}")
                    if st.button("OK", key=f"resetbtn_{a['username']}") and new_pw:
                        set_password(a["username"], new_pw)
                        st.success("✅")

    # -------------------------------------------------------------------
    # Onglet 2 : Coûts API (estimation)
    # -------------------------------------------------------------------
    with tabs[1]:
        st.caption("⚠️ " + ("Estimation indicative basée sur le nombre d'échanges enregistrés — "
                            "seule la console Anthropic fait foi pour la facturation réelle."
                            if lang == "fr" else
                            "Indicative estimate based on the number of recorded exchanges — "
                            "only the Anthropic console reflects actual billing."))
        actions = list_recent_actions(limit=1000)
        chat_actions = [a for a in actions if a.get("action") == "message_ia"]
        from collections import Counter
        counts = Counter(a["username"] for a in chat_actions)
        if counts:
            for user, n in counts.most_common():
                cost = n * _COUT_ESTIME_PAR_MESSAGE_USD
                st.markdown(f"- **{user}** : {n} échanges — ≈ {cost:.2f} $")
            total = len(chat_actions) * _COUT_ESTIME_PAR_MESSAGE_USD
            st.metric("Total estimé" if lang == "fr" else "Estimated total", f"≈ {total:.2f} $")
        else:
            st.info("Aucun échange IA enregistré pour l'instant." if lang == "fr"
                    else "No AI exchange recorded yet.")

    # -------------------------------------------------------------------
    # Onglet 3 : Journal d'activité
    # -------------------------------------------------------------------
    with tabs[2]:
        actions = list_recent_actions(limit=200)
        if not actions:
            st.info("Aucune activité enregistrée pour l'instant." if lang == "fr"
                    else "No activity recorded yet.")
        for a in actions:
            st.caption(f"`{a.get('created_at', '')[:19]}` — **{a.get('username', '')}** — "
                       f"{a.get('action', '')} — {a.get('details', '')}")
