"""Shared branding helpers — logo, sidebar, footer, global CSS."""
import base64
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent / "assets"
_LOGO_PATH   = str(_ROOT / "DataSentics_a_Bull_company_white.svg")
_BULL_B64    = base64.b64encode((_ROOT / "bull_logo.svg").read_bytes()).decode()
_BULL_IMG_SM = f'<img src="data:image/svg+xml;base64,{_BULL_B64}" width="90" style="display:block;">'

# Embed Tosh fonts as base64 so they work without a static file server
_FONTS_DIR = _ROOT / "fonts"
_TOSH_BLACK_B64  = base64.b64encode((_FONTS_DIR / "ToshA-Black.woff2").read_bytes()).decode()
_TOSH_MEDIUM_B64 = base64.b64encode((_FONTS_DIR / "ToshA-Medium.woff2").read_bytes()).decode()

# Service logos for pipeline diagrams
def _svg_b64(name: str) -> str:
    return base64.b64encode((_ROOT / name).read_bytes()).decode()

def svc_icon(name: str, size: int = 36) -> str:
    """Return an <img> tag for a service logo SVG from assets/."""
    b64 = _svg_b64(name)
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" style="display:block;margin:0 auto 2px;">'

ICON_AZURE       = svc_icon("azure-icon.svg")
ICON_OPENAI      = svc_icon("openai-icon.svg")
ICON_DATABRICKS  = svc_icon("databricks-icon.svg")

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
    font-family: 'Lexend', system-ui, -apple-system, sans-serif !important;
}}

/* Arrow characters — force system font so glyphs always render */
.pipe-arrow {{
    font-family: system-ui, -apple-system, sans-serif !important;
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
/* White text for all sidebar content */
section[data-testid="stSidebar"] * {{
    color: rgba(255, 255, 255, 0.9) !important;
}}
/* Restore dark text inside input/select widgets — white bg, so text must be dark */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [data-baseweb="select"] * {{
    color: #1a1a1a !important;
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
/* Home icon before the first nav link (Home page has no emoji in filename) */
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:first-child::before {{
    content: "🏠 ";
    font-family: system-ui, sans-serif;
    display: inline;
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

/* ── Footer — fixed bottom-right watermark ───────────────────────────── */
.ds-footer {{
    position: fixed;
    bottom: 16px;
    right: 24px;
    z-index: 9999;
    opacity: 0.65;
    transition: opacity 0.2s;
}}
.ds-footer:hover {{
    opacity: 1;
}}
</style>
"""


def inject_brand_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def brand_sidebar() -> None:
    """Logo pinned to top of sidebar; injects CSS and fixed footer watermark."""
    inject_brand_css()
    st.logo(_LOGO_PATH, size="large")
    brand_footer()


def brand_footer() -> None:
    """Fixed bottom-right Bull logo watermark."""
    st.markdown(f'<div class="ds-footer">{_BULL_IMG_SM}</div>', unsafe_allow_html=True)
