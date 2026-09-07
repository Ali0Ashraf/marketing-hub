"""
db.py — Supabase client, authentication, RBAC, data helpers,
and shared UI components for the Marketing Hub portal.
"""

import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime, date

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DROPDOWN / ENUM CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BRANDS = ["Laoret", "Bayan_Tech", "Sawa_Tech", "ReguNet", "Asia_Localize"]

PLATFORMS_ADS = ["Google", "Meta", "LinkedIn", "TikTok", "Snapchat", "Microsoft"]
CAMPAIGN_OBJECTIVES = ["Lead_Generation", "Traffic", "Awareness", "Conversion"]
CAMPAIGN_STATUS = ["Active", "Paused", "Completed"]

CONTENT_TYPES = ["Blog", "Social", "Website", "Email", "Landing Page"]
CONTENT_STATUS = ["Assigned", "Draft", "Review", "Approved", "Published"]
REVISION_OPTIONS = ["Yes", "No"]

SOCIAL_PLATFORMS = ["Facebook", "Instagram", "LinkedIn", "X", "TikTok"]
SOCIAL_CONTENT_TYPES = ["Post", "Reel", "Story", "Carousel"]
SOCIAL_POST_STATUS = ["Planned", "Published", "Cancelled"]
CAPTION_STATUS = ["Draft", "Approved"]
DESIGN_STATUS_SM = ["Pending", "Ready"]

PR_STATUS = ["Draft", "Sent", "Completed"]

LEAD_SOURCES = ["Google", "LinkedIn", "Website", "Email", "Event", "Referral"]
LEAD_STATUS_OPTIONS = ["New", "Contacted", "Qualified", "Disqualified", "Converted"]
OPPORTUNITY_OPTIONS = ["Yes", "No"]

DESIGN_STATUS = ["Requested", "In Progress", "Delivered", "Revised", "Approved"]
TECHNICAL_AUDIT_OPTIONS = ["Done", "Pending"]

MEMBER_ROLES = ["Manager", "Senior", "Junior"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SUPABASE CLIENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_resource
def _init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def get_supabase() -> Client:
    return _init_supabase()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTHENTICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def login(email: str, password: str):
    """Sign in via Supabase Auth, then look up the team_members profile."""
    sb = get_supabase()
    try:
        resp = sb.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user_email = resp.user.email

        # Look up the member profile — use .execute() first, then check data
        result = (
            sb.table("team_members")
            .select("member_id, team_id, full_name, email, role, is_active")
            .eq("email", user_email)
            .execute()
        )

        members = result.data if result and result.data else []

        if members and len(members) > 0:
            member_data = members[0]
            st.session_state["user"] = member_data
            st.session_state["authenticated"] = True
            return member_data
        else:
            st.error("Your email is not registered as a team member. Contact your manager.")
            return None

    except Exception as e:
        msg = str(e)
        if "Invalid login credentials" in msg:
            st.error("❌ Invalid email or password.")
        else:
            st.error(f"Login failed: {msg}")
        return None


def logout():
    """Sign out and clear session."""
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass
    for key in ["user", "authenticated"]:
        st.session_state.pop(key, None)


def get_current_user():
    """Return the logged-in user dict or None."""
    if st.session_state.get("authenticated"):
        return st.session_state.get("user")
    return None


def require_login():
    """Guard: stops the page if the user is not authenticated."""
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please log in from the main page.")
        st.stop()
    return get_current_user()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ROLE-BASED ACCESS CONTROL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_manager() -> bool:
    u = get_current_user()
    return bool(u and u.get("role") == "Manager")


def is_senior() -> bool:
    u = get_current_user()
    return bool(u and u.get("role") == "Senior")


def is_junior() -> bool:
    u = get_current_user()
    return bool(u and u.get("role") == "Junior")


def can_edit(record_member_id=None) -> bool:
    """Manager → edit anything. Senior → own records only. Junior → never."""
    u = get_current_user()
    if not u:
        return False
    if u["role"] == "Manager":
        return True
    if u["role"] == "Senior":
        return record_member_id is None or record_member_id == u["member_id"]
    return False


def can_delete(record_member_id=None) -> bool:
    """Same rules as can_edit."""
    return can_edit(record_member_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_teams():
    return (
        get_supabase().table("teams")
        .select("*").order("team_name").execute().data or []
    )


def fetch_members(team_id=None, active_only=True):
    q = get_supabase().table("team_members").select("*")
    if team_id:
        q = q.eq("team_id", team_id)
    if active_only:
        q = q.eq("is_active", True)
    return q.order("full_name").execute().data or []


def fetch_campaigns(brand=None):
    q = get_supabase().table("campaigns").select("*")
    if brand:
        q = q.eq("brand", brand)
    return q.order("created_at", desc=True).execute().data or []


def member_name_map() -> dict:
    """Returns {member_id: full_name}."""
    return {m["member_id"]: m["full_name"] for m in fetch_members(active_only=False)}


def team_name_map() -> dict:
    """Returns {team_id: team_name}."""
    return {t["team_id"]: t["team_name"] for t in fetch_teams()}


def member_count_by_team() -> dict:
    """Returns {team_id: count_of_active_members}."""
    counts: dict = {}
    for m in fetch_members(active_only=True):
        tid = m.get("team_id")
        if tid:
            counts[tid] = counts.get(tid, 0) + 1
    return counts


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UTILITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_date(val):
    """Convert a date string from Supabase to a Python date, or None."""
    if not val:
        return None
    try:
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def safe_index(options: list, value, default=0):
    """Return the index of value in options, or default."""
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return default


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SHARED UI — CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def apply_custom_css():
    st.markdown(
        """
        <style>
        /* ── Dark-blue sidebar ── */
        section[data-testid="stSidebar"] {
            background-color: #1a1f36;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.15) !important;
        }
        section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
            color: #c8cdd6 !important;
            border-radius: 6px;
            padding: 0.4rem 0.75rem;
        }
        section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {
            color: #ffffff !important;
            background-color: rgba(255,255,255,0.08);
        }
        section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {
            color: #ffffff !important;
            background-color: rgba(59,130,246,0.18);
            border-left: 3px solid #3b82f6;
            font-weight: 600;
        }
        /* ── Metric cards ── */
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 18px 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        [data-testid="stMetric"] label {
            color: #6b7280 !important;
            font-size: 0.85rem !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #111827 !important;
            font-weight: 700 !important;
        }
        /* ── General polish ── */
        .main .block-container { padding-top: 2rem; }
        div[data-testid="stDialog"] > div { max-width: 700px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SHARED UI — CONFIRM DELETE DIALOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.dialog("Confirm Delete")
def confirm_delete(table_name: str, id_column: str, record_id, display_name: str):
    """Reusable delete-confirmation dialog."""
    st.warning(
        f"Are you sure you want to delete **{display_name}**?  \n"
        "This action cannot be undone."
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
            get_supabase().table(table_name).delete().eq(id_column, record_id).execute()
            st.success("Deleted successfully!")
            time.sleep(0.5)
            st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
