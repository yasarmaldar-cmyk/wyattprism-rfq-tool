import json
import os
import urllib.error
import urllib.request
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta

HISTORY_DIR = Path(__file__).parent.parent / "history"
HISTORY_DIR.mkdir(exist_ok=True)

# Status constants
STATUS_DRAFT = "draft"
STATUS_SENT = "sent"
STATUS_FOLLOW_UP = "follow_up_due"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_LOST = "lost"

STATUS_LABELS = {
    STATUS_DRAFT: "Draft",
    STATUS_SENT: "Sent",
    STATUS_FOLLOW_UP: "Follow-up Due",
    STATUS_APPROVED: "Approved / Won",
    STATUS_REJECTED: "Rejected",
    STATUS_LOST: "Lost",
}

STATUS_COLORS = {
    STATUS_DRAFT: "gray",
    STATUS_SENT: "blue",
    STATUS_FOLLOW_UP: "orange",
    STATUS_APPROVED: "green",
    STATUS_REJECTED: "red",
    STATUS_LOST: "red",
}

FOLLOW_UP_DAYS = 8


def _generate_id(filename: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in filename)
    safe_name = safe_name.strip().replace(" ", "_")[:50]
    return f"{ts}_{safe_name}"


def save_analysis(filename: str, results: dict, doc_meta: dict) -> str:
    """Save analysis results to a JSON file. Returns the file path."""
    record = {
        "id": _generate_id(filename),
        "filename": filename,
        "saved_at": datetime.now().isoformat(),
        "doc_meta": {
            "page_count": doc_meta.get("page_count", 0),
            "char_count": doc_meta.get("char_count", 0),
            "file_type": doc_meta.get("file_type", ""),
        },
        "results": results,
        # Status tracking
        "status": STATUS_DRAFT,
        "sent_date": None,
        "approval_date": None,
        "revised_cost": None,
        "scope_changes": None,
        "rejection_reason": None,
        "status_history": [
            {"status": STATUS_DRAFT, "date": datetime.now().isoformat(), "notes": "Proposal generated"}
        ],
    }

    summary = results.get("summary", {})
    org = summary.get("issuing_organization", {})
    record["org_name"] = org.get("name", "Unknown")
    record["report_type"] = summary.get("report_type", "Unknown")

    # Wyattprism Platform link — if this analysis was started from the shell,
    # the project id/code are kept on the record AND we POST the result back
    # to the shell so it shows up immediately as a Proposal artifact.
    wp_project_id = st.session_state.get("wp_project_id")
    if wp_project_id:
        record["wp_project_id"] = wp_project_id
        record["wp_project_code"] = st.session_state.get("wp_project_code")

    filepath = HISTORY_DIR / f"{record['id']}.json"
    filepath.write_text(json.dumps(record, indent=2, default=str))

    # Remember which record represents the current session so later updates
    # (e.g. generating the proposal in Upload mode) can find and update it.
    st.session_state["current_record_id"] = record["id"]

    if wp_project_id:
        _notify_shell(record)

    return str(filepath)


def update_analysis_results(record_id: str | None, new_results: dict) -> None:
    """Re-notify the Wyattprism shell with updated proposal content.

    Streamlit Cloud's filesystem is ephemeral — the previously-saved history
    file may not be there any more — so the local file update is fully
    best-effort and the callback is built directly from session_state.
    """
    print(f"[wyattprism-update] called record_id={record_id} has_proposal_in_new_results={bool(new_results.get('proposal'))}")

    wp_project_id = st.session_state.get("wp_project_id")
    if not wp_project_id:
        st.warning(
            "No Wyattprism project linked to this session. Open the RFQ tool "
            "again from the project page in the platform."
        )
        print("[wyattprism-update] SKIP — no wp_project_id in session_state")
        return

    # Best-effort: update the local history file if it still exists. Wrapped
    # so a write failure on the ephemeral FS can't block the callback.
    org_name = "Unknown"
    report_type = "Unknown"
    filename = st.session_state.get("uploaded_filename", "document")

    try:
        if record_id:
            for f in HISTORY_DIR.glob("*.json"):
                try:
                    data = json.loads(f.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                if data.get("id") != record_id:
                    continue
                try:
                    data["results"] = new_results
                    summary_l = new_results.get("summary", {}) or {}
                    org_l = summary_l.get("issuing_organization", {}) or {}
                    if org_l.get("name"):
                        data["org_name"] = org_l["name"]
                    if summary_l.get("report_type"):
                        data["report_type"] = summary_l["report_type"]
                    f.write_text(json.dumps(data, indent=2, default=str))
                except OSError as e:
                    print(f"[wyattprism-update] local file write failed (ignored): {e}")
                org_name = data.get("org_name", org_name)
                report_type = data.get("report_type", report_type)
                filename = data.get("filename", filename)
                break
    except OSError as e:
        print(f"[wyattprism-update] local file scan failed (ignored): {e}")

    # Build a synthetic record from session_state + the new results and POST
    # to the shell directly. This works even if the local file was lost.
    summary = new_results.get("summary", {}) or {}
    org = summary.get("issuing_organization", {}) or {}
    record = {
        "id": record_id or _generate_id(filename),
        "filename": filename,
        "saved_at": datetime.now().isoformat(),
        "org_name": org.get("name") or org_name,
        "report_type": summary.get("report_type") or report_type,
        "results": new_results,
        "wp_project_id": wp_project_id,
        "wp_project_code": st.session_state.get("wp_project_code"),
    }
    print(f"[wyattprism-update] about to notify shell, payload has proposal={bool(record['results'].get('proposal'))}")
    _notify_shell(record)


def _get_shell_config():
    """Read shell URL + callback key from Streamlit secrets or env."""
    try:
        secrets = st.secrets  # streamlit.runtime.secrets.Secrets
        url = secrets.get("SHELL_URL")
        key = secrets.get("SHELL_CALLBACK_KEY")
    except Exception:
        url = key = None
    return (
        url or os.environ.get("SHELL_URL"),
        key or os.environ.get("SHELL_CALLBACK_KEY"),
    )


def _notify_shell(record: dict) -> None:
    """POST a saved proposal back to the Wyattprism shell so it can attach
    the result to the project. Best-effort — failures show a warning but do
    not break the local save. Status is shown both via toast (transient) and
    via persistent inline message so users always know what happened."""
    shell_url, callback_key = _get_shell_config()
    if not shell_url or not callback_key:
        # Tell the user explicitly — these env vars must be set in Streamlit
        # Cloud's secrets panel for the integration to work.
        if record.get("wp_project_id"):
            st.warning(
                "Wyattprism integration is missing config (SHELL_URL or "
                "SHELL_CALLBACK_KEY). Proposal saved locally but not synced."
            )
        return

    has_proposal = bool(record.get("results", {}).get("proposal"))
    payload = {
        "wp_project_id": record.get("wp_project_id"),
        "wp_project_code": record.get("wp_project_code"),
        "rfq_record_id": record.get("id"),
        "filename": record.get("filename"),
        "org_name": record.get("org_name"),
        "report_type": record.get("report_type"),
        "saved_at": record.get("saved_at"),
        "proposal": record.get("results", {}).get("proposal"),
        "summary": record.get("results", {}).get("summary"),
        "clarifications": record.get("results", {}).get("clarifications"),
    }

    url = f"{shell_url.rstrip('/')}/api/rfq-callback?key={callback_key}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
        if has_proposal:
            st.success(
                f"✓ Proposal synced to Wyattprism platform "
                f"(project {record.get('wp_project_code', '')})."
            )
        else:
            st.info(
                "Analysis synced to Wyattprism. Proposal text will be sent "
                "once you click *Generate Proposal Draft*."
            )
        # Keep the small toast as well in case they switch tabs
        st.toast("Synced to Wyattprism.", icon="✅")
        # Debug breadcrumb visible in Streamlit Cloud logs
        print(f"[wyattprism-sync] OK status={status} has_proposal={has_proposal} body={body[:200]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        st.error(
            f"Could not sync to Wyattprism (HTTP {e.code}): {body[:300]}"
        )
        print(f"[wyattprism-sync] FAIL HTTPError code={e.code} body={body[:500]}")
    except (urllib.error.URLError, TimeoutError) as e:
        st.error(f"Could not reach Wyattprism platform: {e}")
        print(f"[wyattprism-sync] FAIL URLError {e}")


def update_record(record_id: str, updates: dict):
    """Update fields on a saved record."""
    for f in HISTORY_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("id") == record_id:
                data.update(updates)
                f.write_text(json.dumps(data, indent=2, default=str))
                return True
        except (json.JSONDecodeError, KeyError):
            continue
    return False


def update_status(record_id: str, new_status: str, notes: str = "", **extra):
    """Update status of a record and append to status history."""
    for f in HISTORY_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("id") == record_id:
                data["status"] = new_status
                history = data.get("status_history", [])
                entry = {"status": new_status, "date": datetime.now().isoformat(), "notes": notes}
                history.append(entry)
                data["status_history"] = history

                if new_status == STATUS_SENT and not data.get("sent_date"):
                    data["sent_date"] = datetime.now().isoformat()
                elif new_status == STATUS_APPROVED:
                    data["approval_date"] = datetime.now().isoformat()

                # Apply any extra fields
                for k, v in extra.items():
                    data[k] = v

                f.write_text(json.dumps(data, indent=2, default=str))
                return True
        except (json.JSONDecodeError, KeyError):
            continue
    return False


def list_history() -> list[dict]:
    """List all saved analyses, most recent first."""
    records = []
    now = datetime.now()
    for f in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            status = data.get("status", STATUS_DRAFT)

            # Auto-detect follow-up needed
            sent_date = data.get("sent_date")
            needs_followup = False
            if status == STATUS_SENT and sent_date:
                try:
                    sent_dt = datetime.fromisoformat(sent_date)
                    if (now - sent_dt).days >= FOLLOW_UP_DAYS:
                        needs_followup = True
                except ValueError:
                    pass

            records.append({
                "id": data.get("id", f.stem),
                "filename": data.get("filename", "Unknown"),
                "org_name": data.get("org_name", "Unknown"),
                "report_type": data.get("report_type", "Unknown"),
                "saved_at": data.get("saved_at", ""),
                "status": status,
                "sent_date": sent_date,
                "approval_date": data.get("approval_date"),
                "revised_cost": data.get("revised_cost"),
                "needs_followup": needs_followup,
                "path": str(f),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return records


def load_analysis(filepath: str) -> dict | None:
    try:
        return json.loads(Path(filepath).read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def delete_analysis(filepath: str):
    try:
        Path(filepath).unlink()
    except FileNotFoundError:
        pass


def get_current_record() -> dict | None:
    """Get the currently loaded record (if loaded from history) by matching filename."""
    filename = st.session_state.get("uploaded_filename")
    if not filename:
        return None
    for f in HISTORY_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("filename") == filename:
                return data
        except (json.JSONDecodeError, KeyError):
            continue
    return None


def render_history_sidebar():
    """Render history list in the sidebar with status indicators."""
    records = list_history()
    if not records:
        return

    st.sidebar.divider()

    # Show follow-ups due banner
    followups = [r for r in records if r["needs_followup"]]
    if followups:
        st.sidebar.error(f"⚠ {len(followups)} proposal{'s' if len(followups) > 1 else ''} need follow-up")

    st.sidebar.subheader("History")

    status_emoji = {
        STATUS_DRAFT: "📝",
        STATUS_SENT: "📤",
        STATUS_APPROVED: "✅",
        STATUS_REJECTED: "❌",
        STATUS_LOST: "❌",
    }

    for record in records[:20]:
        saved_dt = record.get("saved_at", "")
        if saved_dt:
            try:
                dt = datetime.fromisoformat(saved_dt)
                date_str = dt.strftime("%d %b %Y, %I:%M %p")
            except ValueError:
                date_str = saved_dt[:10]
        else:
            date_str = "Unknown"

        emoji = status_emoji.get(record["status"], "📝")
        followup_tag = " ⚠" if record["needs_followup"] else ""
        label = f"{emoji} {record['org_name'][:22]}{followup_tag}"

        col1, col2 = st.sidebar.columns([5, 1])
        with col1:
            if st.button(
                label,
                key=f"hist_{record['id']}",
                help=f"{record['report_type']}\n{date_str}\nStatus: {STATUS_LABELS.get(record['status'], 'Draft')}",
                use_container_width=True,
            ):
                data = load_analysis(record["path"])
                if data:
                    st.session_state.analysis_results = data["results"]
                    st.session_state.uploaded_filename = data["filename"]
                    st.session_state.history_loaded = True
                    st.session_state.app_mode = "history"
                    st.rerun()
        with col2:
            if st.button(
                "✕",
                key=f"del_{record['id']}",
                help="Delete",
            ):
                delete_analysis(record["path"])
                st.rerun()


def render_status_tracker():
    """Render the status tracker UI for the currently loaded proposal.

    Shown in the Proposal Draft tab after a proposal is generated.
    Handles: Has it been sent? Follow-up reminder. Approval capture."""
    results = st.session_state.get("analysis_results", {})
    if not results.get("proposal"):
        return

    record = get_current_record()
    if not record:
        return

    record_id = record.get("id")
    status = record.get("status", STATUS_DRAFT)
    summary = results.get("summary", {})
    org_name = summary.get("issuing_organization", {}).get("name", "Unknown")

    st.divider()
    st.markdown("### Proposal Status")

    # --- Status display ---
    status_label = STATUS_LABELS.get(status, "Draft")
    if status == STATUS_DRAFT:
        st.info(f"**Status: {status_label}** — Proposal generated but not yet sent.")

        col1, col2, _ = st.columns([1, 1, 3])
        with col1:
            if st.button("Mark as Sent", type="primary", key=f"mark_sent_{record_id}"):
                update_status(record_id, STATUS_SENT, notes=f"Proposal sent to {org_name}")
                st.success(f"Marked as sent. Follow-up reminder in {FOLLOW_UP_DAYS} days.")
                st.rerun()
        with col2:
            if st.button("Skip", key=f"skip_status_{record_id}"):
                st.session_state[f"skip_{record_id}"] = True

    elif status == STATUS_SENT:
        sent_date = record.get("sent_date")
        if sent_date:
            try:
                sent_dt = datetime.fromisoformat(sent_date)
                days_since = (datetime.now() - sent_dt).days
                followup_due = sent_dt + timedelta(days=FOLLOW_UP_DAYS)

                if days_since >= FOLLOW_UP_DAYS:
                    # Follow-up due
                    st.warning(
                        f"**Follow-up Reminder** — Proposal was sent **{days_since} days ago** "
                        f"on {sent_dt.strftime('%d %b %Y')}. Has the client responded?"
                    )

                    with st.form(f"followup_form_{record_id}"):
                        outcome = st.radio(
                            "What's the status?",
                            ["Approved / Won",
                             "Still under discussion",
                             "Revised scope/cost needed",
                             "Rejected",
                             "Lost (no response / went to competitor)"],
                            key=f"outcome_{record_id}",
                        )

                        # Conditional fields
                        revised_cost = ""
                        scope_changes = ""
                        notes = ""

                        if outcome == "Approved / Won":
                            col1, col2 = st.columns(2)
                            with col1:
                                revised_cost = st.text_input(
                                    "Final Cost (if revised)",
                                    placeholder="e.g., Rs. 5.5 lac",
                                    key=f"cost_{record_id}",
                                )
                            with col2:
                                notes = st.text_input("Notes (optional)", key=f"notes_{record_id}")
                            scope_changes = st.text_area(
                                "Scope changes (if any)",
                                placeholder="e.g., Added ESG content writing, removed printing",
                                height=80,
                                key=f"scope_{record_id}",
                            )
                        elif outcome == "Revised scope/cost needed":
                            col1, col2 = st.columns(2)
                            with col1:
                                revised_cost = st.text_input("Revised Cost", key=f"rcost_{record_id}")
                            with col2:
                                notes = st.text_input("Notes", key=f"rnotes_{record_id}")
                            scope_changes = st.text_area(
                                "Scope changes requested",
                                height=80,
                                key=f"rscope_{record_id}",
                            )
                        elif outcome == "Rejected" or outcome == "Lost (no response / went to competitor)":
                            notes = st.text_area(
                                "Reason / Notes",
                                placeholder="e.g., Budget mismatch, competitor selected",
                                height=80,
                                key=f"rejnotes_{record_id}",
                            )
                        else:
                            notes = st.text_area("Notes", key=f"updnotes_{record_id}")

                        if st.form_submit_button("Update Status", type="primary"):
                            if outcome == "Approved / Won":
                                update_status(
                                    record_id, STATUS_APPROVED, notes=notes,
                                    revised_cost=revised_cost, scope_changes=scope_changes,
                                )
                                st.success("Status updated to Approved!")
                            elif outcome == "Still under discussion":
                                # Reset the sent_date so the 8-day clock restarts
                                update_record(record_id, {"sent_date": datetime.now().isoformat()})
                                update_status(record_id, STATUS_SENT, notes=f"Still discussing — {notes}")
                                st.success("Follow-up rescheduled for 8 days from now.")
                            elif outcome == "Revised scope/cost needed":
                                update_status(
                                    record_id, STATUS_SENT, notes=f"Revision requested — {notes}",
                                    revised_cost=revised_cost, scope_changes=scope_changes,
                                )
                                # Reset clock
                                update_record(record_id, {"sent_date": datetime.now().isoformat()})
                                st.success("Updated with revision details. Follow-up reset.")
                            elif outcome == "Rejected":
                                update_status(record_id, STATUS_REJECTED, notes=notes, rejection_reason=notes)
                                st.warning("Marked as rejected.")
                            else:
                                update_status(record_id, STATUS_LOST, notes=notes, rejection_reason=notes)
                                st.warning("Marked as lost.")
                            st.rerun()
                else:
                    # Sent but follow-up not due yet
                    days_left = FOLLOW_UP_DAYS - days_since
                    st.success(
                        f"**Status: Sent** — Sent {days_since} day{'s' if days_since != 1 else ''} ago "
                        f"on {sent_dt.strftime('%d %b %Y')}. Follow-up reminder in **{days_left} day{'s' if days_left != 1 else ''}**."
                    )

                    col1, col2, _ = st.columns([1, 1, 3])
                    with col1:
                        if st.button("Mark Approved", key=f"early_approve_{record_id}"):
                            st.session_state[f"early_approve_{record_id}"] = True
                    with col2:
                        if st.button("Mark Lost", key=f"early_lost_{record_id}"):
                            update_status(record_id, STATUS_LOST, notes="Marked as lost early")
                            st.rerun()

                    if st.session_state.get(f"early_approve_{record_id}"):
                        with st.form(f"early_approve_form_{record_id}"):
                            revised_cost = st.text_input("Final Cost", placeholder="e.g., Rs. 5.5 lac")
                            scope_changes = st.text_area("Scope changes (if any)", height=80)
                            if st.form_submit_button("Confirm Approval", type="primary"):
                                update_status(
                                    record_id, STATUS_APPROVED,
                                    notes="Approved early",
                                    revised_cost=revised_cost,
                                    scope_changes=scope_changes,
                                )
                                st.session_state.pop(f"early_approve_{record_id}", None)
                                st.rerun()
            except ValueError:
                st.warning("Could not parse sent date.")
        else:
            st.info("Status: Sent")

    elif status == STATUS_APPROVED:
        approval_date = record.get("approval_date", "")
        approved_dt_str = approval_date[:10] if approval_date else "Unknown"
        st.success(f"**✅ Approved / Won** — Approved on {approved_dt_str}")

        col1, col2 = st.columns(2)
        if record.get("revised_cost"):
            col1.metric("Final Cost", record["revised_cost"])
        if record.get("scope_changes"):
            with col2:
                st.markdown("**Scope changes:**")
                st.caption(record["scope_changes"])

    elif status in (STATUS_REJECTED, STATUS_LOST):
        label = "Rejected" if status == STATUS_REJECTED else "Lost"
        st.error(f"**{label}**")
        if record.get("rejection_reason"):
            st.caption(f"Reason: {record['rejection_reason']}")

    # Show status history
    history = record.get("status_history", [])
    if len(history) > 1:
        with st.expander("Status History"):
            for entry in reversed(history):
                date = entry.get("date", "")[:10]
                status_lbl = STATUS_LABELS.get(entry.get("status"), entry.get("status", ""))
                notes = entry.get("notes", "")
                st.write(f"**{date}** — {status_lbl}" + (f" — {notes}" if notes else ""))
