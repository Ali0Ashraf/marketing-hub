"""
Content Writing — data entry, edit, delete for the content_writing table.
"""

import streamlit as st
import pandas as pd
import time
from db import (
    require_login, get_supabase, is_junior, can_edit, can_delete,
    confirm_delete, fetch_teams, fetch_members, member_name_map, team_name_map,
    BRANDS, CONTENT_TYPES, CONTENT_STATUS, REVISION_OPTIONS,
    safe_index, safe_int, parse_date,
)

user = require_login()
sb = get_supabase()


@st.dialog("Content Writing")
def content_form(record=None):
    editing = record is not None
    st.subheader("Edit Content" if editing else "New Content")

    teams = fetch_teams()
    team_opts = {t["team_id"]: t["team_name"] for t in teams}
    team_ids = list(team_opts.keys())
    members_all = fetch_members(active_only=True)
    mem_opts = {m["member_id"]: m["full_name"] for m in members_all}
    mem_ids = list(mem_opts.keys())
    if not team_ids or not mem_ids:
        st.warning("Please create teams and members first.")
        return

    c1, c2 = st.columns(2)
    with c1:
        member_id = st.selectbox("Member *", options=mem_ids,
            index=mem_ids.index(record["member_id"]) if editing and record.get("member_id") in mem_ids else 0,
            format_func=lambda x: mem_opts[x], key="cw_mem")
    with c2:
        team_id = st.selectbox("Team *", options=team_ids,
            index=team_ids.index(record["team_id"]) if editing and record.get("team_id") in team_ids else 0,
            format_func=lambda x: team_opts[x], key="cw_team")

    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", options=BRANDS,
            index=safe_index(BRANDS, record.get("brand")) if editing else 0, key="cw_brand")
    with c2:
        month = st.date_input("Month",
            value=parse_date(record.get("month")) if editing else None, key="cw_month")

    c1, c2 = st.columns(2)
    with c1:
        content_type = st.selectbox("Content Type", options=CONTENT_TYPES,
            index=safe_index(CONTENT_TYPES, record.get("content_type")) if editing else 0, key="cw_ctype")
    with c2:
        content_title = st.text_input("Content Title",
            value=record.get("content_title", "") if editing else "", key="cw_title")

    c1, c2 = st.columns(2)
    with c1:
        assigned_date = st.date_input("Assigned Date",
            value=parse_date(record.get("assigned_date")) if editing else None, key="cw_adate")
    with c2:
        submission_date = st.date_input("Submission Date",
            value=parse_date(record.get("submission_date")) if editing else None, key="cw_sdate")

    c1, c2, c3 = st.columns(3)
    with c1:
        status = st.selectbox("Status", options=CONTENT_STATUS,
            index=safe_index(CONTENT_STATUS, record.get("status")) if editing else 0, key="cw_status")
    with c2:
        revision_req = st.selectbox("Revision Required", options=REVISION_OPTIONS,
            index=safe_index(REVISION_OPTIONS, record.get("revision_required")) if editing else 0, key="cw_rev")
    with c3:
        revision_count = st.number_input("Revision Count", min_value=0,
            value=safe_int(record.get("revision_count")) if editing else 0, key="cw_rc")

    c1, c2 = st.columns(2)
    with c1:
        approval_date = st.date_input("Final Approval Date",
            value=parse_date(record.get("final_approval_date")) if editing else None, key="cw_fdate")
    with c2:
        published_date = st.date_input("Published Date",
            value=parse_date(record.get("published_date")) if editing else None, key="cw_pdate")

    c1, c2 = st.columns(2)
    with c1:
        word_count = st.number_input("Word Count", min_value=0,
            value=safe_int(record.get("word_count")) if editing else 0, key="cw_wc")
    with c2:
        content_url = st.text_input("Content URL",
            value=record.get("content_url", "") if editing else "", key="cw_url")

    notes = st.text_area("Notes", value=record.get("notes", "") if editing else "", key="cw_notes")

    if st.button("💾 Save", type="primary", use_container_width=True):
        data = {
            "member_id": member_id, "team_id": team_id, "brand": brand,
            "month": str(month) if month else None,
            "content_type": content_type, "content_title": content_title,
            "assigned_date": str(assigned_date) if assigned_date else None,
            "submission_date": str(submission_date) if submission_date else None,
            "status": status, "revision_required": revision_req,
            "revision_count": revision_count,
            "final_approval_date": str(approval_date) if approval_date else None,
            "published_date": str(published_date) if published_date else None,
            "word_count": word_count, "notes": notes,
            "content_url": content_url,
        }
        if editing:
            sb.table("content_writing").update(data).eq("content_id", record["content_id"]).execute()
            st.success("Content record updated!")
        else:
            sb.table("content_writing").insert(data).execute()
            st.success("Content record added!")
        time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.header("Content Writing")
with col2:
    search = st.text_input("Search", placeholder="Search content...", label_visibility="collapsed", key="search_cw")
with col3:
    if st.button("➕ Add Content", type="primary", use_container_width=True):
        content_form()

st.markdown("---")

data = sb.table("content_writing").select("*").order("content_id", desc=True).execute().data or []
m_map = member_name_map()
t_map = team_name_map()

if search:
    data = [r for r in data if search.lower() in str(r.values()).lower()]

if data:
    df = pd.DataFrame(data)
    df["member"] = df["member_id"].map(m_map).fillna("—")
    df["team"] = df["team_id"].map(t_map).fillna("—")
    display = ["content_title", "content_type", "brand", "status", "member", "team",
               "assigned_date", "submission_date", "published_date", "word_count", "revision_count"]
    display = [c for c in display if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    if not is_junior():
        st.markdown("---")
        st.markdown("#### Actions")
        opts = {r["content_id"]: f"{r.get('content_title','—')} (#{r['content_id']})" for r in data}
        sel_id = st.selectbox("Select record", options=list(opts.keys()), format_func=lambda x: opts[x], key="sel_cw")
        sel_rec = next(r for r in data if r["content_id"] == sel_id)
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if can_edit(sel_rec.get("member_id")):
                if st.button("✏️ Edit"):
                    content_form(sel_rec)
            else:
                st.info("Own records only.")
        with c2:
            if can_delete(sel_rec.get("member_id")):
                if st.button("🗑️ Delete"):
                    confirm_delete("content_writing", "content_id", sel_rec["content_id"],
                                   sel_rec.get("content_title", "this record"))
else:
    st.info("No content records found.")
