"""
SEO — monthly SEO metrics data entry, edit, delete.
"""

import streamlit as st
import pandas as pd
import time
from db import (
    require_login, get_supabase, is_junior, can_edit, can_delete,
    confirm_delete, fetch_teams, fetch_members, member_name_map, team_name_map,
    BRANDS, TECHNICAL_AUDIT_OPTIONS,
    safe_index, safe_int, parse_date,
)

user = require_login()
sb = get_supabase()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FORM DIALOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.dialog("SEO Record")
def seo_form(record=None):
    editing = record is not None
    st.subheader("Edit SEO Record" if editing else "New SEO Record")

    teams = fetch_teams()
    team_opts = {t["team_id"]: t["team_name"] for t in teams}
    team_ids = list(team_opts.keys())
    members_all = fetch_members(active_only=True)
    mem_opts = {m["member_id"]: m["full_name"] for m in members_all}
    mem_ids = list(mem_opts.keys())
    if not team_ids or not mem_ids:
        st.warning("Please create teams and members first.")
        return

    # Row 1: member, team, brand, month
    c1, c2 = st.columns(2)
    with c1:
        member_id = st.selectbox("Member *", options=mem_ids,
            index=mem_ids.index(record["member_id"]) if editing and record.get("member_id") in mem_ids else 0,
            format_func=lambda x: mem_opts[x], key="sf_mem")
    with c2:
        team_id = st.selectbox("Team *", options=team_ids,
            index=team_ids.index(record["team_id"]) if editing and record.get("team_id") in team_ids else 0,
            format_func=lambda x: team_opts[x], key="sf_team")

    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", options=BRANDS,
            index=safe_index(BRANDS, record.get("brand")) if editing else 0, key="sf_brand")
    with c2:
        month = st.date_input("Month",
            value=parse_date(record.get("month")) if editing else None, key="sf_month")

    # Content metrics
    st.markdown("**Content Metrics**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        outlines_created = st.number_input("Outlines Created", min_value=0,
            value=safe_int(record.get("outlines_created")) if editing else 0, key="sf_oc")
    with c2:
        outlines_approved = st.number_input("Outlines Approved", min_value=0,
            value=safe_int(record.get("outlines_approved")) if editing else 0, key="sf_oa")
    with c3:
        pages_published = st.number_input("Pages Published", min_value=0,
            value=safe_int(record.get("pages_published")) if editing else 0, key="sf_pp")
    with c4:
        blogs_published = st.number_input("Blogs Published", min_value=0,
            value=safe_int(record.get("blogs_published")) if editing else 0, key="sf_bp")

    # Traffic & Leads
    st.markdown("**Traffic & Leads**")
    c1, c2 = st.columns(2)
    with c1:
        organic_leads = st.number_input("Organic Leads", min_value=0,
            value=safe_int(record.get("organic_leads")) if editing else 0, key="sf_ol")
    with c2:
        organic_traffic = st.number_input("Organic Traffic", min_value=0,
            value=safe_int(record.get("organic_traffic")) if editing else 0, key="sf_ot")

    # Keywords
    st.markdown("**Keywords**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        keywords_tracked = st.number_input("Tracked", min_value=0,
            value=safe_int(record.get("keywords_tracked")) if editing else 0, key="sf_kt")
    with c2:
        keywords_improved = st.number_input("Improved", min_value=0,
            value=safe_int(record.get("keywords_improved")) if editing else 0, key="sf_ki")
    with c3:
        keywords_top10 = st.number_input("Top 10", min_value=0,
            value=safe_int(record.get("keywords_in_top_10")) if editing else 0, key="sf_k10")
    with c4:
        keywords_top3 = st.number_input("Top 3", min_value=0,
            value=safe_int(record.get("keywords_in_top_3")) if editing else 0, key="sf_k3")

    # Technical
    st.markdown("**Technical**")
    c1, c2, c3 = st.columns(3)
    with c1:
        tech_audit = st.selectbox("Technical Audit", options=TECHNICAL_AUDIT_OPTIONS,
            index=safe_index(TECHNICAL_AUDIT_OPTIONS, record.get("technical_audit")) if editing else 0, key="sf_ta")
    with c2:
        issues_found = st.number_input("Issues Found", min_value=0,
            value=safe_int(record.get("technical_issues_found")) if editing else 0, key="sf_if")
    with c3:
        issues_fixed = st.number_input("Issues Fixed", min_value=0,
            value=safe_int(record.get("technical_issues_fixed")) if editing else 0, key="sf_ix")

    # Backlinks & Recommendations
    c1, c2, c3 = st.columns(3)
    with c1:
        backlinks = st.number_input("Backlinks Built", min_value=0,
            value=safe_int(record.get("backlinks_built")) if editing else 0, key="sf_bl")
    with c2:
        seo_recs = st.number_input("SEO Recommendations", min_value=0,
            value=safe_int(record.get("seo_recommendations")) if editing else 0, key="sf_sr")
    with c3:
        recs_impl = st.number_input("Implemented", min_value=0,
            value=safe_int(record.get("recommendations_implemented")) if editing else 0, key="sf_ri")

    notes = st.text_area("Notes", value=record.get("notes", "") if editing else "", key="sf_notes")

    if st.button("💾 Save", type="primary", use_container_width=True):
        data = {
            "member_id": member_id, "team_id": team_id, "brand": brand,
            "month": str(month) if month else None,
            "outlines_created": outlines_created, "outlines_approved": outlines_approved,
            "pages_published": pages_published, "blogs_published": blogs_published,
            "organic_leads": organic_leads, "organic_traffic": organic_traffic,
            "keywords_tracked": keywords_tracked, "keywords_improved": keywords_improved,
            "keywords_in_top_10": keywords_top10, "keywords_in_top_3": keywords_top3,
            "technical_audit": tech_audit,
            "technical_issues_found": issues_found, "technical_issues_fixed": issues_fixed,
            "backlinks_built": backlinks, "seo_recommendations": seo_recs,
            "recommendations_implemented": recs_impl, "notes": notes,
        }
        if editing:
            sb.table("seo").update(data).eq("seo_id", record["seo_id"]).execute()
            st.success("SEO record updated!")
        else:
            sb.table("seo").insert(data).execute()
            st.success("SEO record added!")
        time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.header("SEO")
with col2:
    search = st.text_input("Search", placeholder="Search SEO records...", label_visibility="collapsed", key="search_seo")
with col3:
    if st.button("➕ Add SEO Record", type="primary", use_container_width=True):
        seo_form()

st.markdown("---")

data = sb.table("seo").select("*").order("seo_id", desc=True).execute().data or []
m_map = member_name_map()
t_map = team_name_map()

if search:
    data = [r for r in data if search.lower() in str(r.values()).lower()]

if data:
    df = pd.DataFrame(data)
    df["member"] = df["member_id"].map(m_map).fillna("—")
    df["team"] = df["team_id"].map(t_map).fillna("—")
    display = ["brand", "month", "member", "team", "organic_traffic", "organic_leads",
               "keywords_tracked", "keywords_in_top_10", "keywords_in_top_3",
               "pages_published", "blogs_published", "backlinks_built", "technical_audit"]
    display = [c for c in display if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    if not is_junior():
        st.markdown("---")
        st.markdown("#### Actions")
        opts = {r["seo_id"]: f"{r.get('brand','—')} — {str(r.get('month',''))[:7]} (#{r['seo_id']})" for r in data}
        sel_id = st.selectbox("Select record", options=list(opts.keys()), format_func=lambda x: opts[x], key="sel_seo")
        sel_rec = next(r for r in data if r["seo_id"] == sel_id)
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if can_edit(sel_rec.get("member_id")):
                if st.button("✏️ Edit"):
                    seo_form(sel_rec)
            else:
                st.info("Own records only.")
        with c2:
            if can_delete(sel_rec.get("member_id")):
                if st.button("🗑️ Delete"):
                    confirm_delete("seo", "seo_id", sel_rec["seo_id"],
                                   f"SEO {sel_rec.get('brand','')} {str(sel_rec.get('month',''))[:7]}")
else:
    st.info("No SEO records found. Click **Add SEO Record** to create one.")
