import streamlit as st
from parsers import parse_pdf, parse_docx


def render_upload():
    uploaded_file = st.file_uploader(
        "Upload RFQ / RFP Document",
        type=["pdf", "docx"],
        help="Supported formats: PDF, DOCX (up to 50MB)",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name

        # Parse only if it's a new file
        if (
            "parsed_doc" not in st.session_state
            or st.session_state.get("uploaded_filename") != filename
        ):
            with st.spinner("Parsing document..."):
                if filename.lower().endswith(".pdf"):
                    doc = parse_pdf(file_bytes, filename)
                else:
                    doc = parse_docx(file_bytes, filename)
                st.session_state.parsed_doc = doc
                st.session_state.uploaded_filename = filename
                # Clear previous analysis when new file is uploaded
                st.session_state.pop("analysis_results", None)

        doc = st.session_state.parsed_doc

        # Show document info
        col1, col2, col3 = st.columns(3)
        col1.metric("Pages", doc.page_count)
        col2.metric("Characters", f"{doc.char_count:,}")
        col3.metric("Est. Tokens", f"{doc.estimated_tokens:,}")

        with st.expander("Preview extracted text", expanded=False):
            st.text(doc.raw_text[:2000] + ("..." if len(doc.raw_text) > 2000 else ""))

        return True
    return False
