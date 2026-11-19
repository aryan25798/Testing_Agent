"""
Top Navigation Header Component.
"""

import streamlit as st


def render_top_header(user_name: str = "Aryan", *args, **kwargs):
    clean_name = kwargs.get("user_name", user_name) or "Aryan"
    initials = "".join([part[0].upper() for part in clean_name.split() if part])[:2] or "A"
    st.markdown(
        f"""
        <div class="top-nav-bar">
            <div class="top-nav-left">
                <div class="brand-logo-badge">⚡</div>
                <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-right:1rem;">
                    AI Testing Assistant
                </div>
                <div class="nav-pill active">Projects</div>
                <div class="nav-pill">Organization</div>
                <div class="nav-pill">Dashboards</div>
                <div class="nav-pill">Reports</div>
            </div>
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="font-size:0.8rem; color:#64748b; font-weight:500;">{clean_name}</div>
                <div class="top-avatar-pill">{initials}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
