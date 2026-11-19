"""
Interactive Analytics Charts using Plotly.
Matches the visual design of the reference dashboard screenshot.
"""

import plotly.graph_objects as go


def create_results_donut_chart(passed: int, failed: int, pending: int) -> go.Figure:
    """Creates the 'Test Results Overview' donut chart with central total."""
    total = passed + failed + pending
    if total == 0:
        total = 1
        labels = ["No Data"]
        values = [1]
        colors = ["#e2e8f0"]
    else:
        labels = ["Passed", "Failed", "Pending"]
        values = [passed, failed, pending]
        colors = ["#10b981", "#ef4444", "#f59e0b"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.68,
                marker=dict(colors=colors),
                textinfo="none",
                hoverinfo="label+value+percent",
                sort=False,
            )
        ]
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=12, color="#475569"),
        ),
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        annotations=[
            dict(
                text=f"<b>{total}</b><br><span style='font-size:11px;color:#64748b'>total</span>",
                x=0.5,
                y=0.5,
                font_size=20,
                showarrow=False,
                align="center",
            )
        ],
    )
    return fig


def create_execution_trend_chart() -> go.Figure:
    """Creates the 'Execution Trend' dual-line chart (Success % and Runs)."""
    dates = ["Apr 9", "Apr 10", "Apr 11", "Apr 12", "Apr 13", "Apr 14", "Apr 15"]
    success_rate = [75, 78, 82, 80, 85, 79, 84]
    runs = [28, 35, 42, 30, 48, 22, 54]

    fig = go.Figure()

    # Success % line (Indigo / Purple)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=success_rate,
            mode="lines+markers",
            name="Success %",
            line=dict(color="#4f46e5", width=2.5),
            marker=dict(size=5),
        )
    )

    # Runs line (Emerald Green)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=runs,
            mode="lines+markers",
            name="Runs",
            line=dict(color="#10b981", width=2.5),
            marker=dict(size=5),
        )
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=20, b=10, l=10, r=10),
        height=260,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        xaxis=dict(
            showgrid=False,
            linecolor="#e2e8f0",
            tickfont=dict(color="#64748b", size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            linecolor="#e2e8f0",
            tickfont=dict(color="#64748b", size=11),
        ),
    )
    return fig
