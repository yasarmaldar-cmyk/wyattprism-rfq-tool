import streamlit as st
import yaml
from pathlib import Path

PROFILE_PATH = Path(__file__).parent.parent / "config" / "company_profile.yaml"


def load_profile() -> dict:
    if PROFILE_PATH.exists():
        return yaml.safe_load(PROFILE_PATH.read_text())
    return {}


def save_profile(profile: dict):
    PROFILE_PATH.write_text(yaml.dump(profile, default_flow_style=False, allow_unicode=True))


def render_profile_editor():
    """Renders profile editor fields inline (meant to be called inside a container)."""
    profile = load_profile()
    company = profile.get("company", {})
    exp = profile.get("experience", {})

    st.caption(f"**{company.get('name', 'Not configured')}** | Est. {company.get('established', 'N/A')}")

    with st.form("profile_form"):
        new_name = st.text_input("Company Name", value=company.get("name", ""))
        new_type = st.selectbox(
            "Company Type",
            ["LLP", "Pvt Ltd", "Partnership", "Proprietorship"],
            index=["LLP", "Pvt Ltd", "Partnership", "Proprietorship"].index(
                company.get("type", "LLP")
            )
            if company.get("type", "LLP") in ["LLP", "Pvt Ltd", "Partnership", "Proprietorship"]
            else 0,
        )
        new_established = st.number_input(
            "Year Established", value=company.get("established", 2015), min_value=1900, max_value=2026
        )
        new_years = st.number_input(
            "Years in Business", value=exp.get("years_in_business", 0), min_value=0
        )
        new_reports = st.number_input(
            "Total Reports Done", value=exp.get("total_reports", 0), min_value=0
        )

        if st.form_submit_button("Save"):
            profile.setdefault("company", {})["name"] = new_name
            profile["company"]["type"] = new_type
            profile["company"]["established"] = new_established
            profile.setdefault("experience", {})["years_in_business"] = new_years
            profile["experience"]["total_reports"] = new_reports
            save_profile(profile)
            st.success("Saved!")

    return profile
