"""
PR — data entry, edit, delete for the pr table.
"""

import streamlit as st
import pandas as pd
import time
from db import (
    require_login, get_supabase, is_junior, can_edit, can_delete,
    confirm_delete, fetch_teams, fetch_members, fetch_campaigns,
    member_name_map, team_name_map,
    BRANDS, PR_STATUS,
    safe_index, safe_float, safe_int, parse_date,
)

user = require_login()
sb = get_supabase()


@st.dialog("PR Record")
def pr_form(record=None):
    editing = record is not None
    st.subheader("Edit PR Record" if editing else "New PR Record")

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
            format_func=lambda x: mem_opts[x], key="pr_mem")
    with c2:
        team_id = st.selectbox("Team *", options=team_ids,
            index=team_ids.index(record["team_id"]) if editing and record.get("team_id") in team_ids else 0,
            format_func=lambda x: team_opts[x], key="pr_team")

    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", options=BRANDS,
            index=safe_index(BRANDS, record.get("brand")) if editing else 0, key="pr_brand")
    with c2:
        campaign_type = st.text_input("Campaign Type",
            value=record.get("campaign_type", "") if editing else "", key="pr_ctype")

    # Link to existing campaign (optional)
    campaigns = fetch_campaigns()
    camp_opts = {0: "— None —"}
    camp_opts.update({c["campaign_id"]: c["campaign_name"] for c in campaigns})
    camp_ids = list(camp_opts.keys())
    default_camp = 0
    if editing and record.get("campaign_id") and record["campaign_id"] in camp_ids:
        default_camp = camp_ids.index(record["campaign_id"])

    campaign_id = st.selectbox("Linked Campaign", options=camp_ids,
        index=default_camp, format_func=lambda x: camp_opts[x], key="pr_camp")

    c1, c2 = st.columns(2)
    with c1:
        send_date = st.date_input("Send Date",
            value=parse_date(record.get("send_date")) if editing else None, key="pr_sdate")
    with c2:
        status = st.selectbox("Status", options=PR_STATUS,
            index=safe_index(PR_STATUS, record.get("status")) if editing else 0, key="pr_status")

    # Metrics
    st.markdown("**Email Metrics**")
    c1, c2, c3 = st.columns(3)
    with c1:
        recipients = st.number_input("Recipients", min_value=0,
            value=safe_int(record.get("recipients")) if editing else 0, key="pr_recip")
    with c2:
        delivered = st.number_input("Delivered", min_value=0,
            value=safe_int(record.get("delivered")) if editing else 0, key="pr_deliv")
    with c3:
        responses = st.number_input("Responses", min_value=0,
            value=safe_int(record.get("responses")) if editing else 0, key="pr_resp")

    c1, c2, c3 = st.columns(3)
    with c1:
        open_rate = st.number_input("Open Rate %", min_value=0.0, max_value=100.0, step=0.1,
            value=safe_float(record.get("open_rate")) if editing else 0.0, key="pr_or")
    with c2:
        click_rate = st.number_input("Click Rate %", min_value=0.0, max_value=100.0, step=0.1,
            value=safe_float(record.get("click_rate")) if editing else 0.0, key="pr_cr")
    with c3:
        leads_gen = st.number_input("Leads Generated", min_value=0,
            value=safe_int(record.get("leads_generated")) if editing else 0, key="pr_leads")

    pr_url = st.text_input("PR URL",
        value=record.get("pr_url", "") if editing else "", key="pr_url")

    if st.button("💾 Save", type="primary", use_container_width=True):
        data = {
            "member_id": member_id, "team_id": team_id, "brand": brand,
            "campaign_id": campaign_id if campaign_id != 0 else None,
            "campaign_type": campaign_type,
            "send_date": str(send_date) if send_date else None,
            "recipients": recipients, "delivered": delivered,
            "open_rate": open_rate, "click_rate": click_rate,
            "responses": responses, "leads_generated": leads_gen,
            "status": status, "pr_url": pr_url,
        }
        if editing:
            sb.table("pr").update(data).eq("pr_id", record["pr_id"]).execute()
            st.success("PR record updated!")
        else:
            sb.table("pr").insert(data).execute()
            st.success("PR record added!")
        time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.header("PR")
with col2:
    search = st.text_input("Search", placeholder="Search PR records...", label_visibility="collapsed", key="search_pr")
with col3:
    if st.button("➕ Add PR Record", type="primary", use_container_width=True):
        pr_form()

st.markdown("---")

data = sb.table("pr").select("*").order("pr_id", desc=True).execute().data or []
m_map = member_name_map()
t_map = team_name_map()

if search:
    data = [r for r in data if search.lower() in str(r.values()).lower()]

if data:
    df = pd.DataFrame(data)
    df["member"] = df["member_id"].map(m_map).fillna("—")
    df["team"] = df["team_id"].map(t_map).fillna("—")
    display = ["brand", "campaign_type", "send_date", "recipients", "delivered",
               "open_rate", "click_rate", "responses", "leads_generated", "status", "member"]
    display = [c for c in display if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    if not is_junior():
        st.markdown("---")
        st.markdown("#### Actions")
        opts = {r["pr_id"]: f"{r.get('brand','—')} — {r.get('campaign_type','')} (#{r['pr_id']})" for r in data}
        sel_id = st.selectbox("Select record", options=list(opts.keys()), format_func=lambda x: opts[x], key="sel_pr")
        sel_rec = next(r for r in data if r["pr_id"] == sel_id)
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if can_edit(sel_rec.get("member_id")):
                if st.button("✏️ Edit"):
                    pr_form(sel_rec)
            else:
                st.info("Own records only.")
        with c2:
            if can_delete(sel_rec.get("member_id")):
                if st.button("🗑️ Delete"):
                    confirm_delete("pr", "pr_id", sel_rec["pr_id"],
                                   f"PR #{sel_rec['pr_id']}")
else:
    st.info("No PR records found.")
