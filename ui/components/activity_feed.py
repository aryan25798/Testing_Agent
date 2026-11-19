"""
Recent Activity Stream Component.
"""

from typing import List, Dict, Any
import streamlit as st


def render_activity_feed(activities: List[Dict[str, Any]]):
    items_html = ""
    for act in activities:
        act_type = act.get("type", "info")
        if act_type == "success" or "passed" in act.get("title", "").lower() or "updated" in act.get("title", "").lower():
            icon = "✓"
            bg = "#ecfdf5"
            color = "#10b981"
        elif act_type == "error" or "failed" in act.get("title", "").lower():
            icon = "✕"
            bg = "#fef2f2"
            color = "#ef4444"
        elif "schedule" in act.get("title", "").lower():
            icon = "⏱"
            bg = "#fffbeb"
            color = "#f59e0b"
        else:
            icon = "⚡"
            bg = "#eff6ff"
            color = "#3b82f6"

        items_html += f"""
        <div class="activity-item">
            <div class="activity-icon" style="background:{bg}; color:{color}; font-weight:bold;">{icon}</div>
            <div class="activity-content">
                <div class="activity-title">{act.get('title', 'Activity Event')}</div>
                <div class="activity-desc">{act.get('description', '')}</div>
            </div>
            <div style="font-size:0.75rem; color:#94a3b8;">{act.get('timestamp', 'Recent')}</div>
        </div>
        """

    live_indicator = "<span style='color:#10b981; font-size:0.75rem; font-weight:600;'>● Live</span>"

    st.markdown(
        f"""
        <div class="content-card">
            <div class="card-header-row">
                <div class="card-title">Recent Activity {live_indicator}</div>
            </div>
            <div>
                {items_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
