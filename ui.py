"""Shared branding helpers — logo, sidebar, footer, global CSS."""
import base64
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent / "assets"
_LOGO_PATH   = str(_ROOT / "DataSentics_a_Bull_company_white.svg")
_BULL_B64    = base64.b64encode((_ROOT / "bull_logo.svg").read_bytes()).decode()
_BULL_IMG_SM = f'<img src="data:image/svg+xml;base64,{_BULL_B64}" width="80" style="display:block;">'

# Embed Tosh fonts as base64 so they work without a static file server
_FONTS_DIR = _ROOT / "fonts"
_TOSH_BLACK_B64  = base64.b64encode((_FONTS_DIR / "ToshA-Black.woff2").read_bytes()).decode()
_TOSH_MEDIUM_B64 = base64.b64encode((_FONTS_DIR / "ToshA-Medium.woff2").read_bytes()).decode()

_CSS = f"""
<style>
/* ── Brand fonts ─────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600&display=swap');

@font-face {{
    font-family: 'ToshA';
    font-weight: 900;
    font-style: normal;
    src: url('data:font/woff2;base64,{_TOSH_BLACK_B64}') format('woff2');
}}
@font-face {{
    font-family: 'ToshA';
    font-weight: 500;
    font-style: normal;
    src: url('data:font/woff2;base64,{_TOSH_MEDIUM_B64}') format('woff2');
}}

/* ── Global typography ───────────────────────────────────────────────── */
body, p, span, div, label, button, input, textarea, select {{
    font-family: 'Lexend', sans-serif !important;
}}
h1, h2, h3 {{
    font-family: 'ToshA', sans-serif !important;
    font-weight: 900 !important;
    letter-spacing: -0.02em;
}}
h4, h5, h6 {{
    font-family: 'ToshA', sans-serif !important;
    font-weight: 500 !important;
}}

/* ── Sidebar — dark navy background ─────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background-color: #002870 !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stMultiSelect label {{
    color: rgba(255, 255, 255, 0.9) !important;
}}
section[data-testid="stSidebar"] a,
section[data-testid="stSidebarNavLink"] {{
    color: rgba(255, 255, 255, 0.85) !important;
}}
section[data-testid="stSidebarNavLink"]:hover {{
    background-color: rgba(255, 255, 255, 0.08) !important;
}}
section[data-testid="stSidebar"] hr {{
    border-color: rgba(255, 255, 255, 0.15) !important;
}}

/* ── Primary buttons → Bull orange ──────────────────────────────────── */
button[kind="primary"] {{
    background-color: #FF5539 !important;
    border-color: #FF5539 !important;
    color: #fff !important;
}}
button[kind="primary"]:hover {{
    background-color: #e03d20 !important;
    border-color: #e03d20 !important;
}}

/* ── Links ───────────────────────────────────────────────────────────── */
a {{ color: #FF5539 !important; }}
a:hover {{ color: #e03d20 !important; }}

/* ── Bordered containers ─────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: #e8e0db !important;
    border-radius: 6px !important;
}}

/* ── Tab active underline → Bull orange ─────────────────────────────── */
button[data-baseweb="tab"][aria-selected="true"] {{
    border-bottom-color: #FF5539 !important;
    color: #FF5539 !important;
}}

/* ── Footer strip ────────────────────────────────────────────────────── */
.ds-footer {{
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-top: 16px;
    margin-top: 40px;
    border-top: 1px solid #e8e0db;
}}
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
