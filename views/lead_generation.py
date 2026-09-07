"""
Lead Generation — data entry, edit, delete for the lead_generation table.
Note: This table has NO member_id. Ownership is via lead_owner (text field).
"""

import streamlit as st
import pandas as pd
import time
from db import (
    require_login, get_supabase, is_junior, is_manager, get_current_user,
    confirm_delete, fetch_campaigns,
    BRANDS, LEAD_SOURCES, LEAD_STATUS_OPTIONS, OPPORTUNITY_OPTIONS,
    safe_index, safe_float, parse_date,
)

user = require_login()
sb = get_supabase()


def _can_edit_lead(record):
    """Manager: all. Senior: own (lead_owner matches). Junior: never."""
    u = get_current_user()
    if not u:
        return False
    if u["role"] == "Manager":
        return True
    if u["role"] == "Senior":
        return (record.get("lead_owner") or "").strip().lower() == u["full_name"].strip().lower()
    return False


@st.dialog("Lead")
def lead_form(record=None):
    editing = record is not None
    st.subheader("Edit Lead" if editing else "New Lead")

    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", options=BRANDS,
            index=safe_index(BRANDS, record.get("brand")) if editing else 0, key="lg_brand")
    with c2:
        lead_source = st.selectbox("Lead Source", options=LEAD_SOURCES,
            index=safe_index(LEAD_SOURCES, record.get("lead_source")) if editing else 0, key="lg_src")

    # Link to campaign (optional)
    campaigns = fetch_campaigns()
    camp_opts = {0: "— None —"}
    camp_opts.update({c["campaign_id"]: c["campaign_name"] for c in campaigns})
    camp_ids = list(camp_opts.keys())
    default_camp = 0
    if editing and record.get("campaign_id") and record["campaign_id"] in camp_ids:
        default_camp = camp_ids.index(record["campaign_id"])

    c1, c2 = st.columns(2)
    with c1:
        campaign_id = st.selectbox("Linked Campaign", options=camp_ids,
            index=default_camp, format_func=lambda x: camp_opts[x], key="lg_camp")
    with c2:
        date_gen = st.date_input("Date Generated",
            value=parse_date(record.get("date_generated")) if editing else None, key="lg_date")

    # Contact details
    st.markdown("**Contact Information**")
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("Company Name",
            value=record.get("company_name", "") if editing else "", key="lg_comp")
    with c2:
        contact = st.text_input("Contact Name",
            value=record.get("contact_name", "") if editing else "", key="lg_contact")

    c1, c2 = st.columns(2)
    with c1:
        job_title = st.text_input("Job Title",
            value=record.get("job_title", "") if editing else "", key="lg_job")
    with c2:
        country = st.text_input("Country",
            value=record.get("country", "") if editing else "", key="lg_country")

    c1, c2 = st.columns(2)
    with c1:
        email = st.text_input("Email",
            value=record.get("email", "") if editing else "", key="lg_email")
    with c2:
        phone = st.text_input("Phone",
            value=record.get("phone", "") if editing else "", key="lg_phone")

    service = st.text_input("Service Interested",
        value=record.get("service_interested", "") if editing else "", key="lg_service")

    # Status & qualification
    st.markdown("**Status & Qualification**")
    c1, c2, c3 = st.columns(3)
    with c1:
        lead_status = st.selectbox("Lead Status", options=LEAD_STATUS_OPTIONS,
            index=safe_index(LEAD_STATUS_OPTIONS, record.get("lead_status")) if editing else 0, key="lg_status")
    with c2:
        lead_owner = st.text_input("Lead Owner",
            value=record.get("lead_owner", user["full_name"]) if editing else user["full_name"], key="lg_owner")
    with c3:
        qual_date = st.date_input("Qualification Date",
            value=parse_date(record.get("qualification_date")) if editing else None, key="lg_qdate")

    c1, c2 = st.columns(2)
    with c1:
        opp_created = st.selectbox("Opportunity Created", options=OPPORTUNITY_OPTIONS,
            index=safe_index(OPPORTUNITY_OPTIONS, record.get("opportunity_created")) if editing else 0, key="lg_opp")
    with c2:
        opp_value = st.number_input("Opportunity Value", min_value=0.0, step=100.0,
            value=safe_float(record.get("opportunity_value")) if editing else 0.0, key="lg_oval")

    lead_url = st.text_input("Lead URL",
        value=record.get("lead_url", "") if editing else "", key="lg_url")
    notes = st.text_area("Notes", value=record.get("notes", "") if editing else "", key="lg_notes")

    if st.button("💾 Save", type="primary", use_container_width=True):
        data = {
            "brand": brand, "lead_source": lead_source,
            "campaign_id": campaign_id if campaign_id != 0 else None,
            "date_generated": str(date_gen) if date_gen else None,
            "company_name": company, "contact_name": contact,
            "job_title": job_title, "country": country,
            "email": email, "phone": phone,
            "service_interested": service, "lead_status": lead_status,
            "lead_owner": lead_owner,
            "qualification_date": str(qual_date) if qual_date else None,
            "opportunity_created": opp_created,
            "opportunity_value": opp_value,
            "notes": notes, "lead_url": lead_url,
        }
        if editing:
            sb.table("lead_generation").update(data).eq("lead_id", record["lead_id"]).execute()
            st.success("Lead updated!")
        else:
            sb.table("lead_generation").insert(data).execute()
            st.success("Lead added!")
        time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PAGE LAYOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.header("Lead Generation")
with col2:
    search = st.text_input("Search", placeholder="Search leads...", label_visibility="collapsed", key="search_lg")
with col3:
    if st.button("➕ Add Lead", type="primary", use_container_width=True):
        lead_form()

st.markdown("---")

data = sb.table("lead_generation").select("*").order("lead_id", desc=True).execute().data or []

if search:
    data = [r for r in data if search.lower() in str(r.values()).lower()]

if data:
    df = pd.DataFrame(data)
    display = ["brand", "lead_source", "company_name", "contact_name", "job_title",
               "country", "email", "lead_status", "lead_owner", "opportunity_created",
               "opportunity_value", "date_generated"]
    display = [c for c in display if c in df.columns]
    st.dataframe(df[display], use_container_width=True, hide_index=True)

    if not is_junior():
        st.markdown("---")
        st.markdown("#### Actions")
        opts = {r["lead_id"]: f"{r.get('contact_name','—')} @ {r.get('company_name','—')} (#{r['lead_id']})" for r in data}
        sel_id = st.selectbox("Select lead", options=list(opts.keys()), format_func=lambda x: opts[x], key="sel_lg")
        sel_rec = next(r for r in data if r["lead_id"] == sel_id)
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if _can_edit_lead(sel_rec):
                if st.button("✏️ Edit"):
                    lead_form(sel_rec)
            else:
                st.info("Own leads only.")
        with c2:
            if _can_edit_lead(sel_rec):
                if st.button("🗑️ Delete"):
                    confirm_delete("lead_generation", "lead_id", sel_rec["lead_id"],
                                   f"{sel_rec.get('contact_name','')} @ {sel_rec.get('company_name','')}")
else:
    st.info("No leads found.")
