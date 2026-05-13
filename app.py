"""
Streamlit review app — human-in-the-loop extraction review
Run: streamlit run app.py
"""
import time
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from schema import ReportMetrics
from strategies import grounded, regex_llm, self_consistency, table_first, vanilla

PDF_DIR = Path(".")
PDFS = sorted(PDF_DIR.glob("*.pdf"))

STRATEGIES = {
    "Vanilla LLM": vanilla,
    "Table-first": table_first,
    "Regex + LLM": regex_llm,
    "Grounded (citations)": grounded,
    "Self-consistency (3×)": self_consistency,
}

NUMERIC_FIELDS = [
    ("prime_yield", "%"),
    ("vacancy_rate", "%"),
    ("prime_rent", "€"),
    ("gross_take_up", "sqm"),
    ("net_take_up", "sqm"),
    ("total_stock_sqm", "sqm"),
    ("transaction_volume_eur_bn", "€bn"),
]
META_FIELDS = ["market", "asset_class", "period", "prime_rent_unit"]


def validate(data: dict) -> tuple[bool, list[str]]:
    flat = {k: v["value"] if isinstance(v, dict) and "value" in v else v for k, v in data.items()}
    try:
        ReportMetrics(**flat)
        return True, []
    except ValidationError as e:
        return False, [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]


def flatten_value(v):
    if isinstance(v, dict):
        return v.get("value")
    return v


def confidence_color(c: float) -> str:
    if c >= 0.9:
        return "green"
    if c >= 0.67:
        return "orange"
    return "red"


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Report Extraction Review", layout="wide")
st.title("Report Extraction Review")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    selected_pdf = st.selectbox(
        "Report",
        [p.name for p in PDFS],
        index=0,
    )
    selected_strategies = st.multiselect(
        "Strategies to run",
        list(STRATEGIES.keys()),
        default=["Vanilla LLM", "Table-first", "Regex + LLM"],
    )
    run_btn = st.button("Run extraction", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("All strategies use `claude-haiku-4-5`. Grounded and self-consistency use more tokens.")

# ── Run extractions ───────────────────────────────────────────────────────────

if run_btn:
    if not selected_strategies:
        st.warning("Select at least one strategy.")
        st.stop()

    results = {}
    timings = {}
    progress = st.progress(0, text="Running...")

    for i, name in enumerate(selected_strategies):
        progress.progress((i) / len(selected_strategies), text=f"Running {name}...")
        t = time.time()
        try:
            results[name] = STRATEGIES[name](selected_pdf)
        except Exception as e:
            results[name] = {"error": str(e)}
        timings[name] = round(time.time() - t, 1)

    progress.progress(1.0, text="Done")
    st.session_state["results"] = results
    st.session_state["timings"] = timings
    st.session_state["pdf"] = selected_pdf

# ── Display results ───────────────────────────────────────────────────────────

if "results" not in st.session_state:
    st.info("Select a report and strategies, then click **Run extraction**.")
    st.stop()

results = st.session_state["results"]
timings = st.session_state["timings"]
pdf_name = st.session_state["pdf"]

st.subheader(f"Results — {pdf_name}")

tabs = st.tabs(["Comparison", "Citations", "Confidence", "Schema Validation"])

# ── Tab 1: Comparison ─────────────────────────────────────────────────────────

with tabs[0]:
    st.markdown("**Extracted values across all strategies**")

    rows = []
    all_fields = META_FIELDS + [f for f, _ in NUMERIC_FIELDS]

    for field in all_fields:
        row = {"Field": field}
        vals = []
        for name, data in results.items():
            v = flatten_value(data.get(field))
            row[name] = v
            if v is not None:
                vals.append(str(v))
        # Agreement indicator
        unique = set(str(v) for v in vals if v)
        row["Agreement"] = "✓" if len(unique) <= 1 else f"⚠ {len(unique)} values"
        rows.append(row)

    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.markdown("**Run times**")
    timing_cols = st.columns(len(timings))
    for col, (name, t) in zip(timing_cols, timings.items()):
        col.metric(name, f"{t}s")

# ── Tab 2: Citations ──────────────────────────────────────────────────────────

with tabs[1]:
    if "Grounded (citations)" not in results:
        st.info("Run the **Grounded (citations)** strategy to see source quotes.")
    else:
        data = results["Grounded (citations)"]
        st.markdown("Each value includes the verbatim quote it was extracted from, verified against the PDF text.")
        for field, unit in NUMERIC_FIELDS:
            entry = data.get(field)
            if not isinstance(entry, dict):
                continue
            val = entry.get("value")
            quote = entry.get("quote", "")
            page = entry.get("page")
            verified = entry.get("verified", False)

            with st.expander(f"**{field}** = {val} {unit}  |  page {page}  |  {'✅ verified' if verified else '❌ unverified'}"):
                if quote:
                    st.markdown(f"> {quote}")
                else:
                    st.caption("No quote provided")
                if not verified:
                    st.warning("Quote not found verbatim in document — may be paraphrased or hallucinated.")

# ── Tab 3: Confidence ─────────────────────────────────────────────────────────

with tabs[2]:
    if "Self-consistency (3×)" not in results:
        st.info("Run the **Self-consistency (3×)** strategy to see confidence scores.")
    else:
        data = results["Self-consistency (3×)"]
        st.markdown("Confidence = fraction of 3 independent runs that returned the same value.")
        st.markdown("")

        cols = st.columns([2, 1, 1, 3])
        cols[0].markdown("**Field**")
        cols[1].markdown("**Value**")
        cols[2].markdown("**Confidence**")
        cols[3].markdown("**All runs**")

        for field, unit in NUMERIC_FIELDS:
            entry = data.get(field)
            if not isinstance(entry, dict):
                continue
            c = entry.get("confidence", 0)
            color = confidence_color(c)
            cols = st.columns([2, 1, 1, 3])
            cols[0].write(field)
            cols[1].write(f"{entry.get('value')} {unit}")
            cols[2].markdown(f":{color}[{c:.0%}]")
            cols[3].write(str(entry.get("all_values", [])))

# ── Tab 4: Schema Validation ──────────────────────────────────────────────────

with tabs[3]:
    st.markdown("**Pydantic validation against expected ranges and formats**")
    st.caption("Validators: yield 0.5–20%, vacancy 0–60%, rent > 0, period matches Q1 2025 format.")
    st.markdown("")

    for name, data in results.items():
        ok, errors = validate(data)
        if ok:
            st.success(f"**{name}** — all fields valid")
        else:
            st.error(f"**{name}** — {len(errors)} issue(s) found")
            for err in errors:
                st.markdown(f"  • `{err}`")

    # Demo: show what validation catches
    with st.expander("Demo: inject bad values and see what gets caught"):
        st.markdown("**Injected errors:**")
        st.code(
            "prime_yield = 42.5     # decimal point off — should be 4.25\n"
            "vacancy_rate = 107.0   # impossible — over 100%\n"
            "period = 'First quarter 2025'  # wrong format"
        )
        if results:
            first = next(iter(results.values()))
            bad = dict(first)
            bad["prime_yield"] = 42.5
            bad["vacancy_rate"] = 107.0
            bad["period"] = "First quarter 2025"
            ok, errors = validate(bad)
            if not ok:
                st.error("Caught:")
                for err in errors:
                    st.markdown(f"  • `{err}`")
