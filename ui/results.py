import streamlit as st
from ui.export import export_clarifications_docx, export_proposal_docx


def _severity_emoji(severity: str) -> str:
    return {"high": "\U0001f534", "medium": "\U0001f7e0", "low": "\U0001f7e2"}.get(severity.lower(), "\u26aa")


def render_results():
    results = st.session_state.get("analysis_results", {})
    if not results:
        return

    tab_summary, tab_clarify, tab_proposal, tab_fulltext = st.tabs(
        ["Summary", "Clarifications", "Proposal Draft", "Full Text"]
    )

    with tab_summary:
        _render_summary(results.get("summary", {}))

    with tab_clarify:
        _render_clarifications(results.get("clarifications", []))

    with tab_proposal:
        _render_proposal(results)

    with tab_fulltext:
        _render_fulltext()


def _render_summary(summary: dict):
    if not summary or summary.get("_parse_error"):
        st.warning("Summary could not be parsed. Raw response below.")
        st.code(summary.get("_raw_response", "No data"))
        return

    # Organization header
    org = summary.get("issuing_organization", {})
    st.subheader(f"{org.get('name', 'Unknown Organization')}")
    col1, col2, col3 = st.columns(3)
    col1.write(f"**Type:** {org.get('type', 'N/A')}")
    col2.write(f"**Sector:** {org.get('sector', 'N/A')}")
    col3.write(f"**Document:** {summary.get('document_type', 'N/A')}")

    listed = org.get("listed_entity")
    report_type = summary.get("report_type", "N/A")
    listed_text = " (Listed)" if listed else ""
    st.write(f"**Report Type:** {report_type}{listed_text}")

    # Framework Detection Badge — THE KEY FEATURE
    st.divider()
    frameworks = summary.get("frameworks", {})
    detected = frameworks.get("detected", [])
    implied = frameworks.get("implied", [])
    recommended = frameworks.get("recommended_frameworks", [])
    no_framework = frameworks.get("no_framework_detected", False)

    if no_framework and recommended:
        st.error("**No Reporting Framework Specified in RFQ**")
        st.warning(
            f"**Recommended Frameworks for {org.get('sector', 'this sector')}:** "
            f"{' | '.join(recommended)}"
        )
        notes = frameworks.get("framework_notes", "")
        if notes:
            st.info(f"**Why:** {notes}")
    elif no_framework:
        st.error(
            "**No Reporting Framework Detected** — This document does not specify a reporting "
            "framework. Check the Clarifications tab for recommended frameworks based on the "
            "organization's sector."
        )
    elif detected:
        framework_tags = " | ".join(detected)
        st.success(f"**Frameworks Detected:** {framework_tags}")
        if implied:
            st.info(f"**Also Implied:** {' | '.join(implied)}")
        notes = frameworks.get("framework_notes", "")
        if notes:
            st.caption(notes)
    else:
        st.info("No specific reporting framework requirements identified.")

    # Scope of Work
    st.divider()
    scope = summary.get("scope_of_work", {})
    st.subheader("Scope of Work")
    st.write(scope.get("description", "N/A"))

    if scope.get("deliverables"):
        st.write("**Deliverables:**")
        for d in scope["deliverables"]:
            st.write(f"- {d}")

    # Print specs
    specs = scope.get("print_specs", {})
    if any(v for v in specs.values() if v):
        st.write("**Print Specifications:**")
        spec_cols = st.columns(3)
        spec_items = [(k.replace("_", " ").title(), v) for k, v in specs.items() if v]
        for i, (label, value) in enumerate(spec_items):
            spec_cols[i % 3].write(f"**{label}:** {value}")

    if scope.get("digital_deliverables"):
        st.write(f"**Digital:** {', '.join(scope['digital_deliverables'])}")

    if scope.get("languages"):
        st.write(f"**Languages:** {', '.join(scope['languages'])}")

    # Timeline
    timeline = summary.get("timeline", {})
    if timeline.get("key_dates"):
        st.divider()
        st.subheader("Key Dates")
        for date_item in timeline["key_dates"]:
            notes = f" — {date_item['notes']}" if date_item.get("notes") else ""
            st.write(f"- **{date_item.get('event', 'N/A')}:** {date_item.get('date', 'N/A')}{notes}")

    if timeline.get("project_duration"):
        st.write(f"**Project Duration:** {timeline['project_duration']}")

    # Evaluation
    eval_c = summary.get("evaluation_criteria", {})
    if eval_c.get("scoring_parameters"):
        st.divider()
        st.subheader("Evaluation Criteria")
        st.write(f"**Method:** {eval_c.get('method', 'N/A')}")
        if eval_c.get("technical_weightage") or eval_c.get("financial_weightage"):
            st.write(
                f"**Technical:** {eval_c.get('technical_weightage', 'N/A')} | "
                f"**Financial:** {eval_c.get('financial_weightage', 'N/A')}"
            )
        for p in eval_c["scoring_parameters"]:
            marks = f" ({p['max_marks']} marks)" if p.get("max_marks") else ""
            st.write(f"- {p.get('parameter', 'N/A')}{marks}")

    # Financial
    fin = summary.get("financial_terms", {})
    if any(v for v in fin.values() if v):
        st.divider()
        st.subheader("Financial Terms")
        for key, val in fin.items():
            if val:
                st.write(f"**{key.replace('_', ' ').title()}:** {val}")

    # Submission
    sub = summary.get("submission_requirements", {})
    if sub and any(v for v in sub.values() if v):
        st.divider()
        st.subheader("Submission")
        if sub.get("format"):
            st.write(f"**Format:** {sub['format']}")
        if sub.get("email_addresses"):
            st.write(f"**Email:** {', '.join(sub['email_addresses'])}")
        if sub.get("separate_technical_commercial"):
            st.write("**Separate technical & commercial bids required**")

    # Contact
    contacts = summary.get("contact_information", [])
    if contacts:
        st.divider()
        st.subheader("Contact Information")
        for c in contacts:
            parts = [v for k, v in c.items() if v]
            if parts:
                st.write(f"- {' | '.join(parts)}")


def _normalize_clarifications(clarifications):
    """Ensure clarifications is a proper list."""
    if isinstance(clarifications, dict) and clarifications.get("_parse_error"):
        return None, clarifications.get("_raw_response", "No data")
    if isinstance(clarifications, dict):
        for key in clarifications:
            if isinstance(clarifications[key], list):
                return clarifications[key], None
    if isinstance(clarifications, list):
        return clarifications, None
    return None, str(clarifications)


def _render_clarifications(clarifications):
    if not clarifications:
        st.info("No clarification questions generated.")
        return

    clarifications, error = _normalize_clarifications(clarifications)
    if error:
        st.warning("Clarifications could not be parsed. Raw response below.")
        st.code(error)
        return
    if not clarifications:
        st.info("No clarification questions generated.")
        return

    # Initialize answers in session state
    if "clarification_answers" not in st.session_state:
        st.session_state.clarification_answers = {}

    # Count by severity
    high = sum(1 for q in clarifications if q.get("severity", "").lower() == "high")
    medium = sum(1 for q in clarifications if q.get("severity", "").lower() == "medium")
    low = sum(1 for q in clarifications if q.get("severity", "").lower() == "low")
    answered = sum(1 for i in range(len(clarifications)) if st.session_state.clarification_answers.get(f"ans_{i}", "").strip())

    # Header row: metrics + download
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    col1.metric("Total", len(clarifications))
    col2.metric("High", high)
    col3.metric("Medium", medium)
    col4.metric("Answered", f"{answered}/{len(clarifications)}")
    with col5:
        filename = st.session_state.get("uploaded_filename", "document")
        docx_bytes = export_clarifications_docx(clarifications, filename)
        st.download_button(
            "Download Questions DOCX",
            data=docx_bytes,
            file_name=f"{filename}_clarifications.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    if answered > 0:
        st.success(f"{answered} questions answered. These answers will be used to generate a more accurate proposal draft.")
    else:
        st.caption("Answer the questions below (optional). Your answers help the AI generate a more accurate proposal in the Proposal Draft tab.")

    st.divider()

    # Render all questions with answer fields
    all_qs = clarifications
    # Framework questions first
    framework_qs = [(i, q) for i, q in enumerate(all_qs) if q.get("category", "").lower() == "framework"]
    other_qs = [(i, q) for i, q in enumerate(all_qs) if q.get("category", "").lower() != "framework"]

    if framework_qs:
        st.subheader("Framework & Reporting Standards")
        for idx, q in framework_qs:
            _render_question_with_answer(idx, q, expanded=True)
        st.divider()

    for idx, q in other_qs:
        severity = q.get("severity", "unknown").lower()
        _render_question_with_answer(idx, q, expanded=(severity == "high"))


def _render_question_with_answer(idx: int, q: dict, expanded: bool = False):
    """Render a single clarification question with an answer text input."""
    severity = q.get("severity", "unknown").lower()
    category = q.get("category", "general").upper()
    emoji = _severity_emoji(severity)
    has_answer = bool(st.session_state.clarification_answers.get(f"ans_{idx}", "").strip())
    check = " \u2705" if has_answer else ""

    label = f"{emoji} [{category}] {q.get('question', 'N/A')}{check}" if category != "FRAMEWORK" else f"{emoji} {q.get('question', 'N/A')}{check}"

    with st.expander(label, expanded=expanded):
        st.write(f"**Section:** {q.get('section_reference', 'N/A')}")
        st.write(f"**Why this matters:** {q.get('reason', 'N/A')}")
        st.text_input(
            "Your answer",
            key=f"ans_{idx}",
            placeholder="Type your answer here (optional — helps generate better proposal)",
            label_visibility="collapsed",
            on_change=_save_answer,
            args=(idx,),
        )


def _save_answer(idx: int):
    """Save answer to session state."""
    val = st.session_state.get(f"ans_{idx}", "")
    st.session_state.clarification_answers[f"ans_{idx}"] = val


def get_answered_clarifications() -> list[dict]:
    """Get clarifications with their answers for passing to proposal generator."""
    results = st.session_state.get("analysis_results", {})
    clarifications = results.get("clarifications", [])
    clarifications, _ = _normalize_clarifications(clarifications)
    if not clarifications:
        return []

    answered = []
    for i, q in enumerate(clarifications):
        answer = st.session_state.get("clarification_answers", {}).get(f"ans_{i}", "").strip()
        if answer:
            answered.append({
                "question": q.get("question", ""),
                "category": q.get("category", ""),
                "answer": answer,
            })
    return answered


def _render_proposal(results: dict):
    proposal_text = results.get("proposal")

    if not proposal_text:
        summary = results.get("summary", {})
        org_name = summary.get("issuing_organization", {}).get("name", "Unknown")
        report_type = summary.get("report_type", "Unknown")

        st.write("Generate a proposal draft based on the RFQ analysis. The proposal follows WyattPrism's standard format.")

        # Show how many clarifications have been answered
        answered = get_answered_clarifications()
        if answered:
            st.success(f"{len(answered)} clarification answers will be used to generate a more tailored proposal.")
        else:
            st.caption("Tip: Answer some questions in the Clarifications tab first for a more accurate proposal.")

        st.info(f"Ready to draft proposal for **{org_name}** — {report_type}")

        if st.button("Generate Proposal Draft", type="primary", use_container_width=True):
            from analysis.proposal import generate_proposal
            from analysis.client import ClaudeClient
            from ui.history import update_analysis_results

            model = "claude-sonnet-4-20250514"
            client = ClaudeClient(model=model)

            doc = st.session_state.get("parsed_doc")
            doc_text = doc.raw_text if doc else ""

            proposal_generated = False
            with st.spinner("Drafting proposal in WyattPrism format..."):
                try:
                    proposal = generate_proposal(client, doc_text, summary, answered)
                    st.session_state.analysis_results["proposal"] = proposal
                    proposal_generated = True
                except Exception as e:
                    st.error(f"Proposal generation failed: {e}")

            # Separate the shell sync from the generation so a sync failure
            # is shown to the user instead of looking like a generation failure.
            if proposal_generated:
                try:
                    update_analysis_results(
                        st.session_state.get("current_record_id"),
                        st.session_state.analysis_results,
                    )
                except Exception as e:
                    st.error(
                        f"Proposal generated, but syncing to Wyattprism failed: {e}"
                    )
                st.rerun()
        return

    # Display the proposal
    summary = results.get("summary", {})
    org_name = summary.get("issuing_organization", {}).get("name", "Unknown")
    report_type = summary.get("report_type", "Unknown")
    filename = st.session_state.get("uploaded_filename", "document")

    # Download button at the top
    col1, col2 = st.columns([1, 4])
    with col1:
        docx_bytes = export_proposal_docx(proposal_text, org_name, report_type)
        st.download_button(
            "Download Proposal DOCX",
            data=docx_bytes,
            file_name=f"Proposal_{org_name.replace(' ', '_')}_{report_type.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
    with col2:
        if st.button("Regenerate"):
            st.session_state.analysis_results.pop("proposal", None)
            st.rerun()

    st.divider()

    # Display proposal text with nice formatting
    lines = proposal_text.strip().split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            st.write("")
        elif stripped.startswith("Proposal for"):
            st.subheader(stripped)
        elif any(stripped.startswith(kw) for kw in [
            "Scope of Work", "Please note", "Please Note", "Timeline",
            "Costing", "Payment terms", "Payment Terms", "Benefits",
        ]):
            st.write(f"**{stripped}**")
        elif stripped.startswith(("-", "\u2022")):
            st.write(f"  {stripped}")
        elif stripped.startswith("Dear "):
            st.write(f"*{stripped}*")
        elif stripped.startswith("Sincerely") or stripped.startswith("CA ") or stripped.startswith("+91"):
            st.write(f"**{stripped}**")
        else:
            st.write(stripped)

    # === STATUS TRACKER ===
    from ui.history import render_status_tracker
    render_status_tracker()


def _render_fulltext():
    doc = st.session_state.get("parsed_doc")
    if doc:
        st.text_area(
            "Full Extracted Text",
            value=doc.raw_text,
            height=600,
            disabled=True,
        )
    else:
        st.info("No document loaded.")
