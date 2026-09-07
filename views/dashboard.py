"""
Dashboard — simple landing page with 4 KPI metric cards.
"""

import streamlit as st
from db import require_login, get_supabase, safe_float

user = require_login()
sb = get_supabase()

st.header("Dashboard")

# ── KPI Cards ─────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

# Active campaigns
campaigns = sb.table("campaigns").select("campaign_id, status, budget_spent").execute().data or []
active_count = len([c for c in campaigns if c.get("status") == "Active"])
total_budget = sum(safe_float(c.get("budget_spent", 0)) for c in campaigns) if campaigns else 0

# Total leads
leads_resp = sb.table("lead_generation").select("lead_id", count="exact").execute()
lead_count = leads_resp.count if leads_resp.count else 0

# Social posts
social_resp = sb.table("social_media").select("social_id", count="exact").execute()
social_count = social_resp.count if social_resp.count else 0

with c1:
    st.metric("Active Campaigns", active_count)
with c2:
    st.metric("Total Leads", lead_count)
with c3:
    st.metric("Budget Spent", f"${total_budget:,.2f}")
with c4:
    st.metric("Social Posts", social_count)

# ── Recent Activity Feed ──────────────────────────────────────────
st.markdown("---")
st.subheader("Recent Activity Feed")

recent = (
    sb.table("campaigns")
    .select("campaign_name, status, brand, created_at")
    .order("created_at", desc=True)
    .limit(8)
    .execute()
    .data or []
)

if recent:
    for r in recent:
        date_str = str(r.get("created_at", ""))[:10]
        status_icon = {"Active": "🟢", "Paused": "🟡", "Completed": "✅"}.get(r.get("status"), "⚪")
        st.markdown(
            f"{status_icon} **{r['campaign_name']}** — {r.get('brand', '')} "
            f"| {r.get('status', '')} | {date_str}"
        )
else:
    st.info("No recent activity yet. Start by adding campaigns!")
