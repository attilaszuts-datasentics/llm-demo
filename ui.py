"""Shared branding helpers — logo, sidebar, footer, global CSS."""
import base64
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent / "assets"
_LOGO_PATH   = str(_ROOT / "DataSentics_a_Bull_company_white.svg")
_BULL_B64    = base64.b64encode((_ROOT / "bull_logo.svg").read_bytes()).decode()
_BULL_IMG_SM = f'<img src="data:image/svg+xml;base64,{_BULL_B64}" width="80" style="display:block;">'

_CSS = """
<style>
/* ── Global typography ───────────────────────────────────────────────── */
h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.01em; }

/* ── Sidebar — dark navy background ─────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #002870 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stMultiSelect label {
    color: rgba(255, 255, 255, 0.9) !important;
}
section[data-testid="stSidebar"] a,
section[data-testid="stSidebarNavLink"] {
    color: rgba(255, 255, 255, 0.85) !important;
}
section[data-testid="stSidebarNavLink"]:hover {
    background-color: rgba(255, 255, 255, 0.08) !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.15) !important;
}

/* ── Primary buttons → coral ─────────────────────────────────────────── */
button[kind="primary"] {
    background-color: #ED7650 !important;
    border-color: #ED7650 !important;
    color: #fff !important;
}
button[kind="primary"]:hover {
    background-color: #d9603e !important;
    border-color: #d9603e !important;
}

/* ── Links ───────────────────────────────────────────────────────────── */
a { color: #ED7650 !important; }
a:hover { color: #d9603e !important; }

/* ── Bordered containers ─────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #e8e0db !important;
    border-radius: 6px !important;
}

/* ── Tab active underline → coral ────────────────────────────────────── */
button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom-color: #ED7650 !important;
    color: #ED7650 !important;
}

/* ── Footer strip ────────────────────────────────────────────────────── */
.ds-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-top: 16px;
    margin-top: 40px;
    border-top: 1px solid #e8e0db;
}
</style>
"""


def inject_brand_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def brand_sidebar() -> None:
    """Logo pinned to top of sidebar via st.logo(), dark navy background."""
    inject_brand_css()
    st.logo(_LOGO_PATH, size="large")


def brand_footer() -> None:
    """Footer strip with Bull logo."""
    st.markdown(f'<div class="ds-footer">{_BULL_IMG_SM}</div>', unsafe_allow_html=True)
