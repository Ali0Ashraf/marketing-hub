"""
App.py — Main entry point for the Marketing Hub portal.
Handles login and multi-page navigation using st.navigation.
"""

import streamlit as st
from db import apply_custom_css, login, logout, get_current_user

# ── Page config (must be first Streamlit call) ───────────────────
st.set_page_config(
    page_title="Marketing Hub",
    page_icon="Ⓜ️",
    layout="wide",
)
apply_custom_css()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTHENTICATED — show sidebar + page navigation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if st.session_state.get("authenticated"):

    # Build page list
    pages = [
        st.Page("views/dashboard.py",        title="Dashboard",        icon="📊", default=True),
        st.Page("views/teams.py",            title="Teams",            icon="👥"),
        st.Page("views/campaigns.py",        title="Campaigns",        icon="📢"),
        st.Page("views/seo.py",              title="SEO",              icon="🔍"),
        st.Page("views/content_writing.py",  title="Content Writing",  icon="✍️"),
        st.Page("views/social_media.py",     title="Social Media",     icon="📱"),
        st.Page("views/pr.py",               title="PR",               icon="📰"),
        st.Page("views/lead_generation.py",  title="Lead Generation",  icon="🎯"),
        st.Page("views/designers.py",        title="Designers",        icon="🎨"),
    ]

    # Sidebar — branding (top)
    with st.sidebar:
        st.markdown("## Ⓜ️ Marketing Hub")
        st.markdown("---")

    # Navigation (Streamlit renders the page links in the sidebar)
    pg = st.navigation(pages)

    # Sidebar — user info (bottom)
    with st.sidebar:
        st.markdown("---")
        user = get_current_user()
        st.markdown(f"👤 **{user['full_name']}**")
        st.caption(f"{user['role']} • v1.0.0")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    # Run the selected page
    pg.run()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NOT AUTHENTICATED — show login form
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
else:
    # Center the login form
    _left, center, _right = st.columns([1, 1.5, 1])
    with center:
        st.markdown("")
        st.markdown("")
        st.markdown("## Ⓜ️ Marketing Hub")
        st.caption("Internal Data Entry Portal")
        st.markdown("---")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@company.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button(
                "🔐 Sign In", type="primary", use_container_width=True
            )

        if submitted:
            if email and password:
                result = login(email.strip(), password)
                if result:
                    st.rerun()
            else:
                st.warning("Please enter both email and password.")