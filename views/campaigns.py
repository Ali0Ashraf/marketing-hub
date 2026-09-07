"""
Campaigns — data entry, edit, delete for the campaigns table.
"""

import streamlit as st
import pandas as pd
import time
from db import (
    require_login, get_supabase, is_junior, can_edit, can_delete,
    confirm_delete, fetch_teams, fetch_members, member_name_map, team_name_map,
    BRANDS, PLATFORMS_ADS, CAMPAIGN_OBJECTIVES, CAMPAIGN_STATUS,
    safe_index, safe_float, safe_int, parse_date,
)

user = require_login()
sb = get_supabase()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FORM DIALOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.dialog("Campaign")
def campaign_form(record=None):
    editing = record is not None
    st.subheader("Edit Campaign" if editing else "New Campaign")

    # Lookups
    teams = fetch_teams()
    team_opts = {t["team_id"]: t["team_name"] for t in teams}
    team_ids = list(team_opts.keys())
    members_all = fetch_members(active_only=True)
    mem_opts = {m["member_id"]: m["full_name"] for m in members_all}
    mem_ids = list(mem_opts.keys())

    if not team_ids or not mem_ids:
        st.warning("Please create teams and members first.")
        return

    # Row 1: member, team, brand
    c1, c2, c3 = st.columns(3)
    with c1:
        member_id = st.selectbox("Member *", options=mem_ids,
            index=mem_ids.index(record["member_id"]) if editing and record.get("member_id") in mem_ids else 0,
            format_func=lambda x: mem_opts[x], key="cf_member")
    with c2:
        team_id = st.selectbox("Team *", options=team_ids,
            index=team_ids.index(record["team_id"]) if editing and record.get("team_id") in team_ids else 0,
            format_func=lambda x: team_opts[x], key="cf_team")
    with c3:
        brand = st.selectbox("Brand", options=BRANDS,
            index=safe_index(BRANDS, record.get("brand")) if editing else 0, key="cf_brand")

    # Row 2: name, platform, objectives, type
    c1, c2 = st.columns(2)
    with c1:
        campaign_name = st.text_input("Campaign Name *",
            value=record.get("campaign_name", "") if editing else "", key="cf_name")
    with c2:
        platform = st.selectbox("Platform", options=PLATFORMS_ADS,
            index=safe_index(PLATFORMS_ADS, record.get("platform")) if editing else 0, key="cf_plat")

    c1, c2 = st.columns(2)
    with c1:
        objectives = st.selectbox("Objectives", options=CAMPAIGN_OBJECTIVES,
            index=safe_index(CAMPAIGN_OBJECTIVES, record.get("campaign_objectives")) if editing else 0, key="cf_obj")
    with c2:
        campaign_type = st.text_input("Campaign Type",
            value=record.get("campaign_type", "") if editing else "", key="cf_type")

    # Row 3: target country, dates, status
    c1, c2, c3 = st.columns(3)
    with c1:
        target_country = st.text_input("Target Country",
            value=record.get("target_country", "") if editing else "", key="cf_country")
    with c2:
        start_date = st.date_input("Start Date",
            value=parse_date(record.get("start_date")) if editing else None, key="cf_start")
    with c3:
        end_date = st.date_input("End Date",
            value=parse_date(record.get("end_date")) if editing else None, key="cf_end")

    status = st.selectbox("Status", options=CAMPAIGN_STATUS,
        index=safe_index(CAMPAIGN_STATUS, record.get("status")) if editing else 0, key="cf_status")

    # Row 4: budget & metrics
    st.markdown("**Budget & Metrics**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        budget_planned = st.number_input("Budget Planned", min_value=0.0, step=100.0,
            value=safe_float(record.get("budget_planned")) if editing else 0.0, key="cf_bp")
    with c2:
        budget_spent = st.number_input("Budget Spent", min_value=0.0, step=100.0,
            value=safe_float(record.get("budget_spent")) if editing else 0.0, key="cf_bs")
    with c3:
        impressions = st.number_input("Impressions", min_value=0, step=100,
            value=safe_int(record.get("impressions")) if editing else 0, key="cf_imp")
    with c4:
        clicks = st.number_input("Clicks", min_value=0, step=10,
            value=safe_int(record.get("clicks")) if editing else 0, key="cf_clicks")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ctr = st.number_input("CTR %", min_value=0.0, step=0.1,
            value=safe_float(record.get("ctr")) if editing else 0.0, key="cf_ctr")
    with c2:
        leads = st.number_input("Leads", min_value=0, step=1,
            value=safe_int(record.get("leads")) if editing else 0, key="cf_leads")
    with c3:
        cost_per_result = st.number_input("Cost / Result", min_value=0.0, step=1.0,
            value=safe_float(record.get("cost_per_result")) if editing else 0.0, key="cf_cpr")
    with c4:
        conversion_rate = st.number_input("Conv Rate %", min_value=0.0, step=0.1,
            value=safe_float(record.get("conversion_rate")) if editing else 0.0, key="cf_cr")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        qualified_leads = st.number_input("Qualified Leads", min_value=0,
            value=safe_int(record.get("qualified_leads")) if editing else 0, key="cf_ql")
    with c2:
        opportunities = st.number_input("Opportunities", min_value=0,
            value=safe_int(record.get("opportunities")) if editing else 0, key="cf_opp")
    with c3:
        revenue = st.number_input("Revenue", min_value=0.0, step=100.0,
            value=safe_float(record.get("revenue")) if editing else 0.0, key="cf_rev")
    with c4:
        roas = st.number_input("ROAS", min_value=0.0, step=0.1,
            value=safe_float(record.get("roas")) if editing else 0.0, key="cf_roas")

    notes = st.text_area("Notes", value=record.get("notes", "") if editing else "", key="cf_notes")

    if st.button("💾 Save", type="primary", use_container_width=True):
        if not campaign_name:
            st.error("Campaign name is required.")
            return
        data = {
            "member_id": member_id, "team_id": team_id, "brand": brand,
            "platform": platform, "campaign_name": campaign_name,
            "campaign_objectives": objectives, "campaign_type": campaign_type,
            "target_country": target_country,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "status": status, "budget_planned": budget_planned,
            "budget_spent": budget_spent, "impressions": impressions,
            "clicks": clicks, "ctr": ctr, "leads": leads,
            "cost_per_result": cost_per_result, "conversion_rate": conversion_rate,
            "qualified_leads": qualified_leads, "opportunities": opportunities,
            "revenue": revenue, "roas": roas, "notes": notes,
        }
        if editing:
            sb.table("campaigns").update(data).eq("campaign_id", record["campaign_id"]).execute()
            st.success("Campaign updated!")
        else:
            sb.table("campaigns").insert(data).execute()
            st.success("Campaign added!")
        time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.header("Campaigns")
with col2:
    search = st.text_input("Search", placeholder="Search campaigns...", label_visibility="collapsed", key="search_camp")
with col3:
    if st.button("➕ Add Campaign", type="primary", use_container_width=True):
        campaign_form()

st.markdown("---")

# ── Data table ────────────────────────────────────────────────────
data = sb.table("campaigns").select("*").order("created_at", desc=True).execute().data or []
m_map = member_name_map()
t_map = team_name_map()

if search:
    data = [r for r in data if search.lower() in str(r.values()).lower()]

if data:
    df = pd.DataFrame(data)
    df["member"] = df["member_id"].map(m_map).fillna("—")
    df["team"] = df["team_id"].map(t_map).fillna("—")
    display = ["campaign_name", "brand", "platform", "status", "start_date", "end_date",
               "budget_planned", "budget_spent", "impressions", "clicks", "ctr", "roas", "member", "team"]
    display = [c for c in display if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    # Edit / Delete
    if not is_junior():
        st.markdown("---")
        st.markdown("#### Actions")
        opts = {r["campaign_id"]: f"{r['campaign_name']} (#{r['campaign_id']})" for r in data}
        sel_id = st.selectbox("Select campaign", options=list(opts.keys()), format_func=lambda x: opts[x], key="sel_camp")
        sel_rec = next(r for r in data if r["campaign_id"] == sel_id)

        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if can_edit(sel_rec.get("member_id")):
                if st.button("✏️ Edit Campaign"):
                    campaign_form(sel_rec)
            else:
                st.info("You can only edit your own records.")
        with c2:
            if can_delete(sel_rec.get("member_id")):
                if st.button("🗑️ Delete Campaign"):
                    confirm_delete("campaigns", "campaign_id", sel_rec["campaign_id"], sel_rec["campaign_name"])
else:
    st.info("No campaigns found. Click **Add Campaign** to create one.")
