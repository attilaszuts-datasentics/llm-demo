"""
Demo 4 — Databricks Genie
Ask natural language questions over the extracted Delta Lake data.
Genie translates the question to SQL, runs it, and explains the result.

Run: streamlit run demo_genie.py
"""
import time
import random
import pandas as pd
import streamlit as st
from fixtures import REPORTS
from ui import brand_sidebar, brand_footer

st.set_page_config(page_title="Databricks Genie", layout="wide", page_icon="assets/DS_favicon_color.svg")
brand_sidebar()

# ── Build a flat "Delta table" from all fixtures ──────────────────────────────

rows = []
for pdf_name, report in REPORTS.items():
    for field, meta in report["fields"].items():
        rows.append({
            "pdf_name": pdf_name,
            "broker": report["broker"],
            "market": report["market"],
            "asset_class": report["asset_class"],
            "period": report["period"],
            "field_name": field,
            "value": meta["value"],
            "unit": meta["unit"],
            "confidence": meta["confidence"],
        })
DELTA_TABLE = pd.DataFrame(rows)

# ── Pre-scripted Genie Q&A ────────────────────────────────────────────────────
# Each entry: question → {sql, answer_df or answer_text, chart_type, explanation}

GENIE_QA = [
    {
        "q": "What is the vacancy rate for offices in Prague?",
        "sql": "SELECT market, period, value AS vacancy_rate_pct\nFROM gold.real_estate_metrics\nWHERE asset_class = 'Office' AND field_name = 'vacancy_rate' AND market = 'Prague'",
        "result": pd.DataFrame([{"market": "Prague", "period": "Q1 2025", "vacancy_rate_pct": "7.0%"}]),
        "chart": None,
        "explanation": "The Prague office market had a vacancy rate of **7.0%** in Q1 2025, down from 7.4% in Q1 2024 — a 38 basis point improvement year-on-year.",
    },
    {
        "q": "Compare prime yields across all asset classes",
        "sql": "SELECT market, asset_class, field_name, value AS yield_pct, unit\nFROM gold.real_estate_metrics\nWHERE field_name LIKE '%yield%'\nORDER BY value DESC",
        "result": DELTA_TABLE[DELTA_TABLE["field_name"].str.contains("yield")][
            ["market", "asset_class", "field_name", "value", "unit"]
        ].sort_values("value", ascending=False).reset_index(drop=True),
        "chart": "bar",
        "explanation": "Prime yields range from **4.25%** (Czech retail high street) to **6.00%** (Czech shopping centres). Office yields in Austria (5.00%) sit above Prague industrial (5.50%).",
    },
    {
        "q": "Which reports had low-confidence extractions?",
        "sql": "SELECT pdf_name, broker, asset_class,\n       COUNT(*) AS total_fields,\n       ROUND(AVG(confidence), 2) AS avg_confidence,\n       SUM(CASE WHEN confidence < 0.8 THEN 1 ELSE 0 END) AS flagged_fields\nFROM gold.real_estate_metrics\nGROUP BY pdf_name, broker, asset_class\nORDER BY avg_confidence ASC",
        "result": None,  # generated dynamically below
        "chart": "bar_confidence",
        "explanation": "The **CBRE Austria Retail** and **Knight Frank CZ Investment** reports had the most low-confidence fields — both are chart-heavy PDFs where values are embedded in images rather than text. These are good candidates for Document Intelligence pre-processing improvements.",
    },
    {
        "q": "What is the total industrial stock in Czech Republic?",
        "sql": "SELECT market, field_name, value, unit\nFROM gold.real_estate_metrics\nWHERE market = 'Czech Republic'\n  AND asset_class = 'Industrial'\n  AND field_name = 'total_stock_sqm'",
        "result": pd.DataFrame([{
            "market": "Czech Republic", "asset_class": "Industrial",
            "field": "total_stock_sqm", "value": "12,400,000 sqm", "growth_yoy": "+4.7%"
        }]),
        "chart": None,
        "explanation": "Czech industrial stock reached **12.4 million sqm** in Q1 2025, up 4.7% year-on-year. An additional 1.6 million sqm is currently under construction.",
    },
    {
        "q": "Show me take-up volumes across all office markets",
        "sql": "SELECT market, field_name, value, unit\nFROM gold.real_estate_metrics\nWHERE asset_class = 'Office'\n  AND field_name IN ('gross_take_up', 'net_take_up')\nORDER BY market, field_name",
        "result": DELTA_TABLE[
            (DELTA_TABLE["asset_class"] == "Office") &
            (DELTA_TABLE["field_name"].isin(["gross_take_up", "net_take_up"]))
        ][["market", "field_name", "value", "unit"]].reset_index(drop=True),
        "chart": "grouped_bar",
        "explanation": "Prague had gross take-up of **87,700 sqm** and net take-up of **47,900 sqm** in Q1 2025. Vienna recorded **34,062 sqm** in letting performance. The lower net-to-gross ratio in Prague (55%) reflects a high share of renegotiations.",
    },
]

# ── UI ────────────────────────────────────────────────────────────────────────

col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("")
with col_title:
    st.title("Databricks Genie")
    st.caption("Ask questions about the extracted real estate data in plain English — Genie writes the SQL for you.")

st.divider()

# ── Suggested questions ───────────────────────────────────────────────────────

st.markdown("**Try one of these questions:**")
cols = st.columns(len(GENIE_QA))
triggered_qa = None
for i, (col, qa) in enumerate(zip(cols, GENIE_QA)):
    with col:
        if st.button(qa["q"], key=f"suggest_{i}", use_container_width=True):
            triggered_qa = qa

# ── Free-text input ───────────────────────────────────────────────────────────

st.markdown("")
st.caption(
    "Custom questions are matched to the nearest preset by keyword. "
    "In production, Genie generates SQL against your real Delta tables."
)
user_q = st.chat_input("Or type your own question…")

if user_q and triggered_qa is None:
    matched = next(
        (qa for qa in GENIE_QA if any(w in user_q.lower() for w in qa["q"].lower().split()[:3])),
        None,
    )
    triggered_qa = matched or GENIE_QA[0]
    if not matched:
        st.info(f"No exact match — showing the closest preset: *\"{GENIE_QA[0]['q']}\"*")

if triggered_qa is None:
    st.markdown("#### How Genie works")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**1. Natural language → SQL**")
        st.markdown("Genie understands your question and generates the correct SQL query against your Delta tables — no SQL knowledge needed.")
    with col2:
        st.markdown("**2. Runs on Delta Lake**")
        st.markdown("The query runs directly on your governed Delta tables in Unity Catalog. All access controls and audit logs apply.")
    with col3:
        st.markdown("**3. Explains the result**")
        st.markdown("Genie doesn't just return a table — it summarises the finding in plain English, including relevant context.")

    st.divider()
    st.subheader("📊 Current Gold Table Preview")
    summary = (
        DELTA_TABLE.groupby(["market", "asset_class"])
        .agg(fields=("field_name", "count"), avg_confidence=("confidence", "mean"))
        .reset_index()
    )
    summary["avg_confidence"] = summary["avg_confidence"].map("{:.0%}".format)
    st.dataframe(summary, hide_index=True, use_container_width=True)
    st.stop()

# ── Genie "thinking" animation ────────────────────────────────────────────────

qa = triggered_qa
st.markdown(f"**You asked:** {qa['q']}")
st.markdown("")

with st.status("🧞  Genie is thinking...", expanded=True) as genie_status:
    time.sleep(0.4)
    st.markdown("✅  Understanding question")
    time.sleep(0.5)
    st.markdown("✅  Identifying relevant Delta tables")
    time.sleep(0.6)
    st.markdown("✅  Generating SQL")
    genie_status.update(label="🧞  Genie is thinking...  ✅", state="complete")

# ── Generated SQL ─────────────────────────────────────────────────────────────

with st.expander("🔍 Generated SQL", expanded=True):
    st.code(qa["sql"], language="sql")

# ── Result ────────────────────────────────────────────────────────────────────

st.markdown("#### Result")

if qa["chart"] == "bar_confidence":
    # Generate the confidence summary dynamically
    summary = (
        DELTA_TABLE.groupby(["broker", "asset_class"])
        .agg(
            total_fields=("field_name", "count"),
            avg_confidence=("confidence", "mean"),
            flagged=("confidence", lambda x: (x < 0.8).sum()),
        )
        .reset_index()
        .sort_values("avg_confidence")
        .reset_index(drop=True)
    )
    summary["avg_confidence_pct"] = summary["avg_confidence"].map("{:.0%}".format)
    st.dataframe(summary[["broker", "asset_class", "total_fields", "avg_confidence_pct", "flagged"]], hide_index=True, use_container_width=True)
    st.bar_chart(summary.set_index("broker")["avg_confidence"])

elif qa["chart"] == "bar" and qa["result"] is not None:
    df = qa["result"]
    st.dataframe(df, hide_index=True, use_container_width=True)
    if "value" in df.columns and df["value"].dtype in ["float64", "int64"]:
        label_col = "field_name" if "field_name" in df.columns else df.columns[0]
        st.bar_chart(df.set_index(label_col)["value"])

elif qa["chart"] == "grouped_bar" and qa["result"] is not None:
    df = qa["result"]
    st.dataframe(df, hide_index=True, use_container_width=True)
    pivot = df.pivot(index="market", columns="field_name", values="value")
    st.bar_chart(pivot)

elif qa["result"] is not None:
    st.dataframe(qa["result"], hide_index=True, use_container_width=True)

# ── Explanation ───────────────────────────────────────────────────────────────

st.markdown("#### Genie's interpretation")
st.info(qa["explanation"])
