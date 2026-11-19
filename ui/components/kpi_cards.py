"""
KPI Metric Cards Component.
Renders the top 4 metric cards matching the screenshot.
"""

import streamlit as st


def render_kpi_cards(
    test_suites: int = 2,
    scenarios: int = 3,
    schedules: int = 0,
    run_history: int = 247,
    passed: int = 181,
    failed: int = 50,
    success_rate: float = 73.0,
):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Test Suites</div>
                <div class="metric-value">{test_suites}</div>
                <div class="metric-subtext">{scenarios} scenarios</div>
                <div class="metric-icon-badge" style="background:#eff6ff; color:#3b82f6;">📄</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Schedules</div>
                <div class="metric-value">{schedules}</div>
                <div class="metric-subtext">{schedules} scheduled</div>
                <div class="metric-icon-badge" style="background:#ecfdf5; color:#10b981;">📅</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Run History</div>
                <div class="metric-value">{run_history}</div>
                <div class="metric-subtext">
                    <span class="metric-subtext-success">{passed} passed</span> · 
                    <span class="metric-subtext-danger">{failed} failed</span>
                </div>
                <div class="metric-icon-badge" style="background:#fffbeb; color:#f59e0b;">⏱️</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Success Rate</div>
                <div class="metric-value">{success_rate}%</div>
                <div style="width:100%; background:#f1f5f9; height:6px; border-radius:3px; margin-top:8px;">
                    <div style="width:{min(100, max(0, success_rate))}%; background:#10b981; height:6px; border-radius:3px;"></div>
                </div>
                <div class="metric-icon-badge" style="background:#fef2f2; color:#ef4444;">📈</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
