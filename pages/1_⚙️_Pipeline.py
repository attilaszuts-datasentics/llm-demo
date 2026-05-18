"""
Demo 1 — Automated Ingestion Pipeline
Azure Blob Storage → Azure Document Intelligence → Azure OpenAI → Databricks Delta Lake

Run: streamlit run demo_pipeline.py
"""
import time
import json
import pandas as pd
import streamlit as st
from fixtures import REPORTS, mock_doc_intelligence_response, mock_openai_response
from ui import brand_sidebar, ICON_AZURE_BLOB, ICON_AZURE_DOCINT, ICON_OPENAI, ICON_DATABRICKS

st.set_page_config(page_title="Ingestion Pipeline", layout="wide", page_icon="assets/DS_favicon_color.svg")
brand_sidebar()

# ── Header ─────────────────────────────────────────────────────────────────

st.title("Automated Report Ingestion Pipeline")
st.caption("Azure Blob Storage  →  Azure Document Intelligence  →  Azure OpenAI  →  Databricks Delta Lake")
st.divider()

# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Select Report")
    pdf_name = st.selectbox("Report", list(REPORTS.keys()), format_func=lambda x: x.replace(".pdf", ""))
    report = REPORTS[pdf_name]

    st.markdown("---")
    st.markdown(f"**Broker:** {report['broker']}")
    st.markdown(f"**Market:** {report['market']}")
    st.markdown(f"**Asset class:** {report['asset_class']}")
    st.markdown(f"**Period:** {report['period']}")
    if report.get("validation_issues"):
        st.warning("\n".join(report["validation_issues"]))

    run_btn = st.button("▶ Run Pipeline", type="primary", use_container_width=True)

# ── Pipeline diagram (always visible) ───────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(ICON_AZURE_BLOB + "**Azure Blob**", unsafe_allow_html=True)
    st.markdown("Object storage  \n`reports/2025/Q1/`")
with col2:
    st.markdown(ICON_AZURE_DOCINT + "**Doc Intelligence**", unsafe_allow_html=True)
    st.markdown("Layout + table extraction")
with col3:
    st.markdown(ICON_OPENAI + "**Azure OpenAI**", unsafe_allow_html=True)
    st.markdown("GPT-4o structured extraction")
with col4:
    st.markdown(ICON_DATABRICKS + "**Delta Lake**", unsafe_allow_html=True)
    st.markdown("Bronze → Silver → Gold")

st.divider()

if not run_btn:
    st.info("Select a report and click **▶ Run Pipeline** to see the end-to-end flow.")
    st.stop()

# ── Step 1: Azure Blob Storage ───────────────────────────────────────────────

with st.status("Step 1 — Uploading to Azure Blob Storage...", expanded=True) as s1:
    time.sleep(0.6)
    container = "real-estate-reports"
    blob_path = f"raw/2025/Q1/{pdf_name}"
    st.success(f"Uploaded to `{container}/{blob_path}`")
    st.markdown(f"""
| Property | Value |
|---|---|
| Container | `{container}` |
| Path | `{blob_path}` |
| Size | {len(REPORTS) * 420 + 180:,} KB |
| Tier | Hot |
| Redundancy | GRS |
""")
    s1.update(label="Step 1 — Azure Blob Storage  ✅", state="complete")

# ── Step 2: Azure Document Intelligence ─────────────────────────────────────

with st.status("Step 2 — Azure Document Intelligence: analyzing layout...", expanded=True) as s2:
    time.sleep(1.2)
    doc_resp = mock_doc_intelligence_response(pdf_name)

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Pages", len(doc_resp["pages"]))
    col_b.metric("Tables detected", doc_resp["tables_found"])
    col_c.metric("Key-value pairs", doc_resp["key_value_pairs_found"])
    col_d.metric("Confidence", f"{doc_resp['overall_confidence']:.0%}")

    if doc_resp["tables"]:
        st.markdown("**Extracted table (page 1):**")
        t = doc_resp["tables"][0]
        df = pd.DataFrame(t["rows"], columns=t["header"])
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.warning("No structured tables detected — document appears to be image-based. Falling back to OCR text only.")

    s2.update(label="Step 2 — Azure Document Intelligence  ✅", state="complete")

# ── Step 3: Azure OpenAI ─────────────────────────────────────────────────────

with st.status("Step 3 — Azure OpenAI (GPT-4o): extracting structured metrics...", expanded=True) as s3:
    time.sleep(1.0)
    oai_resp = mock_openai_response(pdf_name)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Model", oai_resp["model"])
    col_b.metric("Tokens used", f"{oai_resp['usage']['total_tokens']:,}")
    col_c.metric("Avg. field confidence", f"{oai_resp['avg_confidence']:.0%}")

    st.markdown("**Extracted JSON:**")
    st.json(oai_resp["extracted"])

    s3.update(label="Step 3 — Azure OpenAI  ✅", state="complete")

# ── Step 4: Databricks Delta Lake ────────────────────────────────────────────

with st.status("Step 4 — Writing to Databricks Delta Lake...", expanded=True) as s4:
    time.sleep(0.8)

    fields = report["fields"]
    rows = []
    for field_name, meta in fields.items():
        rows.append({
            "field": field_name,
            "value": meta["value"],
            "unit": meta["unit"],
            "confidence": meta["confidence"],
            "source_pdf": pdf_name,
            "period": report["period"],
            "market": report["market"],
        })
    df_gold = pd.DataFrame(rows)

    tab_b, tab_s, tab_g = st.tabs(["🥉 Bronze (raw)", "🥈 Silver (normalized)", "🥇 Gold (validated)"])

    with tab_b:
        st.caption("Raw JSON blob written as-is from OpenAI response")
        st.json(oai_resp["extracted"])

    with tab_s:
        st.caption("Parsed, typed, and joined with metadata")
        df_silver = df_gold[["field", "value", "unit", "confidence"]].copy()
        st.dataframe(df_silver, hide_index=True, use_container_width=True)

    with tab_g:
        st.caption("Validated, schema-enforced, ready for analytics")
        valid = df_gold[df_gold["confidence"] >= 0.8].copy()
        flagged = df_gold[df_gold["confidence"] < 0.8].copy()
        st.dataframe(valid, hide_index=True, use_container_width=True)
        if not flagged.empty:
            st.warning(f"{len(flagged)} field(s) below confidence threshold — held for human review")
            st.dataframe(flagged, hide_index=True, use_container_width=True)

    s4.update(label="Step 4 — Databricks Delta Lake  ✅", state="complete")

# ── Summary ──────────────────────────────────────────────────────────────────

st.divider()
st.success(f"**Pipeline complete.** {len(report['fields'])} fields extracted from `{pdf_name}` and written to Delta Lake.")
valid_count = sum(1 for v in report["fields"].values() if v["confidence"] >= 0.8)
flagged_count = len(report["fields"]) - valid_count
col1, col2, col3, col4 = st.columns(4)
col1.metric("Fields extracted", len(report["fields"]))
col2.metric("Auto-approved", valid_count)
col3.metric("Flagged for review", flagged_count)
col4.metric("Pipeline duration", "~3.6s")
