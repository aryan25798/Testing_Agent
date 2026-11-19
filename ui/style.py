"""
Custom CSS Stylesheet for Testing Agent Platform.
Faithfully recreates the modern, crisp, professional SaaS aesthetic from the reference dashboard.
"""

def get_custom_css() -> str:
    return """
    <style>
    /* Global Page Styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1e293b;
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }

    /* Top Navigation Bar */
    .top-nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1.25rem;
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }

    .top-nav-left {
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }

    .brand-logo-badge {
        background: #ef4444;
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
    }

    .nav-pill {
        font-size: 0.9rem;
        font-weight: 500;
        color: #64748b;
        padding: 0.35rem 0.85rem;
        border-radius: 6px;
        cursor: pointer;
    }

    .nav-pill.active {
        color: #0f172a;
        background: #f1f5f9;
        font-weight: 600;
    }

    .top-avatar-pill {
        background: #0f172a;
        color: white;
        font-size: 0.85rem;
        font-weight: 600;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Modern Card Layouts */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        height: 100%;
        position: relative;
    }

    .metric-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.1;
        margin-bottom: 0.35rem;
    }

    .metric-subtext {
        font-size: 0.82rem;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .metric-subtext-success {
        color: #10b981;
        font-weight: 600;
    }

    .metric-subtext-danger {
        color: #ef4444;
        font-weight: 600;
    }

    .metric-icon-badge {
        position: absolute;
        top: 1.25rem;
        right: 1.25rem;
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }

    /* Content Cards */
    .content-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 1.5rem;
    }

    .card-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
    }

    /* Table Styling */
    .saas-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
    }

    .saas-table th {
        text-align: left;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f1f5f9;
        letter-spacing: 0.04em;
    }

    .saas-table td {
        padding: 0.85rem 1rem;
        border-bottom: 1px solid #f8fafc;
        color: #334155;
    }

    .status-badge {
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }

    .status-active {
        background: #ecfdf5;
        color: #059669;
    }

    .status-inactive {
        background: #fef2f2;
        color: #dc2626;
    }

    .status-pending {
        background: #fffbeb;
        color: #d97706;
    }

    /* Activity Items */
    .activity-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f8fafc;
    }

    .activity-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        flex-shrink: 0;
        margin-top: 2px;
    }

    .activity-content {
        flex: 1;
    }

    .activity-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #1e293b;
    }

    .activity-desc {
        font-size: 0.8rem;
        color: #64748b;
    }

    /* Beginner Wizard Help Box */
    .beginner-guide-box {
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1rem 1.25rem;
        border-radius: 6px;
        margin-bottom: 1.25rem;
    }

    .beginner-guide-title {
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 0.25rem;
        font-size: 0.95rem;
    }

    .beginner-guide-text {
        font-size: 0.85rem;
        color: #334155;
        line-height: 1.5;
    }
    </style>
    """
