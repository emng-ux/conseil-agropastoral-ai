"""Agent IA de conseil agropastoral — application principale Streamlit.

Fonctionnement hybride : le socle (formulaire, stockage, analyse, export) tourne
100% en local sans connexion Internet. Le chat IA conversationnel s'active
uniquement si une connexion est détectée.
"""
import streamlit as st
import plotly.graph_objects as go

from utils.i18n import t
from utils.storage import (new_diagnostic_id, save_diagnostic, load_diagnostic,
                            delete_diagnostic, list_diagnostics, ensure_code)
from utils.connectivity import is_online
from modules.collecte import (branch_keys, branch_label, render_branch_form,
                               branch_completion_ratio)
from modules.import_data import build_template_dataframe, dataframe_to_excel_bytes, \
    import_file_to_diagnostic
from modules.analyse_pestel import compute_pestel, PESTEL_LABELS
from modules.analyse_porter import compute_porter
from modules.analyse_bcg import compute_bcg
from modules.analyse_ansoff import compute_ansoff
from modules.analyse_swot import compute_swot, label as swot_label
from modules.plan_strategique import generate_draft_plan, validate_plan, is_validated
from modules.export import export_pdf_bytes, export_word_bytes, ExportNotAllowedError

st.set_page_config(page_title="Conseil Agropastoral IA", page_icon="🌿", layout="wide")

# Limite d'échanges IA par diagnostic — garde-fou budgétaire (coût maîtrisé par
# diagnostic). L'administrateur peut réinitialiser ce compteur au cas par cas
# si un diagnostic complexe le justifie réellement.
CHAT_EXCHANGE_LIMIT = 12

# --- PWA : rend l'app installable sur l'écran d'accueil (Android notamment).
# Nécessite [server] enableStaticServing = true dans .streamlit/config.toml,
# et les fichiers static/manifest.json, static/icon-*.png, static/sw.js. ---
st.markdown("""
    <link rel="manifest" href="./app/static/manifest.json">
    <meta name="theme-color" content="#2e7d32">
    <link rel="apple-touch-icon" href="./app/static/icon-192.png">
    <script>
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./app/static/sw.js').catch(function() {});
    }
    </script>
""", unsafe_allow_html=True)

# --- Identité visuelle : palette "forêt → récolte" (vert profond vers doré),
# choisie pour évoquer la croissance des cultures et la récolte plutôt qu'un
# dégradé générique. Injection CSS ciblée sur les composants Streamlit
# principaux (sidebar, boutons, cartes, onglets) — dégradation silencieuse
# si une future version de Streamlit renomme ses data-testid internes. ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

:root {
    --forest-deep: #1b5e20;
    --forest-mid: #2e7d32;
    --forest-light: #66bb6a;
    --gold-harvest: #f9a825;
    --gold-light: #ffca28;
    --earth-brown: #6d4c41;
    --bg-warm: #fbfaf6;
    --bg-panel: #f2f7ee;
    --gradient-main: linear-gradient(90deg, var(--forest-deep) 0%, var(--forest-mid) 50%, var(--gold-harvest) 100%);
}

html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
h1, h2, h3, h4 { font-family: 'Sora', 'Inter', sans-serif !important; letter-spacing: -0.01em; }
h1 { color: var(--forest-deep) !important; font-weight: 800 !important; }

.stApp { background-color: var(--bg-warm); }

/* Barre latérale : léger dégradé vertical + liseré doré en tête */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg-panel) 0%, var(--bg-warm) 55%);
    border-right: 3px solid transparent;
    border-image: var(--gradient-main) 1;
}
section[data-testid="stSidebar"] h2 {
    background: var(--gradient-main);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
}

/* Boutons primaires : dégradé forêt -> or, avec effet de survol */
.stButton > button[kind="primary"] {
    background: var(--gradient-main);
    background-size: 160% 160%;
    border: none;
    color: white;
    font-weight: 600;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(27, 94, 32, 0.25);
    transition: all 0.25s ease;
}
.stButton > button[kind="primary"]:hover {
    background-position: 100% 0;
    box-shadow: 0 5px 16px rgba(27, 94, 32, 0.35);
    transform: translateY(-1px);
}
.stButton > button:not([kind="primary"]) {
    border-radius: 10px;
    border: 1.5px solid var(--forest-light);
    color: var(--forest-deep);
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton > button:not([kind="primary"]):hover {
    background: var(--bg-panel);
    border-color: var(--forest-mid);
}

/* Cartes (containers avec bordure) : angles arrondis, ombre douce, liseré doré au survol */
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(27, 94, 32, 0.08);
    transition: box-shadow 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover > div {
    box-shadow: 0 4px 14px rgba(249, 168, 37, 0.18);
}

/* Métriques : valeur en dégradé pour les indicateurs clés */
div[data-testid="stMetricValue"] {
    background: var(--gradient-main);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}

/* Onglets : soulignement doré sur l'onglet actif */
.stTabs [aria-selected="true"] {
    color: var(--forest-deep) !important;
    border-bottom: 3px solid var(--gold-harvest) !important;
    font-weight: 600;
}

/* Expanders : coins arrondis et fond légèrement teinté */
div[data-testid="stExpander"] {
    border-radius: 12px;
    border: 1px solid var(--bg-panel);
    overflow: hidden;
}

/* Barres de progression (radar/plotly restent inchangées, mais st.progress si utilisé) */
.stProgress > div > div { background: var(--gradient-main) !important; }
</style>
""", unsafe_allow_html=True)

# Sécurise la lecture des secrets (clés API) : sur certaines configurations de
# Streamlit Cloud, les secrets ne sont accessibles que via st.secrets et pas
# automatiquement copiés dans os.environ. On les recopie explicitement ici pour
# que agent/orchestrator.py (qui lit os.environ) fonctionne de façon fiable,
# en local comme en ligne.
import os
for _secret_key in ("ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_KEY",
                    "KOBO_API_TOKEN", "KOBO_SERVER_URL", "KOBO_ASSET_UID"):
    if _secret_key not in os.environ:
        try:
            if _secret_key in st.secrets:
                os.environ[_secret_key] = st.secrets[_secret_key]
        except Exception:
            pass  # pas de fichier secrets.toml en local : comportement normal, on ignore

# ---------------------------------------------------------------------------
# Authentification (si des comptes sont configurés dans les secrets)
# ---------------------------------------------------------------------------
from utils.auth import require_login, logout

_login_lang = "fr"  # la langue n'est pas encore choisie à ce stade : écran de connexion toujours en français+anglais
if not require_login(
        title="🔒 Connexion — Login",
        username_label="Nom d'utilisateur / Username",
        password_label="Mot de passe / Password",
        submit_label="Se connecter / Log in",
        error_label="Identifiants incorrects / Incorrect credentials"):
    st.stop()

# ---------------------------------------------------------------------------
# État de session
# ---------------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "fr"
if "current_diagnostic_id" not in st.session_state:
    st.session_state.current_diagnostic_id = None
if "current_diagnostic" not in st.session_state:
    st.session_state.current_diagnostic = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "online" not in st.session_state:
    st.session_state.online = is_online()

lang = st.session_state.lang


def _(key):
    return t(key, lang)


def display_label(diagnostic: dict) -> str:
    """Protection des données : affiche le code d'identifiant par défaut, le nom
    réel de l'EFA/OP seulement si le conseiller a explicitement activé le mode
    'Afficher les noms' dans la barre latérale."""
    code = diagnostic.get("code", "—")
    if st.session_state.get("reveal_names"):
        return f"{code} — {diagnostic.get('nom', '')}"
    return code


# ---------------------------------------------------------------------------
# Barre latérale
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## 🌿 {_('app_title')}")
    st.caption(_("app_subtitle"))

    new_lang = st.selectbox(_("select_language"), ["fr", "en"],
                             index=0 if lang == "fr" else 1,
                             format_func=lambda x: "Français" if x == "fr" else "English")
    if new_lang != lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")
    st.markdown(_("online_status_online") if st.session_state.online else _("online_status_offline"))
    from utils.storage import storage_backend_name
    st.caption(f"💾 {storage_backend_name()}")

    if st.session_state.get("current_user"):
        current_account = st.session_state.get("current_account", {})
        photo_b64 = current_account.get("photo_base64")
        if photo_b64:
            import base64 as _b64
            st.image(_b64.b64decode(photo_b64), width=64)
        st.caption(f"👤 {current_account.get('nom_complet') or st.session_state['current_user']}")
        if current_account.get("fonction"):
            st.caption(f"🏷️ {current_account['fonction']}")
        perimetre_bits = [b for b in [current_account.get("niveau"), current_account.get("region"),
                                       current_account.get("departement")] if b]
        if perimetre_bits:
            st.caption("📍 " + " — ".join(perimetre_bits))

        with st.expander(_("profile_photo_title")):
            photo_file = st.file_uploader(_("profile_photo_upload"), type=["png", "jpg", "jpeg"],
                                           key="profile_photo_uploader")
            if photo_file is not None and st.button(_("profile_photo_save"), key="profile_photo_save_btn"):
                import base64 as _b64
                from utils.hierarchy import set_photo, hierarchical_accounts_available
                if hierarchical_accounts_available():
                    encoded = _b64.b64encode(photo_file.getvalue()).decode("utf-8")
                    set_photo(st.session_state["current_user"], encoded)
                    st.session_state["current_account"]["photo_base64"] = encoded
                    st.success("✅")
                    st.rerun()
                else:
                    st.info(_("profile_photo_needs_hierarchy"))

        if st.button(_("logout_button"), use_container_width=True):
            logout()
            st.rerun()

    from utils.auth import auth_configured
    if not auth_configured():
        with st.expander("🔐 " + _("setup_auth_title")):
            st.caption(_("setup_auth_intro"))
            su_user = st.text_input(_("setup_auth_username"), key="setup_auth_user")
            su_pass = st.text_input(_("setup_auth_password"), type="password", key="setup_auth_pass")
            if st.button(_("setup_auth_generate"), key="setup_auth_btn"):
                if su_user and su_pass:
                    import hashlib
                    _hash = hashlib.sha256(su_pass.encode("utf-8")).hexdigest()
                    st.code(f'[auth_users]\n{su_user} = "{_hash}"', language="toml")
                    st.caption(_("setup_auth_instructions"))
                else:
                    st.warning(_("setup_auth_missing"))

    st.markdown("---")
    st.session_state.reveal_names = st.toggle(
        _("reveal_names_toggle"), value=st.session_state.get("reveal_names", False))
    if st.session_state.reveal_names:
        st.caption(_("reveal_names_warning"))

    st.markdown("---")
    page_labels = {
        "dashboard": _("nav_dashboard"),
        "collecte": _("nav_collecte"),
        "analyse": _("nav_analyse"),
        "plan": _("nav_plan"),
        "historique": _("nav_historique"),
    }
    _current_account_nav = st.session_state.get("current_account", {})
    from utils.hierarchy import hierarchical_accounts_available
    if hierarchical_accounts_available() and st.session_state.get("current_user"):
        page_labels["messagerie"] = _("nav_messagerie")
        if _current_account_nav.get("is_admin"):
            page_labels["administration"] = _("nav_administration")

    for key, label in page_labels.items():
        if st.button(label, use_container_width=True,
                     type="primary" if st.session_state.page == key else "secondary"):
            st.session_state.page = key
            st.rerun()


def _ensure_diagnostic():
    if st.session_state.current_diagnostic is None:
        st.warning(_("no_diagnostics"))
        st.stop()


# ---------------------------------------------------------------------------
# Page : Tableau de bord
# ---------------------------------------------------------------------------
def _get_visible_owners():
    """Calcule l'ensemble des identifiants de diagnostics visibles par
    l'utilisateur connecté, selon son périmètre hiérarchique. Retourne None
    si la hiérarchie n'est pas active (mode simple/local) ou si la base de
    comptes est temporairement injoignable : dans ce cas, aucun filtrage
    n'est appliqué plutôt que de faire planter le tableau de bord."""
    from utils.hierarchy import hierarchical_accounts_available, list_all_accounts, visible_usernames
    if not hierarchical_accounts_available() or not st.session_state.get("current_account"):
        return None
    try:
        all_accounts = list_all_accounts()
        return visible_usernames(st.session_state["current_account"], all_accounts)
    except Exception:
        return None


def page_dashboard():
    st.title(_("nav_dashboard"))

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(_("existing_diagnostics"))
        diagnostics = list_diagnostics(visible_owners=_get_visible_owners())
        if not diagnostics:
            st.info(_("no_diagnostics"))
        for d in diagnostics:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                status = "✅" if d["validated"] else "🕓"
                name_display = (f"{d['code']} — {d['nom']}"
                                 if st.session_state.get("reveal_names") else d["code"])
                c1.markdown(f"**{status} {name_display}** — {d['type']}  \n_{d['conseiller']}_")
                if c2.button(_("open"), key=f"open_{d['id']}"):
                    st.session_state.current_diagnostic_id = d["id"]
                    st.session_state.current_diagnostic = load_diagnostic(d["id"])
                    st.session_state.page = "collecte"
                    st.rerun()
                if c3.button(_("delete"), key=f"del_{d['id']}"):
                    delete_diagnostic(d["id"])
                    st.rerun()

    with col2:
        st.subheader(_("new_diagnostic"))
        with st.form("new_diagnostic_form"):
            nom = st.text_input(_("diagnostic_name"))
            type_structure = st.selectbox(_("diagnostic_type"), [_("type_efa"), _("type_op")])
            conseiller = st.text_input(_("conseiller_name"))
            submitted = st.form_submit_button(_("create"))
            if submitted and nom:
                diagnostic_id = new_diagnostic_id()
                diagnostic = {"nom": nom, "type": type_structure, "conseiller": conseiller, "etoile": {},
                              "owner_username": st.session_state.get("current_user", "")}
                save_diagnostic(diagnostic_id, diagnostic)
                from utils.activity_log import log_action
                log_action(st.session_state.get("current_user", ""), "creation_diagnostic",
                           f"Diagnostic créé : {nom}")
                st.session_state.current_diagnostic_id = diagnostic_id
                st.session_state.current_diagnostic = diagnostic
                st.session_state.page = "collecte"
                st.rerun()

        st.markdown("---")
        st.subheader(_("import_title"))
        st.caption(_("import_help"))
        template_bytes = dataframe_to_excel_bytes(build_template_dataframe(lang))
        st.download_button(_("download_template"), data=template_bytes,
                            file_name="modele_diagnostic.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        uploaded = st.file_uploader(_("upload_file"), type=["xlsx", "csv"])
        if uploaded is not None:
            try:
                diagnostic = import_file_to_diagnostic(uploaded)
                diagnostic_id = new_diagnostic_id()
                save_diagnostic(diagnostic_id, diagnostic)
                st.success(_("import_success"))
                st.session_state.current_diagnostic_id = diagnostic_id
                st.session_state.current_diagnostic = diagnostic
                st.session_state.page = "collecte"
                st.rerun()
            except Exception:
                st.error(_("import_error"))

        st.markdown("---")
        st.subheader(_("import_word_title"))
        if st.session_state.online:
            from modules.import_word import (word_import_available, extract_text_from_docx,
                                               extract_diagnostic_from_text,
                                               build_diagnostic_from_extraction)
            if word_import_available():
                st.caption(_("import_word_help"))
                nom_word = st.text_input(_("diagnostic_name"), key="word_nom")
                type_word = st.selectbox(_("diagnostic_type"), [_("type_efa"), _("type_op")], key="word_type")
                conseiller_word = st.text_input(_("conseiller_name"), key="word_conseiller")
                word_files = st.file_uploader(_("import_word_upload"), type=["docx"],
                                               accept_multiple_files=True, key="word_files")
                if word_files and nom_word and st.button(_("import_word_button")):
                    with st.spinner(_("import_word_progress")):
                        try:
                            full_text = "\n\n".join(extract_text_from_docx(f) for f in word_files)
                            extraction = extract_diagnostic_from_text(full_text, lang)
                            diagnostic = build_diagnostic_from_extraction(
                                extraction, nom_word, type_word, conseiller_word)
                            diagnostic_id = new_diagnostic_id()
                            st.session_state.current_diagnostic_id = diagnostic_id
                            st.session_state.current_diagnostic = diagnostic
                            st.session_state.page = "collecte"
                            st.success(_("import_word_review_hint"))
                            st.rerun()
                        except Exception as e:
                            st.error(f"{_('import_error')} ({e})")
            else:
                st.info(_("import_word_needs_key"))
        else:
            st.info(_("chat_unavailable_offline"))

        st.markdown("---")
        st.subheader(_("import_kobo_title"))
        from modules.kobo_import import kobo_available, list_kobo_submissions, \
            build_diagnostic_from_kobo_submission, submission_label
        st.caption(_("import_kobo_help"))
        with st.expander(_("import_kobo_template_title")):
            st.caption(_("import_kobo_template_help"))
            from modules.kobo_form_generator import generate_kobo_xlsform_bytes
            st.download_button(_("import_kobo_template_download"),
                                data=generate_kobo_xlsform_bytes(),
                                file_name="formulaire_kobo_conseil_agropastoral.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if kobo_available():
            nom_kobo = st.text_input(_("diagnostic_name"), key="kobo_nom")
            type_kobo = st.selectbox(_("diagnostic_type"), [_("type_efa"), _("type_op")], key="kobo_type")
            conseiller_kobo = st.text_input(_("conseiller_name"), key="kobo_conseiller")

            if st.button(_("import_kobo_refresh"), key="kobo_refresh_btn"):
                st.session_state["kobo_submissions"] = None
            if st.session_state.get("kobo_submissions") is None:
                try:
                    st.session_state["kobo_submissions"] = list_kobo_submissions()
                except Exception as e:
                    st.error(f"{_('import_error')} ({e})")
                    st.session_state["kobo_submissions"] = []

            submissions = st.session_state.get("kobo_submissions") or []
            if submissions:
                labels = {submission_label(s): s for s in submissions}
                chosen_label = st.selectbox(_("import_kobo_select"), list(labels.keys()), key="kobo_select")
                if nom_kobo and st.button(_("import_kobo_button"), key="kobo_import_btn"):
                    submission = labels[chosen_label]
                    diagnostic = build_diagnostic_from_kobo_submission(
                        submission, nom_kobo, type_kobo, conseiller_kobo, lang)
                    diagnostic_id = new_diagnostic_id()
                    st.session_state.current_diagnostic_id = diagnostic_id
                    st.session_state.current_diagnostic = diagnostic
                    st.session_state.page = "collecte"
                    st.success(_("import_word_review_hint"))
                    st.rerun()
            else:
                st.info(_("import_kobo_no_submissions"))
        else:
            st.info(_("import_kobo_needs_config"))


# ---------------------------------------------------------------------------
# Page : Collecte (étoile du conseil)
# ---------------------------------------------------------------------------
def _radar_chart(diagnostic):
    keys = branch_keys()
    labels = [branch_label(k, lang) for k in keys]
    values = [branch_completion_ratio(k, diagnostic) for k in keys]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]],
                                   fill="toself", name=_("star_progress"),
                                   line_color="#2e7d32"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                       showlegend=False, height=380, margin=dict(l=40, r=40, t=20, b=20))
    return fig


def page_collecte():
    _ensure_diagnostic()
    diagnostic = st.session_state.current_diagnostic
    ensure_code(st.session_state.current_diagnostic_id, diagnostic)
    st.title(f"{_('nav_collecte')} — {display_label(diagnostic)}")

    from modules.identification import render_identification_form
    with st.expander(_("identification_title"), expanded=not diagnostic.get("identification")):
        render_identification_form(diagnostic, lang)

    from modules.entreprise import (render_histoire, render_environnement, render_parcelles,
                                     render_siege_batiments_paysage, render_calendrier, render_activites,
                                     render_diagnostic_financier)
    from modules.bilan import render_bilan
    with st.expander(_("entreprise_title"), expanded=False):
        ent_tabs = st.tabs([_("tab_histoire"), _("tab_environnement"), _("tab_parcelles"),
                            _("tab_calendrier"), _("tab_activites"), _("tab_diagnostic_financier"),
                            _("tab_bilan"), _("tab_plan_financement")])
        with ent_tabs[0]:
            render_histoire(diagnostic, lang)
        with ent_tabs[1]:
            render_environnement(diagnostic, lang)
        with ent_tabs[2]:
            render_parcelles(diagnostic, lang)
            st.markdown("---")
            render_siege_batiments_paysage(diagnostic, lang)
            st.markdown("---")

            from modules.schema_visuel import (generate_site_plan_svg, generate_general_plan_svg,
                                                list_sites, has_enough_data)
            st.markdown(f"### {_('schema_title')}")
            st.caption(_("schema_help"))

            if not has_enough_data(diagnostic):
                st.info(_("schema_no_data"))
            else:
                sites = list_sites(diagnostic)
                if st.button(_("schema_generate_button"), key="schema_generate_btn"):
                    st.session_state["schema_generated"] = True

                if st.session_state.get("schema_generated"):
                    if sites:
                        st.caption(_("schema_multi_site_help"))
                        svg_general = generate_general_plan_svg(diagnostic, lang)
                        st.markdown(f"#### {_('schema_general_plan')}")
                        st.markdown(f'<div style="overflow-x:auto">{svg_general}</div>', unsafe_allow_html=True)
                        st.download_button(
                            _("schema_download_general"), data=svg_general,
                            file_name=f"plan_general_{diagnostic.get('code', 'diagnostic')}.svg",
                            mime="image/svg+xml", key="dl_general")

                        selected_site = st.selectbox(_("schema_select_site"), sites, key="schema_site_select")
                        svg_site = generate_site_plan_svg(diagnostic, lang, site=selected_site,
                                                           include_flux=False)
                        st.markdown(f"#### {_('schema_site_plan_title')} : {selected_site}")
                        st.markdown(f'<div style="overflow-x:auto">{svg_site}</div>', unsafe_allow_html=True)
                        st.download_button(
                            _("schema_download"), data=svg_site,
                            file_name=f"plan_{selected_site}_{diagnostic.get('code', 'diagnostic')}.svg",
                            mime="image/svg+xml", key="dl_site")
                    else:
                        svg_content = generate_site_plan_svg(diagnostic, lang, site=None, include_flux=True)
                        st.markdown(f'<div style="overflow-x:auto">{svg_content}</div>', unsafe_allow_html=True)
                        st.download_button(
                            _("schema_download"), data=svg_content,
                            file_name=f"schema_{diagnostic.get('code', 'diagnostic')}.svg",
                            mime="image/svg+xml", key="dl_mono")
        with ent_tabs[3]:
            render_calendrier(diagnostic, lang)
        with ent_tabs[4]:
            render_activites(diagnostic, lang)
        with ent_tabs[5]:
            render_diagnostic_financier(diagnostic, lang)
        with ent_tabs[6]:
            render_bilan(diagnostic, lang)
        with ent_tabs[7]:
            from modules.plan_financement import render_plan_financement, render_resultats_plan_financement
            st.caption(_("plan_financement_help"))
            render_plan_financement(diagnostic, lang)
            st.markdown("---")
            if st.button(_("plan_financement_generate_button"), key="pf_generate_btn"):
                st.session_state["plan_financement_generated"] = True
            if st.session_state.get("plan_financement_generated"):
                render_resultats_plan_financement(diagnostic, lang)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.plotly_chart(_radar_chart(diagnostic), use_container_width=True)

        if st.session_state.online:
            from agent.orchestrator import agent_available, run_turn
            if agent_available():
                st.markdown(f"**{_('nav_collecte')} — 🤖**")

                chat_key = f"chat_history_{st.session_state.current_diagnostic_id}"
                if chat_key not in st.session_state:
                    st.session_state[chat_key] = []

                # Affiche l'historique de la conversation (messages texte uniquement,
                # les blocs tool_use/tool_result internes ne sont pas montrés au conseiller)
                for msg in st.session_state[chat_key]:
                    if msg["role"] == "user" and isinstance(msg["content"], str):
                        with st.chat_message("user"):
                            st.markdown(msg["content"])
                    elif msg["role"] == "assistant":
                        content = msg["content"]
                        text_parts = []
                        if isinstance(content, list):
                            for b in content:
                                if isinstance(b, dict) and b.get("type") == "text":
                                    text_parts.append(b.get("text", ""))
                                elif getattr(b, "type", "") == "text":
                                    text_parts.append(getattr(b, "text", ""))
                        if text_parts:
                            with st.chat_message("assistant"):
                                st.markdown("\n".join(text_parts))

                exchange_count = diagnostic.get("ia_exchange_count", 0)
                st.caption(_("chat_exchange_counter").format(count=exchange_count, limit=CHAT_EXCHANGE_LIMIT))

                if exchange_count >= CHAT_EXCHANGE_LIMIT:
                    st.warning(_("chat_limit_reached"))
                    if st.session_state.get("current_account", {}).get("is_admin"):
                        if st.button(_("chat_limit_reset_admin"), key="chat_limit_reset_btn"):
                            diagnostic["ia_exchange_count"] = 0
                            save_diagnostic(st.session_state.current_diagnostic_id, diagnostic)
                            st.rerun()
                else:
                    message = st.chat_input(_("chat_placeholder"))
                    if message:
                        try:
                            result = run_turn(st.session_state[chat_key], message, diagnostic, lang)
                            st.session_state[chat_key] = result["conversation_history"]
                            diagnostic["ia_exchange_count"] = exchange_count + 1
                            st.session_state.current_diagnostic = diagnostic
                            save_diagnostic(st.session_state.current_diagnostic_id, diagnostic)
                            from utils.activity_log import log_action
                            log_action(st.session_state.get("current_user", ""), "message_ia",
                                       f"Diagnostic {st.session_state.current_diagnostic_id}")
                            if result["ready_for_analysis"]:
                                st.session_state.chat_ready_for_analysis = True
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                if st.session_state.get("chat_ready_for_analysis"):
                    st.success("✅ " + ("Diagnostic prêt : va dans l'onglet Analyse stratégique."
                                         if lang == "fr" else
                                         "Diagnostic ready: go to the Strategic analysis tab."))
        else:
            st.info(_("chat_unavailable_offline"))

    with col2:
        tabs = st.tabs([branch_label(k, lang) for k in branch_keys()])
        for tab, key in zip(tabs, branch_keys()):
            with tab:
                render_branch_form(key, diagnostic, lang)
                if key == "moyens_production":
                    st.markdown("---")
                    from modules.amortissements import render_tableau_amortissements
                    render_tableau_amortissements(diagnostic, lang)

        if st.button(_("save"), type="primary"):
            save_diagnostic(st.session_state.current_diagnostic_id, diagnostic)
            st.success(_("saved"))

        st.markdown("---")
        from modules.export import export_diagnostic_pdf_bytes, export_diagnostic_word_bytes
        include_name_collecte = st.checkbox(_("include_real_name_export"), value=False,
                                             key="include_name_diag_export")
        if include_name_collecte:
            st.caption(_("include_real_name_warning"))
        dl_col1, dl_col2 = st.columns(2)
        dl_col1.download_button(
            _("download_diagnostic_pdf"),
            data=export_diagnostic_pdf_bytes(diagnostic, lang, include_real_name=include_name_collecte),
            file_name=f"diagnostic_{diagnostic.get('code', 'export')}.pdf",
            mime="application/pdf")
        dl_col2.download_button(
            _("download_diagnostic_word"),
            data=export_diagnostic_word_bytes(diagnostic, lang, include_real_name=include_name_collecte),
            file_name=f"diagnostic_{diagnostic.get('code', 'export')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ---------------------------------------------------------------------------
# Page : Analyse stratégique
# ---------------------------------------------------------------------------
def page_analyse():
    _ensure_diagnostic()
    diagnostic = st.session_state.current_diagnostic
    st.title(f"{_('nav_analyse')} — {display_label(diagnostic)}")

    if st.button(_("run_analysis"), type="primary"):
        st.session_state.pestel = compute_pestel(diagnostic, lang)
        st.session_state.porter = compute_porter(diagnostic, lang)
        st.session_state.bcg = compute_bcg(diagnostic, lang)
        st.session_state.ansoff = compute_ansoff(diagnostic, lang)
        # Le SWOT recoupe PESTEL et Porter déjà calculés, pour rester cohérent entre les 5 outils.
        st.session_state.swot = compute_swot(diagnostic, lang, pestel=st.session_state.pestel,
                                              porter=st.session_state.porter)

    if "pestel" not in st.session_state:
        st.info(_("analysis_incomplete"))
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [_("tab_pestel"), _("tab_porter"), _("tab_bcg"), _("tab_ansoff"), _("tab_swot")])

    with tab1:
        cols = st.columns(3)
        for i, (key, items) in enumerate(st.session_state.pestel.items()):
            with cols[i % 3]:
                st.markdown(f"**{PESTEL_LABELS[key].get(lang, PESTEL_LABELS[key]['fr'])}**")
                if items:
                    for it in items:
                        st.markdown(f"- {it}")
                else:
                    st.caption("—")

    with tab2:
        for force in st.session_state.porter.values():
            emoji = {"faible": "🟢", "moyen": "🟠", "fort": "🔴"}[force["niveau"]]
            st.markdown(f"{emoji} **{force['label'].get(lang, force['label']['fr'])}** — {force['niveau_label']}")

    with tab3:
        bcg = st.session_state.bcg
        if not bcg:
            st.caption("—")
        else:
            fig = go.Figure()
            for act in bcg:
                fig.add_trace(go.Scatter(
                    x=[act["taux_croissance"]], y=[act["part_marche_relative"]],
                    mode="markers+text", text=[act["nom"]], textposition="top center",
                    marker=dict(size=18), name=act["nom"]))
            fig.update_layout(xaxis_title="Taux de croissance (%)" if lang == "fr" else "Growth rate (%)",
                               yaxis_title="Part de marché relative" if lang == "fr" else "Relative market share",
                               height=420, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            for act in bcg:
                st.markdown(f"- **{act['nom']}** : {act['quadrant_label']}")

    with tab4:
        for key, opt in st.session_state.ansoff["options"].items():
            marker = "⭐ " if opt["recommande"] else ""
            st.markdown(f"{marker}**{opt['nom']}** — {opt['description']}")

    with tab5:
        swot = st.session_state.swot
        st.caption(f"🔵 {_('swot_interne')} : {_('swot_forces')} / {_('swot_faiblesses')}   "
                   f"🟠 {_('swot_externe')} : {_('swot_opportunites')} / {_('swot_menaces')}")
        quad_cols = st.columns(2)
        quadrants = [
            ("forces", "🟢", quad_cols[0]),
            ("faiblesses", "🔴", quad_cols[1]),
        ]
        for key, emoji, col in quadrants:
            with col:
                st.markdown(f"**{emoji} {swot_label(key, lang)}**")
                items = swot.get(key, [])
                if items:
                    for it in items:
                        st.markdown(f"- {it}")
                else:
                    st.caption("—")
        quad_cols2 = st.columns(2)
        quadrants2 = [
            ("opportunites", "🟡", quad_cols2[0]),
            ("menaces", "🟠", quad_cols2[1]),
        ]
        for key, emoji, col in quadrants2:
            with col:
                st.markdown(f"**{emoji} {swot_label(key, lang)}**")
                items = swot.get(key, [])
                if items:
                    for it in items:
                        st.markdown(f"- {it}")
                else:
                    st.caption("—")


# ---------------------------------------------------------------------------
# Page : Plan stratégique (avec validation obligatoire avant export)
# ---------------------------------------------------------------------------
def page_plan():
    _ensure_diagnostic()
    diagnostic = st.session_state.current_diagnostic
    st.title(f"{_('nav_plan')} — {display_label(diagnostic)}")

    if "pestel" not in st.session_state:
        st.info(_("no_analysis_yet"))
        return

    if "plan" not in st.session_state or st.button("🔄 " + _("plan_title")):
        st.session_state.plan = generate_draft_plan(
            diagnostic, st.session_state.pestel, st.session_state.porter,
            st.session_state.bcg, st.session_state.ansoff,
            swot=st.session_state.get("swot"), lang=lang)

    plan = st.session_state.plan
    st.caption(_("plan_intro"))

    st.subheader(_("orientations"))
    orientations_text = st.text_area(_("orientations"), value="\n".join(plan["orientations"]),
                                      height=150, label_visibility="collapsed")
    plan["orientations"] = [o.strip("- ").strip() for o in orientations_text.split("\n") if o.strip()]

    st.subheader(_("action_plan"))
    edited = st.data_editor(
        plan["action_plan"], num_rows="dynamic", use_container_width=True,
        column_config={
            "action": st.column_config.TextColumn(_("action")),
            "responsable": st.column_config.TextColumn(_("responsable")),
            "echeance": st.column_config.TextColumn(_("echeance")),
            "indicateur": st.column_config.TextColumn(_("indicateur")),
        })
    plan["action_plan"] = edited
    st.session_state.plan = plan

    st.markdown("---")
    st.subheader(_("validation_title"))
    validator_name = st.text_input(_("validator_name"), value=diagnostic.get("conseiller", ""))
    confirm = st.checkbox(_("validation_checkbox"))

    if confirm and validator_name:
        validate_plan(diagnostic, validator_name)
        save_diagnostic(st.session_state.current_diagnostic_id, diagnostic)
        v = diagnostic["validation"]
        st.success(f"{_('validated_by')}: {v['validated_by']} — {_('validated_on')}: {v['date']}")

    st.markdown("---")
    if is_validated(diagnostic):
        include_name_plan = st.checkbox(_("include_real_name_export"), value=False,
                                         key="include_name_plan_export")
        if include_name_plan:
            st.caption(_("include_real_name_warning"))
        try:
            swot_data = st.session_state.get("swot")
            pdf_bytes = export_pdf_bytes(diagnostic, plan, lang, swot=swot_data,
                                          include_real_name=include_name_plan)
            word_bytes = export_word_bytes(diagnostic, plan, lang, swot=swot_data,
                                            include_real_name=include_name_plan)
            c1, c2 = st.columns(2)
            c1.download_button(_("download_pdf"), data=pdf_bytes,
                                file_name=f"plan_strategique_{diagnostic.get('code', 'diagnostic')}.pdf",
                                mime="application/pdf")
            c2.download_button(_("download_word"), data=word_bytes,
                                file_name=f"plan_strategique_{diagnostic.get('code', 'diagnostic')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except ExportNotAllowedError as e:
            st.error(str(e))
    else:
        st.warning(_("validation_required"))


# ---------------------------------------------------------------------------
# Page : Historique
# ---------------------------------------------------------------------------
def page_historique():
    st.title(_("nav_historique"))
    diagnostics = list_diagnostics(visible_owners=_get_visible_owners())
    if not diagnostics:
        st.info(_("no_diagnostics"))
        return
    for d in diagnostics:
        status = "✅ " + _("validated_on") if d["validated"] else "🕓"
        name_display = f"{d['code']} — {d['nom']}" if st.session_state.get("reveal_names") else d["code"]
        with st.container(border=True):
            st.markdown(f"**{name_display}** — {d['type']} — {d['conseiller']}  \n"
                        f"{status} — {_('branch_completion')}: {d['updated_at']}")


def page_administration():
    if not st.session_state.get("current_account", {}).get("is_admin"):
        st.error(_("access_denied"))
        return
    from modules.admin import render_admin_panel
    render_admin_panel(lang, st.session_state.get("current_user", ""))


def page_messagerie():
    from utils.hierarchy import list_all_accounts, visible_usernames
    from modules.messaging import send_message, list_messages_for, BROADCAST

    st.title(_("nav_messagerie"))

    # Rafraîchissement automatique périodique pour un effet quasi-temps réel.
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=20000, key="messagerie_autorefresh")
    except ImportError:
        st.caption(_("messagerie_manual_refresh_hint"))

    current_user = st.session_state.get("current_user", "")
    current_account = st.session_state.get("current_account", {})
    all_accounts = list_all_accounts()
    my_scope = visible_usernames(current_account, all_accounts) - {current_user}

    with st.form("send_message_form", clear_on_submit=True):
        options = [BROADCAST] + sorted(my_scope)
        labels = {BROADCAST: _("messagerie_tous")}
        recipient = st.selectbox(_("messagerie_destinataire"), options,
                                  format_func=lambda x: labels.get(x, x))
        body = st.text_area(_("messagerie_message"))
        if st.form_submit_button(_("messagerie_envoyer")) and body.strip():
            send_message(current_user, recipient, body.strip())
            from utils.activity_log import log_action
            log_action(current_user, "message_envoye", f"À : {recipient}")
            st.rerun()

    st.markdown("---")
    messages = list_messages_for(current_user, current_account=current_account, all_accounts=all_accounts)
    if not messages:
        st.info(_("messagerie_aucun_message"))
    for m in reversed(messages):
        with st.container(border=True):
            dest = _("messagerie_tous") if m["recipient"] == BROADCAST else m["recipient"]
            st.caption(f"**{m['sender']}** → {dest} — `{m['created_at'][:16]}`")
            st.markdown(m["body"])


# ---------------------------------------------------------------------------
# Routage
# ---------------------------------------------------------------------------
pages = {
    "dashboard": page_dashboard,
    "collecte": page_collecte,
    "analyse": page_analyse,
    "plan": page_plan,
    "historique": page_historique,
    "administration": page_administration,
    "messagerie": page_messagerie,
}
pages[st.session_state.page]()
