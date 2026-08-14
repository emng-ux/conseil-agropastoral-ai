"""Agent IA de conseil agropastoral — application principale Streamlit.

Fonctionnement hybride : le socle (formulaire, stockage, analyse, export) tourne
100% en local sans connexion Internet. Le chat IA et la transcription audio en
ligne s'activent uniquement si une connexion est détectée.
"""
import streamlit as st
import plotly.graph_objects as go

from utils.i18n import t
from utils.storage import (new_diagnostic_id, save_diagnostic, load_diagnostic,
                            delete_diagnostic, list_diagnostics)
from utils.connectivity import is_online
from modules.collecte import (branch_keys, branch_label, render_branch_form,
                               branch_completion_ratio)
from modules.import_data import build_template_dataframe, dataframe_to_excel_bytes, \
    import_file_to_diagnostic
from modules.analyse_pestel import compute_pestel, PESTEL_LABELS
from modules.analyse_porter import compute_porter
from modules.analyse_bcg import compute_bcg
from modules.analyse_ansoff import compute_ansoff
from modules.plan_strategique import generate_draft_plan, validate_plan, is_validated
from modules.export import export_pdf_bytes, export_word_bytes, ExportNotAllowedError

st.set_page_config(page_title="Conseil Agropastoral IA", page_icon="🌿", layout="wide")

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

    st.markdown("---")
    page_labels = {
        "dashboard": _("nav_dashboard"),
        "collecte": _("nav_collecte"),
        "analyse": _("nav_analyse"),
        "plan": _("nav_plan"),
        "historique": _("nav_historique"),
    }
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
def page_dashboard():
    st.title(_("nav_dashboard"))

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(_("existing_diagnostics"))
        diagnostics = list_diagnostics()
        if not diagnostics:
            st.info(_("no_diagnostics"))
        for d in diagnostics:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                status = "✅" if d["validated"] else "🕓"
                c1.markdown(f"**{status} {d['nom']}** — {d['type']}  \n_{d['conseiller']}_")
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
                diagnostic = {"nom": nom, "type": type_structure, "conseiller": conseiller, "etoile": {}}
                save_diagnostic(diagnostic_id, diagnostic)
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
    st.title(f"{_('nav_collecte')} — {diagnostic.get('nom', '')}")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.plotly_chart(_radar_chart(diagnostic), use_container_width=True)

        if st.session_state.online:
            from agent.orchestrator import agent_available, extract_fields_from_message, apply_updates
            if agent_available():
                st.markdown(f"**{_('nav_collecte')} — 🤖**")
                message = st.chat_input(_("chat_placeholder"))
                if message:
                    try:
                        result = extract_fields_from_message(message, diagnostic, lang)
                        apply_updates(diagnostic, result.get("updates", {}))
                        st.session_state.current_diagnostic = diagnostic
                        st.success(result.get("reply", ""))
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            st.info(_("chat_unavailable_offline"))

    with col2:
        tabs = st.tabs([branch_label(k, lang) for k in branch_keys()])
        for tab, key in zip(tabs, branch_keys()):
            with tab:
                render_branch_form(key, diagnostic, lang)

        if st.button(_("save"), type="primary"):
            save_diagnostic(st.session_state.current_diagnostic_id, diagnostic)
            st.success(_("saved"))


# ---------------------------------------------------------------------------
# Page : Analyse stratégique
# ---------------------------------------------------------------------------
def page_analyse():
    _ensure_diagnostic()
    diagnostic = st.session_state.current_diagnostic
    st.title(f"{_('nav_analyse')} — {diagnostic.get('nom', '')}")

    if st.button(_("run_analysis"), type="primary"):
        st.session_state.pestel = compute_pestel(diagnostic, lang)
        st.session_state.porter = compute_porter(diagnostic, lang)
        st.session_state.bcg = compute_bcg(diagnostic, lang)
        st.session_state.ansoff = compute_ansoff(diagnostic, lang)

    if "pestel" not in st.session_state:
        st.info(_("analysis_incomplete"))
        return

    tab1, tab2, tab3, tab4 = st.tabs([_("tab_pestel"), _("tab_porter"), _("tab_bcg"), _("tab_ansoff")])

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


# ---------------------------------------------------------------------------
# Page : Plan stratégique (avec validation obligatoire avant export)
# ---------------------------------------------------------------------------
def page_plan():
    _ensure_diagnostic()
    diagnostic = st.session_state.current_diagnostic
    st.title(f"{_('nav_plan')} — {diagnostic.get('nom', '')}")

    if "pestel" not in st.session_state:
        st.info(_("no_analysis_yet"))
        return

    if "plan" not in st.session_state or st.button("🔄 " + _("plan_title")):
        st.session_state.plan = generate_draft_plan(
            diagnostic, st.session_state.pestel, st.session_state.porter,
            st.session_state.bcg, st.session_state.ansoff, lang)

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
        try:
            pdf_bytes = export_pdf_bytes(diagnostic, plan, lang)
            word_bytes = export_word_bytes(diagnostic, plan, lang)
            c1, c2 = st.columns(2)
            c1.download_button(_("download_pdf"), data=pdf_bytes,
                                file_name=f"plan_strategique_{diagnostic.get('nom', 'diagnostic')}.pdf",
                                mime="application/pdf")
            c2.download_button(_("download_word"), data=word_bytes,
                                file_name=f"plan_strategique_{diagnostic.get('nom', 'diagnostic')}.docx",
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
    diagnostics = list_diagnostics()
    if not diagnostics:
        st.info(_("no_diagnostics"))
        return
    for d in diagnostics:
        status = "✅ " + _("validated_on") if d["validated"] else "🕓"
        with st.container(border=True):
            st.markdown(f"**{d['nom']}** — {d['type']} — {d['conseiller']}  \n"
                        f"{status} — {_('branch_completion')}: {d['updated_at']}")


# ---------------------------------------------------------------------------
# Routage
# ---------------------------------------------------------------------------
pages = {
    "dashboard": page_dashboard,
    "collecte": page_collecte,
    "analyse": page_analyse,
    "plan": page_plan,
    "historique": page_historique,
}
pages[st.session_state.page]()
