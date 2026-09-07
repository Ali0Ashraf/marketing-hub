"""
Social Media — data entry, edit, delete for the social_media table.
"""

import streamlit as st
import pandas as pd
import time
from db import (
    require_login, get_supabase, is_junior, can_edit, can_delete,
    confirm_delete, fetch_teams, fetch_members, member_name_map, team_name_map,
    BRANDS, SOCIAL_PLATFORMS, SOCIAL_CONTENT_TYPES, SOCIAL_POST_STATUS,
    CAPTION_STATUS, DESIGN_STATUS_SM,
    safe_index, parse_date,
)

user = require_login()
sb = get_supabase()


@st.dialog("Social Media Post")
def social_form(record=None):
    editing = record is not None
    st.subheader("Edit Post" if editing else "New Post")

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
            format_func=lambda x: mem_opts[x], key="sm_mem")
    with c2:
        team_id = st.selectbox("Team *", options=team_ids,
            index=team_ids.index(record["team_id"]) if editing and record.get("team_id") in team_ids else 0,
            format_func=lambda x: team_opts[x], key="sm_team")

    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", options=BRANDS,
            index=safe_index(BRANDS, record.get("brand")) if editing else 0, key="sm_brand")
    with c2:
        month = st.date_input("Month",
            value=parse_date(record.get("month")) if editing else None, key="sm_month")

    c1, c2 = st.columns(2)
    with c1:
        platform = st.selectbox("Platform", options=SOCIAL_PLATFORMS,
            index=safe_index(SOCIAL_PLATFORMS, record.get("platform")) if editing else 0, key="sm_plat")
    with c2:
        content_type = st.selectbox("Content Type", options=SOCIAL_CONTENT_TYPES,
            index=safe_index(SOCIAL_CONTENT_TYPES, record.get("content_type")) if editing else 0, key="sm_ctype")

    content_topic = st.text_input("Content Topic",
        value=record.get("content_topic", "") if editing else "", key="sm_topic")

    c1, c2 = st.columns(2)
    with c1:
        planned_date = st.date_input("Planned Date",
            value=parse_date(record.get("planned_date")) if editing else None, key="sm_pdate")
    with c2:
        actual_date = st.date_input("Actual Published Date",
            value=parse_date(record.get("actual_published_date")) if editing else None, key="sm_adate")

    c1, c2, c3 = st.columns(3)
    with c1:
        status = st.selectbox("Status", options=SOCIAL_POST_STATUS,
            index=safe_index(SOCIAL_POST_STATUS, record.get("status")) if editing else 0, key="sm_status")
    with c2:
        caption_st = st.selectbox("Caption Status", options=CAPTION_STATUS,
            index=safe_index(CAPTION_STATUS, record.get("caption_status")) if editing else 0, key="sm_cap")
    with c3:
        design_st = st.selectbox("Design Status", options=DESIGN_STATUS_SM,
            index=safe_index(DESIGN_STATUS_SM, record.get("design_status")) if editing else 0, key="sm_des")

    social_url = st.text_input("Social URL",
        value=record.get("social_url", "") if editing else "", key="sm_url")
    notes = st.text_area("Notes", value=record.get("notes", "") if editing else "", key="sm_notes")

    if st.button("💾 Save", type="primary", use_container_width=True):
        data = {
            "member_id": member_id, "team_id": team_id, "brand": brand,
            "month": str(month) if month else None,
            "platform": platform, "content_type": content_type,
            "content_topic": content_topic,
            "planned_date": str(planned_date) if planned_date else None,
            "actual_published_date": str(actual_date) if actual_date else None,
            "status": status, "caption_status": caption_st,
            "design_status": design_st,
            "notes": notes, "social_url": social_url,
        }
        if editing:
            sb.table("social_media").update(data).eq("social_id", record["social_id"]).execute()
            st.success("Post updated!")
        else:
            sb.table("social_media").insert(data).execute()
            st.success("Post added!")
        time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.header("Social Media")
with col2:
    search = st.text_input("Search", placeholder="Search posts...", label_visibility="collapsed", key="search_sm")
with col3:
    if st.button("➕ Add Post", type="primary", use_container_width=True):
        social_form()

st.markdown("---")

data = sb.table("social_media").select("*").order("social_id", desc=True).execute().data or []
m_map = member_name_map()
t_map = team_name_map()

if search:
    data = [r for r in data if search.lower() in str(r.values()).lower()]

if data:
    df = pd.DataFrame(data)
    df["member"] = df["member_id"].map(m_map).fillna("—")
    df["team"] = df["team_id"].map(t_map).fillna("—")
    display = ["brand", "platform", "content_type", "content_topic", "status",
               "caption_status", "design_status", "planned_date", "actual_published_date", "member"]
    display = [c for c in display if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    if not is_junior():
        st.markdown("---")
        st.markdown("#### Actions")
        opts = {r["social_id"]: f"{r.get('content_topic','—')} — {r.get('platform','')} (#{r['social_id']})" for r in data}
        sel_id = st.selectbox("Select record", options=list(opts.keys()), format_func=lambda x: opts[x], key="sel_sm")
        sel_rec = next(r for r in data if r["social_id"] == sel_id)
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if can_edit(sel_rec.get("member_id")):
                if st.button("✏️ Edit"):
                    social_form(sel_rec)
            else:
                st.info("Own records only.")
        with c2:
            if can_delete(sel_rec.get("member_id")):
                if st.button("🗑️ Delete"):
                    confirm_delete("social_media", "social_id", sel_rec["social_id"],
                                   sel_rec.get("content_topic", "this post"))
else:
    st.info("No social media records found.")
