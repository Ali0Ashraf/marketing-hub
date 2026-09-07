"""
Teams — manage Teams (card grid) and Team Members (data table).
"""

import streamlit as st
import pandas as pd
from db import (
    require_login, get_supabase, is_manager, is_junior,
    can_edit, can_delete, confirm_delete,
    fetch_teams, fetch_members, member_count_by_team,
    team_name_map, MEMBER_ROLES, safe_index,
)

user = require_login()
sb = get_supabase()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DIALOGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.dialog("Team")
def team_form(record=None):
    editing = record is not None
    st.subheader("Edit Team" if editing else "New Team")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Team Name *", value=record.get("team_name", "") if editing else "")
    with c2:
        manager = st.text_input("Manager Name", value=record.get("manager_name", "") if editing else "")

    if st.button("💾 Save", type="primary", use_container_width=True):
        if not name:
            st.error("Team name is required.")
            return
        data = {"team_name": name, "manager_name": manager}
        if editing:
            sb.table("teams").update(data).eq("team_id", record["team_id"]).execute()
            st.success("Team updated!")
        else:
            sb.table("teams").insert(data).execute()
            st.success(f"Team '{name}' added!")
        import time; time.sleep(0.5)
        st.rerun()


@st.dialog("Team Member")
def member_form(record=None):
    editing = record is not None
    st.subheader("Edit Member" if editing else "New Member")

    teams = fetch_teams()
    if not teams:
        st.warning("Please create a team first.")
        return
    team_opts = {t["team_id"]: t["team_name"] for t in teams}
    team_ids = list(team_opts.keys())
    default_team = 0
    if editing and record.get("team_id") in team_ids:
        default_team = team_ids.index(record["team_id"])

    c1, c2 = st.columns(2)
    with c1:
        full_name = st.text_input("Full Name *", value=record.get("full_name", "") if editing else "")
    with c2:
        email = st.text_input("Email *", value=record.get("email", "") if editing else "")

    c3, c4, c5 = st.columns(3)
    with c3:
        team_id = st.selectbox("Team *", options=team_ids, index=default_team, format_func=lambda x: team_opts[x])
    with c4:
        role = st.selectbox("Role *", options=MEMBER_ROLES, index=safe_index(MEMBER_ROLES, record.get("role")) if editing else 0)
    with c5:
        is_active = st.checkbox("Active", value=record.get("is_active", True) if editing else True)

    if st.button("💾 Save", type="primary", use_container_width=True):
        if not full_name or not email:
            st.error("Name and email are required.")
            return
        data = {
            "full_name": full_name, "email": email,
            "team_id": team_id, "role": role, "is_active": is_active,
        }
        if editing:
            sb.table("team_members").update(data).eq("member_id", record["member_id"]).execute()
            st.success("Member updated!")
        else:
            sb.table("team_members").insert(data).execute()
            st.success(f"Member '{full_name}' added!")
        import time; time.sleep(0.5)
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TABS — Teams | Team Members
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab_teams, tab_members = st.tabs(["👥 Teams", "👤 Team Members"])

# ── TEAMS TAB (card grid) ────────────────────────────────────────
with tab_teams:
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.header("Teams")
    with col2:
        search = st.text_input("Search", placeholder="Search teams...", label_visibility="collapsed", key="search_teams")
    with col3:
        if st.button("➕ Add Team", type="primary", use_container_width=True):
            team_form()

    st.markdown("---")

    teams = fetch_teams()
    counts = member_count_by_team()

    if search:
        teams = [t for t in teams if search.lower() in t["team_name"].lower() or search.lower() in (t.get("manager_name") or "").lower()]

    if teams:
        cols = st.columns(3)
        for i, t in enumerate(teams):
            with cols[i % 3]:
                with st.container(border=True):
                    st.subheader(t["team_name"])
                    st.write(f"Manager: {t.get('manager_name', '—')}")
                    st.caption(f"{counts.get(t['team_id'], 0)} Members")
                    if is_manager():
                        ec, dc = st.columns(2)
                        with ec:
                            if st.button("✏️", key=f"et_{t['team_id']}"):
                                team_form(t)
                        with dc:
                            if st.button("🗑️", key=f"dt_{t['team_id']}"):
                                confirm_delete("teams", "team_id", t["team_id"], t["team_name"])
    else:
        st.info("No teams found.")

# ── TEAM MEMBERS TAB (data table) ────────────────────────────────
with tab_members:
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.header("Team Members")
    with col2:
        search_m = st.text_input("Search", placeholder="Search members...", label_visibility="collapsed", key="search_members")
    with col3:
        if st.button("➕ Add Member", type="primary", use_container_width=True):
            member_form()

    st.markdown("---")

    members = fetch_members(active_only=False)
    t_map = team_name_map()

    if search_m:
        members = [m for m in members if search_m.lower() in str(m.values()).lower()]

    if members:
        df = pd.DataFrame(members)
        df["team"] = df["team_id"].map(t_map).fillna("—")
        display_cols = ["full_name", "email", "role", "team", "is_active"]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        # Edit / Delete
        if is_manager():
            st.markdown("#### Actions")
            mem_opts = {m["member_id"]: f"{m['full_name']} ({m['email']})" for m in members}
            sel_id = st.selectbox("Select member", options=list(mem_opts.keys()), format_func=lambda x: mem_opts[x], key="sel_member")
            sel_rec = next(m for m in members if m["member_id"] == sel_id)
            c1, c2, _ = st.columns([1, 1, 4])
            with c1:
                if st.button("✏️ Edit Member"):
                    member_form(sel_rec)
            with c2:
                if st.button("🗑️ Delete Member"):
                    confirm_delete("team_members", "member_id", sel_rec["member_id"], sel_rec["full_name"])
    else:
        st.info("No team members found.")
