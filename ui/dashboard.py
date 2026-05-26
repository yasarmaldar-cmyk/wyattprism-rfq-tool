import streamlit as st
from datetime import datetime, timedelta
from ui.history import (
    list_history, load_analysis, update_status, delete_analysis,
    STATUS_DRAFT, STATUS_SENT, STATUS_APPROVED, STATUS_REJECTED, STATUS_LOST,
    STATUS_LABELS, FOLLOW_UP_DAYS,
)


def render_dashboard():
    """Render the proposal pipeline dashboard."""
    st.subheader("Proposal Pipeline Dashboard")

    records = list_history()

    if not records:
        st.info("No proposals yet. Upload an RFQ or use the Manual Form to get started.")
        return

    # === METRICS ===
    total = len(records)
    by_status = {
        STATUS_DRAFT: 0, STATUS_SENT: 0, STATUS_APPROVED: 0,
        STATUS_REJECTED: 0, STATUS_LOST: 0,
    }
    followups = 0
    for r in records:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        if r["needs_followup"]:
            followups += 1

    win_rate = 0
    closed = by_status[STATUS_APPROVED] + by_status[STATUS_REJECTED] + by_status[STATUS_LOST]
    if closed > 0:
        win_rate = (by_status[STATUS_APPROVED] / closed) * 100

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total", total)
    col2.metric("Draft", by_status[STATUS_DRAFT])
    col3.metric("Sent", by_status[STATUS_SENT])
    col4.metric("Won", by_status[STATUS_APPROVED])
    col5.metric("Lost", by_status[STATUS_REJECTED] + by_status[STATUS_LOST])
    col6.metric("Win Rate", f"{win_rate:.0f}%" if closed > 0 else "—")

    # === FOLLOW-UP BANNER ===
    if followups > 0:
        st.divider()
        st.warning(
            f"**{followups} proposal{'s' if followups > 1 else ''} need follow-up** "
            f"— sent more than {FOLLOW_UP_DAYS} days ago without response. Click a row below to update status."
        )

    # === FILTERS ===
    st.divider()
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        filter_status = st.multiselect(
            "Filter by status",
            options=list(STATUS_LABELS.keys()),
            format_func=lambda x: STATUS_LABELS[x],
            default=[],
            placeholder="All statuses",
        )
    with col2:
        filter_search = st.text_input(
            "Search by client name",
            placeholder="e.g., Nayara",
        )
    with col3:
        show_followups_only = st.checkbox("Show only follow-ups due", value=False)

    # Apply filters
    filtered = records
    if filter_status:
        filtered = [r for r in filtered if r["status"] in filter_status]
    if filter_search.strip():
        q = filter_search.strip().lower()
        filtered = [r for r in filtered if q in r["org_name"].lower() or q in r["report_type"].lower()]
    if show_followups_only:
        filtered = [r for r in filtered if r["needs_followup"]]

    st.caption(f"Showing **{len(filtered)}** of {total} proposals")

    if not filtered:
        st.info("No proposals match the current filters.")
        return

    # === PROPOSAL LIST ===
    st.divider()

    for r in filtered:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1.5])

            # Client + report type
            with col1:
                emoji = {
                    STATUS_DRAFT: "📝",
                    STATUS_SENT: "📤",
                    STATUS_APPROVED: "✅",
                    STATUS_REJECTED: "❌",
                    STATUS_LOST: "❌",
                }.get(r["status"], "📝")
                followup_tag = " ⚠" if r["needs_followup"] else ""
                st.markdown(f"**{emoji} {r['org_name']}**{followup_tag}")
                st.caption(r["report_type"])

            # Status
            with col2:
                status_label = STATUS_LABELS.get(r["status"], "Draft")
                if r["needs_followup"]:
                    st.markdown(f":orange[**{status_label}**]")
                    sent_dt = datetime.fromisoformat(r["sent_date"])
                    days = (datetime.now() - sent_dt).days
                    st.caption(f"Sent {days}d ago — Follow-up due")
                else:
                    st.markdown(f"**{status_label}**")
                    if r["status"] == STATUS_SENT and r.get("sent_date"):
                        sent_dt = datetime.fromisoformat(r["sent_date"])
                        days = (datetime.now() - sent_dt).days
                        st.caption(f"Sent {days}d ago")
                    elif r["status"] == STATUS_APPROVED and r.get("approval_date"):
                        st.caption(f"Won {r['approval_date'][:10]}")

            # Dates
            with col3:
                saved = r.get("saved_at", "")
                if saved:
                    try:
                        dt = datetime.fromisoformat(saved)
                        st.caption(f"Created: {dt.strftime('%d %b %Y')}")
                    except ValueError:
                        pass

            # Cost (if won)
            with col4:
                if r.get("revised_cost"):
                    st.markdown(f"💰 **{r['revised_cost']}**")

            # Open button
            with col5:
                if st.button("Open", key=f"open_{r['id']}", use_container_width=True):
                    data = load_analysis(r["path"])
                    if data:
                        st.session_state.analysis_results = data["results"]
                        st.session_state.uploaded_filename = data["filename"]
                        st.session_state.history_loaded = True
                        st.session_state.app_mode = "history"
                        st.rerun()

            st.divider()
