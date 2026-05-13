"""
Demo 2 — Strategy Comparison
Side-by-side: Raw OCR  vs  Azure Document Intelligence  vs  Azure OpenAI
Highlights where each approach wins and fails.

Run: streamlit run demo_compare.py
"""
import time
import pandas as pd
import streamlit as st
from fixtures import REPORTS

st.set_page_config(page_title="Extraction Strategy Comparison", layout="wide", page_icon="🔬")

st.title("🔬 Extraction Strategy Comparison")
st.caption("How much better does Azure Document Intelligence + OpenAI do vs. plain text extraction?")
st.divider()

# ── Confidence color helper ──────────────────────────────────────────────────

def conf_badge(c: float) -> str:
    if c >= 0.9:
        return f"🟢 {c:.0%}"
    if c >= 0.7:
        return f"🟡 {c:.0%}"
    return f"🔴 {c:.0%}"


# ── Sidebar ──────────────────────────────────────────────────────────────────

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

# ── Simulate three strategies ────────────────────────────────────────────────

fields = report["fields"]
quotes = report.get("quotes", {})
tables = report.get("doc_intelligence_tables", [])
has_issues = bool(report.get("validation_issues"))

# Strategy 1: Raw OCR (text extraction only, no AI)
# Simulated: lower confidence, misses units and context
def ocr_confidence(c: float, has_issues: bool) -> float:
    penalty = 0.35 if has_issues else 0.18
    return max(0.1, round(c - penalty, 2))

# Strategy 2: Document Intelligence (structured, no LLM)
# Better on tables, still needs LLM for context
def doc_int_confidence(c: float, has_tables: bool) -> float:
    if not has_tables:
        return max(0.1, round(c - 0.22, 2))
    return max(c - 0.04, 0.80)

with st.spinner("Running three strategies..."):
    time.sleep(1.5)

# ── Side-by-side table ────────────────────────────────────────────────────────

st.subheader("Field-by-field comparison")

rows = []
for field, meta in fields.items():
    c_gold = meta["confidence"]
    c_ocr = ocr_confidence(c_gold, has_issues)
    c_doc = doc_int_confidence(c_gold, bool(tables))
    quote_text, quote_page = quotes.get(field, ("—", "—"))
    rows.append({
        "Field": field,
        "Value": f"{meta['value']} {meta['unit']}",
        "Raw OCR": conf_badge(c_ocr),
        "Doc Intelligence": conf_badge(c_doc),
        "OpenAI (full)": conf_badge(c_gold),
        "Source quote": f'"{quote_text[:70]}…" (p.{quote_page})' if quote_text != "—" else "—",
    })

df = pd.DataFrame(rows)
display_cols = ["Field", "Value", "Raw OCR", "Doc Intelligence", "OpenAI (full)"]
if show_quotes:
    display_cols.append("Source quote")

st.dataframe(df[display_cols], hide_index=True, use_container_width=True)

# ── Summary metrics ───────────────────────────────────────────────────────────

st.divider()
st.subheader("Strategy summary")

avg_ocr  = sum(ocr_confidence(v["confidence"], has_issues) for v in fields.values()) / max(len(fields), 1)
avg_doc  = sum(doc_int_confidence(v["confidence"], bool(tables)) for v in fields.values()) / max(len(fields), 1)
avg_gold = sum(v["confidence"] for v in fields.values()) / max(len(fields), 1)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 📄 Raw OCR")
    st.metric("Avg. confidence", f"{avg_ocr:.0%}")
    st.caption("Extracts text from PDF, uses regex patterns to find numbers. Fast but brittle — breaks on any layout change or image-based PDF.")
    issues = sum(1 for v in fields.values() if ocr_confidence(v["confidence"], has_issues) < 0.7)
    if issues:
        st.error(f"{issues} field(s) below 70% confidence")
    else:
        st.success("All fields above 70%")

with col2:
    st.markdown("### 🔍 Azure Document Intelligence")
    st.metric("Avg. confidence", f"{avg_doc:.0%}", delta=f"+{avg_doc - avg_ocr:.0%} vs OCR")
    st.caption("Reads document structure, detects tables and key-value pairs. Works on most PDFs including scanned documents. No understanding of context.")
    issues = sum(1 for v in fields.values() if doc_int_confidence(v["confidence"], bool(tables)) < 0.7)
    if issues:
        st.warning(f"{issues} field(s) below 70% confidence")
    else:
        st.success("All fields above 70%")

with col3:
    st.markdown("### 🤖 Azure OpenAI (GPT-4o)")
    st.metric("Avg. confidence", f"{avg_gold:.0%}", delta=f"+{avg_gold - avg_ocr:.0%} vs OCR")
    st.caption("Understands context, normalizes units, resolves ambiguity. Combined with Doc Intelligence pre-processing, highest accuracy. Source-verifiable quotes.")
    issues = sum(1 for v in fields.values() if v["confidence"] < 0.7)
    if issues:
        st.warning(f"{issues} field(s) below 70% — flagged for review")
    else:
        st.success("All fields above 70%")

# ── Where each strategy fails ─────────────────────────────────────────────────

st.divider()
st.subheader("When does each strategy struggle?")

ex1, ex2, ex3 = st.columns(3)
with ex1:
    st.markdown("**Raw OCR fails when:**")
    st.markdown("""
- PDF is image-based (e.g. scanned)
- Layout changes between brokers
- Values span multiple columns
- Numbers appear without labels nearby
- Report is in a non-Latin language
""")
with ex2:
    st.markdown("**Doc Intelligence struggles with:**")
    st.markdown("""
- Implicit context ("5.00% — target for 2025")
- Values embedded in charts
- Language/currency normalization
- Distinguishing similar metrics
  (yield vs. cap rate vs. return)
""")
with ex3:
    st.markdown("**OpenAI can still miss:**")
    st.markdown("""
- Values only in images/charts
- Contradictions between tables and text
- Very long documents (token limit)
- Hallucinating plausible-sounding values
  when the information is absent
""")

if report.get("validation_issues"):
    st.warning("**Note for this report:** " + "  \n".join(report["validation_issues"]))
