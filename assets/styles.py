TOP_BAR_CSS = """
<style>
    .stApp {
        background: #f3f3f3;
    }

    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }

    .app-shell {
        padding: 0;
    }

    .top-bar {
        border: 3px solid #111111;
        background: #ffffff;
        padding: 1rem 1rem 0.7rem 1rem;
        margin-bottom: 1rem;
    }

    .top-bar h1 {
        margin: 0;
        font-size: 1.85rem;
        line-height: 1.1;
        color: #111111;
    }

    .subtitle {
        margin-top: 0.35rem;
        color: #333333;
        font-size: 0.95rem;
    }

    .label-box {
        display: inline-block;
        border: 3px solid #111111;
        background: #ffffff;
        padding: 0.35rem 0.7rem;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }

    .forecast-card {
        border: 3px solid #111111;
        background: #ffffff;
        padding: 0.75rem;
        min-height: 640px;
        margin-bottom: 1rem;
    }

    .forecast-card h3,
    .comparison-card h3 {
        text-align: center;
        margin: 0 0 0.75rem 0;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }

    .comparison-title-box {
        border: 3px solid #111111;
        padding: 0.6rem;
        text-align: center;
        font-weight: 700;
        background: #ffffff;
        margin: 0.6rem auto 1rem auto;
        max-width: 360px;
    }

    .forecast-meta {
        min-height: 66px;
        margin-bottom: 0.45rem;
        font-size: 0.94rem;
    }

    .status-pill {
        border: 3px solid #111111;
        padding: 0.7rem;
        min-height: 54px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        text-align: center;
        background: #ffffff;
    }

    .status-pill.success {
        background: #eaf7ea;
    }

    .status-pill.error {
        background: #fdecec;
    }

    .status-pill.idle {
        background: #f6f6f6;
    }

    .warning-banner {
        border-left: 5px solid #111111;
        background: #f7f2d9;
        padding: 0.6rem 0.75rem;
        margin: 0.55rem 0 0.75rem 0;
        font-size: 0.92rem;
    }

    .summary-box {
        border: 3px solid #111111;
        background: #ffffff;
        padding: 0.8rem;
        margin-top: 1rem;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border: 3px solid #111111 !important;
        background: #ffffff !important;
        color: #111111 !important;
        border-radius: 0 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stNumberInput"] input,
    div[data-testid="stFileUploader"] section {
        border-radius: 0 !important;
    }

    .small-note {
        color: #555555;
        font-size: 0.85rem;
    }
</style>
"""
