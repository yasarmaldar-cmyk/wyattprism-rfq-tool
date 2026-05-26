import json
import streamlit as st
from datetime import date


def render_manual_form() -> dict | None:
    """Render a manual requirement form for verbal/no-RFQ scenarios.
    Returns a summary dict (same structure as AI-generated) if submitted, else None."""

    st.subheader("Manual Requirement Form")
    st.caption("No RFQ document? Fill in the details from your conversation with the client.")

    # Wyattprism Platform pre-fill — values arrive from the shell via query params
    # and are stashed in session_state at startup. We use them as defaults here.
    _wp_client = st.session_state.get("wp_client_name", "")
    _wp_industry = st.session_state.get("wp_industry", "")
    _wp_report_type = st.session_state.get("wp_report_type", "")

    _sectors = [
        "BFSI", "Energy / Oil & Gas", "Mining & Metals",
        "Infrastructure / Construction", "IT / Technology",
        "Manufacturing", "Healthcare / Pharma", "FMCG / Consumer",
        "Chemicals", "Automobile", "Telecom", "Real Estate",
        "Logistics", "Government / PSU", "Other",
    ]
    _report_types = [
        "Annual Report", "Integrated Annual Report", "Sustainability Report",
        "ESG Report", "Corporate Brochure", "CSR Report", "Other",
    ]

    def _idx(options, value, default=0):
        if value and value in options:
            return options.index(value)
        return default

    with st.form("manual_rfq_form"):

        # === CLIENT INFO ===
        st.markdown("**Client Information**")
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input(
                "Company Name *",
                value=_wp_client,
                placeholder="e.g., Nayara Energy Limited",
            )
            sector = st.selectbox(
                "Sector", _sectors,
                index=_idx(_sectors, _wp_industry, default=_sectors.index("Other")),
            )
        with col2:
            org_type = st.selectbox("Organization Type", [
                "Private", "PSU", "Government", "MNC", "NGO", "Other",
            ])
            listed = st.selectbox("Listed Entity?", ["Yes", "No", "Not Sure"])

        # === REPORT TYPE ===
        st.divider()
        st.markdown("**Report Details**")
        col1, col2, col3 = st.columns(3)
        with col1:
            report_type = st.selectbox(
                "Report Type *", _report_types,
                index=_idx(_report_types, _wp_report_type),
            )
        with col2:
            fy_year = st.text_input("Financial Year", value="FY 2025-26")
        with col3:
            timeline = st.text_input("Expected Timeline", placeholder="e.g., 4 months, 6 weeks")

        # === SCOPE CUSTOMIZATION — THE KEY SECTION ===
        st.divider()
        st.markdown("**Scope of Work — What are we doing?**")

        # Theme & Concept
        col1, col2 = st.columns(2)
        with col1:
            do_theme = st.selectbox("Theme & Concept", [
                "WP creates theme & concept",
                "Client provides theme, WP designs",
                "Not required",
            ])
        with col2:
            do_cover = st.selectbox("Cover Design", [
                "WP designs cover",
                "Client provides cover, WP adapts",
                "Client provides final cover",
                "Not required",
            ])

        # Content / Writing
        st.markdown("**Content & Writing**")
        col1, col2 = st.columns(2)
        with col1:
            do_content = st.selectbox("Non-Financial Content (Theme pages, Operations Review, etc.)", [
                "WP writes + designs (full content development)",
                "Client provides content, WP edits & designs",
                "Client provides final content, WP only designs/layouts",
                "Not required",
            ])
            content_pages = st.number_input("Estimated non-financial pages", value=40, min_value=0)
        with col2:
            do_mda = st.selectbox("MDA Section", [
                "WP writes MDA based on client inputs",
                "WP edits & enhances client-drafted MDA",
                "Client provides final MDA, WP only layouts",
                "Not required",
            ])
            mda_pages = st.number_input("Estimated MDA pages", value=10, min_value=0)

        # Chairman / Director Messages
        col1, col2 = st.columns(2)
        with col1:
            do_chairman = st.selectbox("Chairman / MD Message", [
                "WP drafts message",
                "Client provides content, WP designs",
                "Not required",
            ])
        with col2:
            do_director_report = st.selectbox("Board / Director's Report", [
                "WP edits & enhances",
                "Client provides, WP layouts",
                "Not required",
            ])

        # Financial / Statutory Section
        st.markdown("**Financial & Statutory Section**")
        col1, col2 = st.columns(2)
        with col1:
            do_financial = st.selectbox("Financial Statements & Statutory Section", [
                "WP designs template + does full layout",
                "WP provides template, client does layout",
                "WP provides template, layout done at client's end",
                "Client handles entirely",
                "Not required",
            ])
            financial_pages = st.number_input("Estimated financial/statutory pages", value=200, min_value=0)
        with col2:
            do_brsr = st.selectbox("BRSR Section", [
                "Client provides BRSR data, WP layouts",
                "WP assists with BRSR content + layout",
                "Not applicable",
            ])
            do_cg_report = st.selectbox("Corporate Governance Report", [
                "Client provides, WP layouts",
                "WP edits & layouts",
                "Not required",
            ])

        # ESG / Sustainability specific
        st.markdown("**ESG / Sustainability (if applicable)**")
        col1, col2 = st.columns(2)
        with col1:
            do_esg = st.selectbox("ESG / Sustainability Section", [
                "WP develops ESG narrative + design",
                "Client provides ESG content, WP designs",
                "Not applicable",
            ])
            esg_pages = st.number_input("Estimated ESG pages", value=0, min_value=0)
        with col2:
            frameworks = st.multiselect("Reporting Frameworks & Regulatory Requirements", [
                "SEBI LODR", "Companies Act 2013", "BRSR (SEBI)", "BRSR Core",
                "GRI Standards", "TCFD", "IR Framework (IIRC)",
                "IFRS S1/S2 (ISSB)", "SDGs", "SASB", "CDP",
                "UN Global Compact", "DPE Guidelines (CPSE)", "AA1000",
                "None / Not Discussed", "Client to Confirm",
            ])

        # Integrated Report specific
        if report_type == "Integrated Annual Report":
            st.markdown("**Integrated Reporting Specific**")
            col1, col2 = st.columns(2)
            with col1:
                do_ir_gap_review = st.checkbox("Data Gap Review", value=True)
                do_ir_capacity = st.checkbox("Capacity Building Sessions", value=True)
            with col2:
                do_ir_core_team = st.checkbox("Help Set Core Team", value=True)
                do_ir_content = st.checkbox("IR Content Development", value=True)

        # Production & Delivery
        st.divider()
        st.markdown("**Production & Delivery**")
        col1, col2 = st.columns(2)
        with col1:
            do_hires = st.selectbox("High-Res Conversion & Print-Ready Files", [
                "Yes — WP delivers print-ready files",
                "Not required",
            ])
            do_printing = st.selectbox("Printing", [
                "Not included (client handles)",
                "WP supervises printing",
                "WP handles full printing & delivery",
            ])
        with col2:
            copies = st.text_input("Number of copies (if printing)", placeholder="e.g., 500")
            do_versions = st.multiselect("Report Versions Needed", [
                "Full Color (Print)", "Full Color (Online PDF)",
                "B&W / Junta Version", "Abridged Version",
                "Hindi Version", "Regional Language Version",
            ])

        # Digital Report
        st.divider()
        st.markdown("**Digital Report**")
        do_digital = st.selectbox("Digital E-Report (Microsite)", [
            "Yes — include in proposal",
            "Propose as optional add-on",
            "Not required",
        ])
        do_rag_ai = st.checkbox("RAG AI Interactive Assistant (optional add-on)", value=True)
        do_flipbook = st.checkbox("Animated Flipbook Version (optional add-on)", value=False)
        do_video = st.checkbox("120-Second Highlights Video (optional add-on)", value=False)
        do_eco = st.checkbox("Eco-Friendly Digital Report (optional add-on)", value=False)

        # Additional Notes
        st.divider()
        st.markdown("**Additional Notes**")
        notes = st.text_area(
            "Any other requirements or special instructions",
            placeholder="e.g., Need 5 theme options, client wants photography session, AGM Notice design needed, etc.",
            height=100,
        )

        # Submit
        submitted = st.form_submit_button("Generate Proposal", type="primary", use_container_width=True)

    if not submitted:
        return None

    if not client_name.strip():
        st.error("Company name is required.")
        return None

    # Build scope items based on selections
    scope_deliverables = []
    scope_notes = []

    # Theme
    if do_theme == "WP creates theme & concept":
        scope_deliverables.append("Conceptualize and provide theme suggestions for the report based on macro developments in the industry and strategic focus")
    elif do_theme == "Client provides theme, WP designs":
        scope_deliverables.append("Design execution based on theme direction provided by client")
        scope_notes.append("Theme/concept to be provided by client")

    # Cover
    if do_cover == "WP designs cover":
        scope_deliverables.append("Creating the Cover Design and defining the Visual Properties of the document")
    elif do_cover == "Client provides cover, WP adapts":
        scope_deliverables.append("Adapting and refining cover design based on client-provided concept")
        scope_notes.append("Base cover concept to be provided by client")
    elif do_cover == "Client provides final cover":
        scope_notes.append("Cover design to be provided by client in final form")

    # Chairman message
    if do_chairman == "WP drafts message":
        scope_deliverables.append("Drafting of Chairman/MD message based on inputs and strategic direction")
    elif do_chairman == "Client provides content, WP designs":
        scope_deliverables.append("Design and layout of Chairman/MD message (content provided by client)")

    # Content
    if "WP writes" in do_content:
        scope_deliverables.append(f"Concept, research and writing of content for non-financial section including theme pages, management messages, and operations review (estimated pages: {content_pages})")
    elif "WP edits" in do_content:
        scope_deliverables.append(f"Editing, enhancing and designing of non-financial content provided by client (estimated pages: {content_pages})")
        scope_notes.append("Non-financial content/inputs to be provided by client")
    elif "WP only designs" in do_content:
        scope_deliverables.append(f"Design and layout of non-financial section from final content provided by client (estimated pages: {content_pages})")
        scope_notes.append("All non-financial content to be provided by client in final form")

    # MDA
    if "WP writes" in do_mda:
        scope_deliverables.append(f"Draft, write and design the MDA section based on industry and company specific information (estimated pages: {mda_pages})")
    elif "WP edits" in do_mda:
        scope_deliverables.append(f"Edit, enhance and design the MDA section based on client draft (estimated pages: {mda_pages})")
    elif "WP only layouts" in do_mda:
        scope_deliverables.append(f"Layout of MDA section from final content provided by client (estimated pages: {mda_pages})")
        scope_notes.append("MDA content to be provided by client")

    # Director Report
    if "WP edits" in do_director_report:
        scope_deliverables.append("Editing, enhancement and layout of Board/Director's Report")
    elif "WP layouts" in do_director_report:
        scope_deliverables.append("Layout of Board/Director's Report (content provided by client)")

    # Financial
    if "full layout" in do_financial:
        scope_deliverables.append(f"Designing template and full layout of financial/statutory section — Director's Report, Auditor's Report, CG Report, BRSR, Accounts, Notice etc. (estimated pages: {financial_pages})")
    elif "client does layout" in do_financial or "client's end" in do_financial:
        scope_deliverables.append(f"Designing template for financial/statutory section — layout to be done at client's end (estimated pages: {financial_pages})")
        scope_notes.append("Financial section layout to be done at client's end using WP-provided template")
    elif "Client handles" in do_financial:
        scope_notes.append("Financial/statutory section handled entirely by client")

    # BRSR
    if "WP assists" in do_brsr:
        scope_deliverables.append("BRSR content development assistance and layout design")
    elif "WP layouts" in do_brsr:
        scope_deliverables.append("Layout of BRSR section (data/content to be shared by client)")
        scope_notes.append("BRSR data to be provided by client")

    # CG Report
    if "WP edits" in do_cg_report:
        scope_deliverables.append("Editing and layout of Corporate Governance Report")
    elif "WP layouts" in do_cg_report:
        scope_deliverables.append("Layout of Corporate Governance Report (content provided by client)")

    # ESG
    if "WP develops" in do_esg:
        scope_deliverables.append(f"ESG/Sustainability narrative development, content writing and design (estimated pages: {esg_pages})")
    elif "WP designs" in do_esg:
        scope_deliverables.append(f"Design and layout of ESG/Sustainability section (content provided by client, estimated pages: {esg_pages})")

    # IR specific
    if report_type == "Integrated Annual Report":
        if do_ir_gap_review:
            scope_deliverables.append("Data Gap Review — review of existing reports and data points for IR content elements")
        if do_ir_core_team:
            scope_deliverables.append("Help in forming a Core Team with representatives from various functions/departments")
        if do_ir_capacity:
            scope_deliverables.append("Capacity Building sessions on integrated reporting, global reporting trends, and IIRC Framework")
        if do_ir_content:
            scope_deliverables.append("IR Content Development — blueprint of report structure, supporting development of IR sections with core team")

    # High-res
    if "Yes" in do_hires:
        scope_deliverables.append("High-resolution conversion of the entire report — cover to cover — and delivery of print-ready files")

    # Versions
    if do_versions:
        scope_deliverables.append(f"Preparation of report versions: {', '.join(do_versions)}")

    # Printing
    if "supervises" in do_printing:
        scope_deliverables.append(f"Print supervision and quality control{' — ' + copies + ' copies' if copies else ''}")
    elif "full printing" in do_printing:
        scope_deliverables.append(f"Complete printing and delivery{' — ' + copies + ' copies' if copies else ''}")

    # Build the summary dict (same structure as AI-generated)
    fw_detected = [f for f in frameworks if f not in ["None / Not Discussed", "Client to Confirm"]]
    no_framework = "None / Not Discussed" in frameworks or not fw_detected
    client_to_confirm = "Client to Confirm" in frameworks

    summary = {
        "issuing_organization": {
            "name": client_name.strip(),
            "type": org_type,
            "sector": sector,
            "listed_entity": listed == "Yes",
        },
        "document_type": "Verbal Brief",
        "report_type": report_type,
        "scope_of_work": {
            "description": f"{report_type} for {client_name.strip()} — {fy_year}",
            "deliverables": scope_deliverables,
            "print_specs": {
                "page_count": str(content_pages + mda_pages + financial_pages + esg_pages) if any([content_pages, financial_pages]) else None,
                "copies": copies if copies else None,
                "paper_gsm": None,
                "binding": None,
                "size": None,
                "other": None,
            },
            "digital_deliverables": [],
            "languages": [],
        },
        "frameworks": {
            "detected": fw_detected,
            "implied": [],
            "recommended_frameworks": [],
            "no_framework_detected": no_framework,
            "framework_notes": "Client to confirm framework requirements" if client_to_confirm else "",
        },
        "timeline": {
            "key_dates": [],
            "project_duration": timeline if timeline else None,
            "phases": [],
        },
        "evaluation_criteria": {"method": "N/A — verbal brief", "scoring_parameters": []},
        "financial_terms": {},
        "submission_requirements": {},
        "special_requirements": scope_notes,
        "contact_information": [],
        "_manual_form": True,
        "_form_options": {
            "do_digital": do_digital,
            "do_rag_ai": do_rag_ai,
            "do_flipbook": do_flipbook,
            "do_video": do_video,
            "do_eco": do_eco,
            "notes": notes,
        },
    }

    return summary
