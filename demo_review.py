"""
Demo 3 — Human Review Queue
Low-confidence extractions surface for analyst sign-off before entering production.

Run: streamlit run demo_review.py
"""
import pandas as pd
import streamlit as st
from fixtures import REPORTS

st.set_page_config(page_title="Review Queue", layout="wide", page_icon="✅")

st.title("✅ Human Review Queue")
st.caption("AI-flagged extractions awaiting analyst sign-off before writing to the Gold Delta table")
st.divider()

# ── Build the review queue from all reports ───────────────────────────────────

if "decisions" not in st.session_state:
    st.session_state.decisions = {}   # key: (pdf, field) → "approved" | "rejected" | None
if "edits" not in st.session_state:
    st.session_state.edits = {}       # key: (pdf, field) → edited value

queue_rows = []
for pdf_name, report in REPORTS.items():
    for field, meta in report["fields"].items():
        queue_rows.append({
            "pdf": pdf_name,
            "broker": report["broker"],
            "market": report["market"],
            "asset_class": report["asset_class"],
            "field": field,
            "value": meta["value"],
            "unit": meta["unit"],
            "confidence": meta["confidence"],
            "quote": report["quotes"].get(field, ("", ""))[0],
            "page": report["quotes"].get(field, ("", ""))[1],
        })

df_all = pd.DataFrame(queue_rows)
THRESHOLD = 0.80

# ── Sidebar filters ───────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Filters")
    show_mode = st.radio(
        "Show",
        ["Needs review (< 80%)", "All fields", "Approved", "Rejected"],
    )
    selected_asset = st.multiselect(
        "Asset class",
        df_all["asset_class"].unique().tolist(),
        default=df_all["asset_class"].unique().tolist(),
    )
    st.divider()

    total = len(df_all)
    needs_review = (df_all["confidence"] < THRESHOLD).sum()
    approved = sum(1 for v in st.session_state.decisions.values() if v == "approved")
    rejected = sum(1 for v in st.session_state.decisions.values() if v == "rejected")

    st.metric("Total fields", total)
    st.metric("Needs review", needs_review)
    st.metric("Approved", approved)
    st.metric("Rejected", rejected)

    progress = (approved + rejected) / max(needs_review, 1)
    st.progress(progress, text=f"Review progress: {progress:.0%}")

    if approved + rejected == needs_review and needs_review > 0:
        if st.button("🚀  Commit approved to Delta Lake", type="primary", use_container_width=True):
            st.session_state["committed"] = True

# ── Filter data ───────────────────────────────────────────────────────────────

df_filtered = df_all[df_all["asset_class"].isin(selected_asset)]

if show_mode == "Needs review (< 80%)":
    df_filtered = df_filtered[df_filtered["confidence"] < THRESHOLD]
elif show_mode == "Approved":
    keys = {(k[0], k[1]) for k, v in st.session_state.decisions.items() if v == "approved"}
    df_filtered = df_filtered[df_filtered.apply(lambda r: (r["pdf"], r["field"]) in keys, axis=1)]
elif show_mode == "Rejected":
    keys = {(k[0], k[1]) for k, v in st.session_state.decisions.items() if v == "rejected"}
    df_filtered = df_filtered[df_filtered.apply(lambda r: (r["pdf"], r["field"]) in keys, axis=1)]

df_filtered = df_filtered.sort_values("confidence")

# ── Review rows ───────────────────────────────────────────────────────────────

if df_filtered.empty:
    st.info("No items to show for the current filter.")
else:
    for _, row in df_filtered.iterrows():
        key = (row["pdf"], row["field"])
        decision = st.session_state.decisions.get(key)

        conf = row["confidence"]
        if conf >= 0.9:
            badge = "🟢"
        elif conf >= 0.7:
            badge = "🟡"
        else:
            badge = "🔴"

        border_color = "#2e7d32" if decision == "approved" else "#c62828" if decision == "rejected" else "#555"
        with st.container(border=True):
            top_left, top_right = st.columns([5, 2])
            with top_left:
                st.markdown(
                    f"**{row['field']}** &nbsp; `{row['broker']}` &nbsp; `{row['market']}` &nbsp; `{row['asset_class']}`"
                )
            with top_right:
                st.markdown(f"{badge} Confidence: **{conf:.0%}**")

            val_col, quote_col = st.columns([2, 4])
            with val_col:
                edited = st.session_state.edits.get(key, row["value"])
                new_val = st.number_input(
                    f"Value ({row['unit']})",
                    value=float(edited) if isinstance(edited, (int, float)) else float(row["value"]),
                    key=f"val_{key}",
                    label_visibility="visible",
                )
                if new_val != row["value"]:
                    st.session_state.edits[key] = new_val

            with quote_col:
                if row["quote"]:
                    st.markdown(f"**Source quote** (p. {row['page']}):")
                    st.markdown(f"> {row['quote']}")
                else:
                    st.caption("No source quote available — value may come from a chart or image.")

            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
            with btn_col1:
                if st.button("✅ Approve", key=f"approve_{key}", type="primary" if decision != "approved" else "secondary"):
                    st.session_state.decisions[key] = "approved"
                    st.rerun()
            with btn_col2:
                if st.button("❌ Reject", key=f"reject_{key}"):
                    st.session_state.decisions[key] = "rejected"
                    st.rerun()
            with btn_col3:
                if decision == "approved":
                    st.success("Approved")
                elif decision == "rejected":
                    st.error("Rejected — will not enter production")

# ── Commit confirmation ───────────────────────────────────────────────────────

if st.session_state.get("committed"):
    st.divider()
    approved_rows = [
        row for _, row in df_all.iterrows()
        if st.session_state.decisions.get((row["pdf"], row["field"])) == "approved"
    ]
    if approved_rows:
        st.success(f"**{len(approved_rows)} fields committed to `gold.real_estate_metrics` Delta table.**")
        st.dataframe(
            pd.DataFrame(approved_rows)[["broker", "market", "asset_class", "field", "value", "unit"]],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No approved fields to commit.")
