"""
Test Suites Overview Table Component.
"""

from typing import List, Dict, Any
import streamlit as st


def render_suites_table(suites: List[Dict[str, Any]]):
    rows_html = ""
    for s in suites:
        status_val = s.get("status", "Active")
        if status_val.lower() == "active":
            badge_class = "status-active"
        elif "pending" in status_val.lower():
            badge_class = "status-pending"
        else:
            badge_class = "status-inactive"

        rows_html += f"""
        <tr>
            <td style="font-weight:600; color:#0f172a;">{s.get('suite_name', 'Default Suite')}</td>
            <td>{s.get('scenarios', 1)}</td>
            <td>{s.get('cases', 10)}</td>
            <td><span class="status-badge {badge_class}">{status_val}</span></td>
        </tr>
        """

    count_badge = f"<span style='background:#f1f5f9; color:#475569; font-size:0.75rem; padding:2px 8px; border-radius:12px; margin-left:6px;'>{len(suites)}</span>"

    st.markdown(
        f"""
        <div class="content-card">
            <div class="card-header-row">
                <div class="card-title">Test Suites Overview {count_badge}</div>
                <div>
                    <span style="background:#ef4444; color:white; font-size:0.8rem; font-weight:600; padding:4px 12px; border-radius:6px; cursor:pointer;">
                        View All
                    </span>
                </div>
            </div>
            <table class="saas-table">
                <thead>
                    <tr>
                        <th>Test Suite</th>
                        <th>Scenarios</th>
                        <th>Cases</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
