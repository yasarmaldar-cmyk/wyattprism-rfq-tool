import streamlit as st
import json
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from analysis.client import ClaudeClient
from analysis.summary import analyze_summary
from analysis.clarifications import analyze_clarifications
from analysis.proposal import generate_proposal
from ui.upload import render_upload
from ui.results import render_results
from ui.profile_editor import render_profile_editor
from ui.export import render_export
from ui.theme import inject_glassmorphism
from ui.history import render_history_sidebar, save_analysis
from ui.manual_form import render_manual_form
from ui.dashboard import render_dashboard

# Page config
st.set_page_config(
    page_title="RFQ Analyzer | WP",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject glassmorphism theme
inject_glassmorphism()

# === Wyattprism Platform integration ===
# When opened from the Wyattprism Project Platform shell, query params carry the
# project context so the manual form can be pre-filled. The wp_project_id is
# stored on every history record so the shell can pull results back.
_qp = st.query_params
for _k in ("wp_project_id", "wp_project_code", "wp_client_name",
           "wp_industry", "wp_report_type", "wp_scope", "wp_proposed_cost"):
    if _k in _qp and _qp[_k]:
        st.session_state[_k] = _qp[_k]
# Default to manual-entry mode if we arrived from the shell
if "wp_project_id" in st.session_state and "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "manual"

# Header
st.title("RFQ / RFP Analyzer")
if st.session_state.get("wp_project_id"):
    _code = st.session_state.get("wp_project_code", "")
    _client = st.session_state.get("wp_client_name", "")
    st.info(
        f"**Linked to Wyattprism project {_code}** — {_client}. "
        "When you generate a proposal, it will be available to import back into the platform."
    )
else:
    st.caption("Upload an RFQ document or fill in requirements manually to generate analysis and proposals.")

# Sidebar: Export buttons (only shown after analysis)
render_export()

# Sidebar: History
render_history_sidebar()

# Sidebar: Company profile (collapsed)
with st.sidebar.expander("Company Profile", expanded=False):
    profile = render_profile_editor()

# === MAIN CONTENT — Two modes ===
_default_mode_idx = 1 if st.session_state.get("wp_project_id") else 0
mode = st.radio(
    "Mode",
    ["Upload RFQ / RFP Document", "Manual Entry (Verbal Brief)", "Dashboard"],
    horizontal=True,
    label_visibility="collapsed",
    index=_default_mode_idx,
)

if mode == "Upload RFQ / RFP Document":
    # --- RFQ Upload Mode ---
    has_document = render_upload()

    if has_document:
        doc = st.session_state.parsed_doc

        if doc.char_count < 100 and doc.page_count > 1:
            st.warning(
                "This document appears to be scanned/image-based with very little extractable text. "
                "Consider running OCR (e.g., Adobe Acrobat) before uploading."
            )
        else:
            model = "claude-sonnet-4-20250514"

            if st.button("Analyze Document", type="primary", use_container_width=True):
                st.session_state.history_loaded = False
                st.session_state.clarification_answers = {}

                client = ClaudeClient(model=model)
                results = {}

                with st.status("Analyzing document...", expanded=True) as status:
                    st.write("Analyzing RFQ — extracting scope, timeline, frameworks...")
                    try:
                        results["summary"] = analyze_summary(client, doc.raw_text)
                        st.write("✓ Summary and framework analysis complete")
                    except Exception as e:
                        st.error(f"Summary failed: {e}")
                        results["summary"] = {"_parse_error": True, "_raw_response": str(e)}

                    st.write("Generating clarification questions...")
                    try:
                        summary_context = results.get("summary", {})
                        results["clarifications"] = analyze_clarifications(
                            client, doc.raw_text, summary_context
                        )
                        st.write("✓ Clarification questions ready")
                    except Exception as e:
                        st.error(f"Clarifications failed: {e}")
                        results["clarifications"] = []

                    status.update(label="Analysis complete!", state="complete")

                st.session_state.analysis_results = results

                filename = st.session_state.get("uploaded_filename", "document")
                doc_meta = {
                    "page_count": doc.page_count,
                    "char_count": doc.char_count,
                    "file_type": doc.file_type,
                }
                save_analysis(filename, results, doc_meta)

            render_results()

elif mode == "Manual Entry (Verbal Brief)":
    # --- Manual Form Mode ---
    manual_summary = render_manual_form()

    if manual_summary:
        # Form was submitted — generate proposal directly
        st.session_state.history_loaded = False
        st.session_state.clarification_answers = {}

        client_name = manual_summary["issuing_organization"]["name"]
        report_type = manual_summary["report_type"]

        # Build a text representation of the manual brief for the proposal generator
        brief_text = f"Verbal Brief for {client_name} — {report_type} {manual_summary['timeline'].get('project_duration', '')}\n\n"
        brief_text += "Scope:\n"
        for d in manual_summary["scope_of_work"]["deliverables"]:
            brief_text += f"- {d}\n"
        if manual_summary.get("special_requirements"):
            brief_text += "\nNotes:\n"
            for n in manual_summary["special_requirements"]:
                brief_text += f"- {n}\n"
        form_opts = manual_summary.get("_form_options", {})
        if form_opts.get("notes"):
            brief_text += f"\nAdditional: {form_opts['notes']}\n"

        results = {"summary": manual_summary, "clarifications": []}

        # Generate proposal directly
        with st.status("Generating proposal from your brief...", expanded=True) as status:
            st.write(f"Creating proposal for {client_name} — {report_type}...")
            try:
                model = "claude-sonnet-4-20250514"
                client = ClaudeClient(model=model)
                proposal = generate_proposal(client, brief_text, manual_summary)
                results["proposal"] = proposal
                st.write("✓ Proposal draft ready")
            except Exception as e:
                st.error(f"Proposal generation failed: {e}")

            status.update(label="Proposal ready!", state="complete")

        st.session_state.analysis_results = results
        st.session_state.uploaded_filename = f"{client_name} — {report_type}"

        # Auto-save
        save_analysis(
            f"{client_name} — {report_type} (Manual)",
            results,
            {"page_count": 0, "char_count": len(brief_text), "file_type": "manual"},
        )

        render_results()

elif mode == "Dashboard":
    render_dashboard()

# If loaded from history
elif st.session_state.get("history_loaded") and st.session_state.get("analysis_results"):
    st.info(f"Showing saved analysis: **{st.session_state.get('uploaded_filename', 'Unknown')}**")
    render_results()
