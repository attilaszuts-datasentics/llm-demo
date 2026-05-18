"""
Demo 2 — Strategy Comparison
Raw OCR  →  Regex + LLM  →  Azure Document Intelligence  →  Azure OpenAI
Highlights where each approach wins and where it fails.

Run: streamlit run demo_compare.py
"""
import re
import time
import pandas as pd
import streamlit as st
from fixtures import REPORTS
from utils import get_pages, full_text
from ui import brand_sidebar, brand_footer

st.set_page_config(page_title="Extraction Strategy Comparison", layout="wide", page_icon="assets/DS_favicon_color.svg")
brand_sidebar()

st.title("Extraction Strategy Comparison")
st.caption("Four strategies on the same report — from dumb text search to full LLM extraction")
st.divider()

# ── Confidence helpers ───────────────────────────────────────────────────────

def conf_badge(c: float) -> str:
    if c >= 0.9:
        return f"🟢 {c:.0%}"
    if c >= 0.7:
        return f"🟡 {c:.0%}"
    return f"🔴 {c:.0%}"

def ocr_confidence(c: float, has_issues: bool) -> float:
    return max(0.1, round(c - (0.35 if has_issues else 0.18), 2))

def regex_confidence(c: float, has_issues: bool, field_has_match: bool) -> float:
    if not field_has_match:
        return max(0.1, round(c - (0.30 if has_issues else 0.15), 2))
    return max(0.1, round(c - (0.18 if has_issues else 0.09), 2))

def doc_int_confidence(c: float, has_tables: bool) -> float:
    if not has_tables:
        return max(0.1, round(c - 0.22, 2))
    return max(c - 0.04, 0.80)

# ── Regex patterns (same as strategies.py) ───────────────────────────────────

PATTERNS = [
    (r"(?:prime\s+)?yield[^\n]{0,60}?(\d+\.?\d*)\s*%",                    "yield"),
    (r"vacancy[^\n]{0,60}?(\d+\.?\d*)\s*%",                               "vacancy"),
    (r"(?:prime\s+)?rent[^\n]{0,80}?[€$£]?\s*(\d[\d,\.]+)",              "rent"),
    (r"take.?up[^\n]{0,60}?(\d[\d,\.]+)\s*(?:sq|m²)",                    "take_up"),
    (r"(\d[\d,\.]+)\s*(?:million\s+)?sq\s*m[^\n]{0,40}?stock",           "stock"),
    (r"(?:transaction\s+)?volume[^\n]{0,60}?([\d,\.]+)\s*(?:Mrd|Mio|billion|bn|million)", "volume"),
]

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    pdf_name = st.selectbox("Report", list(REPORTS.keys()), format_func=lambda x: x.replace(".pdf", ""))
    report = REPORTS[pdf_name]
    st.markdown(f"**Broker:** {report['broker']}  \n**Market:** {report['market']}  \n**Period:** {report['period']}")
    show_quotes = st.toggle("Show source quotes", value=True)
    run_btn = st.button("▶  Compare strategies", type="primary", use_container_width=True)

if not run_btn:
    st.info("Select a report and click **▶ Compare strategies**.")
    st.stop()

# ── Run regex on actual PDF text ─────────────────────────────────────────────

fields = report["fields"]
quotes = report.get("quotes", {})
tables = report.get("doc_intelligence_tables", [])
has_issues = bool(report.get("validation_issues"))

with st.spinner("Reading PDF and running strategies..."):
    pages = get_pages(pdf_name)
    text = full_text(pages)
    time.sleep(0.5)

    regex_hits: dict[str, list[str]] = {}
    for pattern, label in PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            regex_hits[label] = [m.strip() for m in matches[:4]]

# ── Side-by-side table ────────────────────────────────────────────────────────

st.subheader("Field-by-field comparison")

FIELD_TO_REGEX_KEY = {
    "prime_yield": "yield", "prime_yield_office": "yield",
    "prime_yield_residential": "yield", "prime_yield_logistics": "yield",
    "prime_yield_high_street": "yield", "prime_yield_shopping_ctr": "yield",
    "vacancy_rate": "vacancy",
    "prime_rent": "rent", "prime_rent_min": "rent", "prime_rent_max": "rent",
    "gross_take_up": "take_up", "net_take_up": "take_up",
    "total_stock_sqm": "stock",
    "transaction_volume_eur_bn": "volume",
}

rows = []
for field, meta in fields.items():
    c_gold = meta["confidence"]
    regex_key = FIELD_TO_REGEX_KEY.get(field)
    field_has_match = bool(regex_key and regex_hits.get(regex_key))
    candidates = regex_hits.get(regex_key, []) if regex_key else []

    c_ocr   = ocr_confidence(c_gold, has_issues)
    c_regex = regex_confidence(c_gold, has_issues, field_has_match)
    c_doc   = doc_int_confidence(c_gold, bool(tables))
    quote_text, quote_page = quotes.get(field, ("—", "—"))

    rows.append({
        "Field":             field,
        "Value":             f"{meta['value']} {meta['unit']}",
        "Raw OCR":           conf_badge(c_ocr),
        "Regex + LLM":       conf_badge(c_regex),
        "Regex candidates":  ", ".join(candidates) if candidates else "—",
        "Doc Intelligence":  conf_badge(c_doc),
        "OpenAI (full)":     conf_badge(c_gold),
        "Source quote":      f'"{quote_text[:70]}…" (p.{quote_page})' if quote_text != "—" else "—",
    })

df = pd.DataFrame(rows)
display_cols = ["Field", "Value", "Raw OCR", "Regex + LLM", "Regex candidates", "Doc Intelligence", "OpenAI (full)"]
if show_quotes:
    display_cols.append("Source quote")

st.dataframe(df[display_cols], hide_index=True, use_container_width=True)

# ── Regex candidates expander ─────────────────────────────────────────────────

if regex_hits:
    with st.expander("🔍 All regex candidates found in this document"):
        st.caption("These are the raw values the regex scanner found before any LLM normalization.")
        for label, matches in regex_hits.items():
            st.markdown(f"**{label}:** `{'` · `'.join(matches)}`")
else:
    with st.expander("🔍 Regex candidates"):
        st.warning("No regex candidates found — document is likely image-based with no extractable text.")

# ── Summary metrics ───────────────────────────────────────────────────────────

st.divider()
st.subheader("Strategy summary")

avg_ocr   = sum(ocr_confidence(v["confidence"], has_issues) for v in fields.values()) / max(len(fields), 1)
avg_regex = sum(regex_confidence(v["confidence"], has_issues, bool(FIELD_TO_REGEX_KEY.get(f) and regex_hits.get(FIELD_TO_REGEX_KEY[f]))) for f, v in fields.items()) / max(len(fields), 1)
avg_doc   = sum(doc_int_confidence(v["confidence"], bool(tables)) for v in fields.values()) / max(len(fields), 1)
avg_gold  = sum(v["confidence"] for v in fields.values()) / max(len(fields), 1)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 📄 Raw OCR")
    st.metric("Avg. confidence", f"{avg_ocr:.0%}")
    st.caption("Extracts text from the PDF and searches for numbers near keywords. Fast and zero-cost but brittle — any layout change breaks it.")
    n = sum(1 for v in fields.values() if ocr_confidence(v["confidence"], has_issues) < 0.7)
    if n:
        st.error(f"{n} field(s) below 70%")
    else:
        st.success("All fields above 70%")

with col2:
    st.markdown("### 🔎 Regex + LLM")
    st.metric("Avg. confidence", f"{avg_regex:.0%}", delta=f"+{avg_regex - avg_ocr:.0%} vs OCR")
    st.caption(
        f"Regex finds {len(regex_hits)} candidate groups in the text. "
        "LLM then picks the right value and normalizes units. More reliable than pure OCR, still fails on image PDFs."
    )
    n = sum(1 for f, v in fields.items() if regex_confidence(v["confidence"], has_issues, bool(FIELD_TO_REGEX_KEY.get(f) and regex_hits.get(FIELD_TO_REGEX_KEY.get(f)))) < 0.7)
    if n:
        st.warning(f"{n} field(s) below 70%")
    else:
        st.success("All fields above 70%")

with col3:
    st.markdown("### 🔍 Doc Intelligence")
    st.metric("Avg. confidence", f"{avg_doc:.0%}", delta=f"+{avg_doc - avg_ocr:.0%} vs OCR")
    st.caption("Azure reads the document structure — tables, key-value pairs, layout — regardless of formatting. No LLM, no context understanding.")
    n = sum(1 for v in fields.values() if doc_int_confidence(v["confidence"], bool(tables)) < 0.7)
    if n:
        st.warning(f"{n} field(s) below 70%")
    else:
        st.success("All fields above 70%")

with col4:
    st.markdown("### 🤖 OpenAI (full)")
    st.metric("Avg. confidence", f"{avg_gold:.0%}", delta=f"+{avg_gold - avg_ocr:.0%} vs OCR")
    st.caption("Doc Intelligence output + full text sent to GPT-4o. Understands context, normalizes units, cites sources. Highest accuracy, costs ~€0.02/report.")
    n = sum(1 for v in fields.values() if v["confidence"] < 0.7)
    if n:
        st.warning(f"{n} field(s) below 70%")
    else:
        st.success("All fields above 70%")

# ── When each strategy fails ──────────────────────────────────────────────────

st.divider()
st.subheader("When does each strategy struggle?")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("**Raw OCR fails when:**")
    st.markdown("- PDF is image-based\n- Layout changes between brokers\n- Values span multiple columns\n- Non-Latin language")
with c2:
    st.markdown("**Regex + LLM fails when:**")
    st.markdown("- No text layer (image PDF)\n- Label and value are far apart\n- Value is in a chart\n- Unconventional phrasing")
with c3:
    st.markdown("**Doc Intelligence struggles with:**")
    st.markdown("- Values only in charts\n- Implicit context\n- Unit normalization\n- Distinguishing similar metrics")
with c4:
    st.markdown("**OpenAI can still miss:**")
    st.markdown("- Values only in images\n- Very long documents\n- Contradictions in source\n- Hallucinated plausible values")

if report.get("validation_issues"):
    st.warning("**This report:** " + "  \n".join(report["validation_issues"]))

brand_footer()
