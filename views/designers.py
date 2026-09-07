"""
Designers — data entry, edit, delete for the designers table.
"""

import streamlit as st
import pandas as pd
import time
from db import (
    require_login, get_supabase, is_junior, can_edit, can_delete,
    confirm_delete, fetch_teams, fetch_members, member_name_map, team_name_map,
    BRANDS, DESIGN_STATUS,
    safe_index, safe_int, parse_date,
)

user = require_login()
sb = get_supabase()


@st.dialog("Design Request")
def designer_form(record=None):
    editing = record is not None
    st.subheader("Edit Design" if editing else "New Design Request")

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
        member_id = st.selectbox("Designer *", options=mem_ids,
            index=mem_ids.index(record["member_id"]) if editing and record.get("member_id") in mem_ids else 0,
            format_func=lambda x: mem_opts[x], key="dsg_mem")
    with c2:
        team_id = st.selectbox("Team *", options=team_ids,
            index=team_ids.index(record["team_id"]) if editing and record.get("team_id") in team_ids else 0,
            format_func=lambda x: team_opts[x], key="dsg_team")

    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", options=BRANDS,
            index=safe_index(BRANDS, record.get("brand")) if editing else 0, key="dsg_brand")
    with c2:
        month = st.date_input("Month",
            value=parse_date(record.get("month")) if editing else None, key="dsg_month")

    c1, c2 = st.columns(2)
    with c1:
        design_name = st.text_input("Design Name",
            value=record.get("design_name", "") if editing else "", key="dsg_name")
    with c2:
        design_category = st.text_input("Design Category",
            value=record.get("design_category", "") if editing else "", key="dsg_cat")

    c1, c2 = st.columns(2)
    with c1:
        request_date = st.date_input("Request Date",
            value=parse_date(record.get("request_date")) if editing else None, key="dsg_rdate")
    with c2:
        delivery_date = st.date_input("Delivery Date",
            value=parse_date(record.get("delivery_date")) if editing else None, key="dsg_ddate")

    c1, c2, c3 = st.columns(3)
    with c1:
        status = st.selectbox("Status", options=DESIGN_STATUS,
            index=safe_index(DESIGN_STATUS, record.get("status")) if editing else 0, key="dsg_status")
    with c2:
        revision_count = st.number_input("Revision Count", min_value=0,
            value=safe_int(record.get("revision_count")) if editing else 0, key="dsg_rc")
    with c3:
        related_project = st.text_input("Related Project",
            value=record.get("related_project", "") if editing else "", key="dsg_proj")

    design_url = st.text_input("Design URL",
        value=record.get("design_url", "") if editing else "", key="dsg_url")
    notes = st.text_area("Notes", value=record.get("notes", "") if editing else "", key="dsg_notes")

    if st.button("💾 Save", type="primary", use_container_width=True):
        data = {
            "member_id": member_id, "team_id": team_id, "brand": brand,
            "month": str(month) if month else None,
            "design_name": design_name, "design_category": design_category,
            "request_date": str(request_date) if request_date else None,
            "delivery_date": str(delivery_date) if delivery_date else None,
            "status": status, "revision_count": revision_count,
            "related_project": related_project,
            "notes": notes, "design_url": design_url,
        }
        if editing:
            sb.table("designers").update(data).eq("design_id", record["design_id"]).execute()
            st.success("Design updated!")
        else:
            sb.table("designers").insert(data).execute()
            st.success("Design request added!")
        time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.header("Designers")
with col2:
    search = st.text_input("Search", placeholder="Search designs...", label_visibility="collapsed", key="search_dsg")
with col3:
    if st.button("➕ Add Design", type="primary", use_container_width=True):
        designer_form()

st.markdown("---")

data = sb.table("designers").select("*").order("design_id", desc=True).execute().data or []
m_map = member_name_map()
t_map = team_name_map()

if search:
    data = [r for r in data if search.lower() in str(r.values()).lower()]

if data:
    df = pd.DataFrame(data)
    df["designer"] = df["member_id"].map(m_map).fillna("—")
    df["team"] = df["team_id"].map(t_map).fillna("—")
    display = ["design_name", "design_category", "brand", "status", "designer",
               "request_date", "delivery_date", "revision_count", "related_project"]
    display = [c for c in display if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    if not is_junior():
        st.markdown("---")
        st.markdown("#### Actions")
        opts = {r["design_id"]: f"{r.get('design_name','—')} (#{r['design_id']})" for r in data}
        sel_id = st.selectbox("Select record", options=list(opts.keys()), format_func=lambda x: opts[x], key="sel_dsg")
        sel_rec = next(r for r in data if r["design_id"] == sel_id)
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if can_edit(sel_rec.get("member_id")):
                if st.button("✏️ Edit"):
                    designer_form(sel_rec)
            else:
                st.info("Own records only.")
        with c2:
            if can_delete(sel_rec.get("member_id")):
                if st.button("🗑️ Delete"):
                    confirm_delete("designers", "design_id", sel_rec["design_id"],
                                   sel_rec.get("design_name", "this design"))
else:
    st.info("No design records found.")
