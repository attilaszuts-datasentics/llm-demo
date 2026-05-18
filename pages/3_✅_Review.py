"""
Demo 3 — Human Review Queue
Every extraction gets a PDF screenshot with the source highlighted.
Analysts approve, reject, or edit values without leaving this page.

Run: streamlit run demo_review.py
"""
import fitz  # pymupdf
import pandas as pd
import streamlit as st
from fixtures import REPORTS
from ui import brand_sidebar, brand_footer

st.set_page_config(page_title="Review Queue", layout="wide", page_icon="assets/DS_favicon_color.svg")
brand_sidebar()

# ── PDF rendering ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def render_page(pdf_path: str, page_num: int, quote: str) -> tuple[bytes | None, bool]:
    """
    Render PDF page as PNG.
    If quote is found: highlights it and crops to a full-width strip around it.
    If not found: returns the full page at lower zoom.
    """
    try:
        doc = fitz.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            page_num = 1
        page = doc[page_num - 1]

        found = False
        hit_rect = None

        if quote:
            for length in [60, 40, 20]:
                hits = page.search_for(quote[:length].strip())
                if hits:
                    for hit in hits:
                        annot = page.add_highlight_annot(hit)
                        annot.set_colors(stroke=[1, 0.85, 0])
                        annot.update()
                    # Union of all hit rects
                    hit_rect = hits[0]
                    for h in hits[1:]:
                        hit_rect = hit_rect | h
                    found = True
                    break

        if found and hit_rect:
            # Full-width strip centred on the highlight, with generous vertical padding
            pad_y = 60
            clip = fitz.Rect(
                0,
                max(0, hit_rect.y0 - pad_y),
                page.rect.width,
                min(page.rect.height, hit_rect.y1 + pad_y),
            )
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=clip)
        else:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))

        return pix.tobytes("png"), found
    except Exception:
        return None, False

# ── Session state ─────────────────────────────────────────────────────────────

if "decisions" not in st.session_state:
    st.session_state.decisions = {}  # key → {"status": "approved"|"rejected", "value": float|None}

# ── Build queue ───────────────────────────────────────────────────────────────

all_items = []
for pdf_name, report in REPORTS.items():
    for field, meta in report["fields"].items():
        quote_text, quote_page = report["quotes"].get(field, ("", 1))
        all_items.append({
            "pdf": pdf_name,
            "broker": report["broker"],
            "market": report["market"],
            "asset_class": report["asset_class"],
            "field": field,
            "value": meta["value"],
            "unit": meta["unit"],
            "confidence": meta["confidence"],
            "quote": quote_text,
            "page": quote_page if quote_page else 1,
        })

all_items.sort(key=lambda x: x["confidence"])

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Queue filters")
    THRESHOLD = st.slider("Confidence threshold", 0.0, 1.0, 0.80, 0.05,
                          help="Fields below this threshold appear in the queue")
    filter_mode = st.radio("Show", ["Needs review", "All fields", "Approved", "Rejected"])
    asset_filter = st.multiselect(
        "Asset class",
        sorted({r["asset_class"] for r in all_items}),
        default=sorted({r["asset_class"] for r in all_items}),
    )

    st.divider()
    needs_review = [x for x in all_items if x["confidence"] < THRESHOLD]
    decided = st.session_state.decisions
    n_approved = sum(1 for v in decided.values() if v["status"] == "approved")
    n_rejected = sum(1 for v in decided.values() if v["status"] == "rejected")
    n_pending = sum(1 for x in needs_review if (x["pdf"], x["field"]) not in decided)

    st.metric("Needs review", len(needs_review))
    st.metric("Approved", n_approved)
    st.metric("Rejected", n_rejected)
    if needs_review:
        st.progress((n_approved + n_rejected) / len(needs_review),
                    text=f"{n_approved + n_rejected}/{len(needs_review)} reviewed")

    st.divider()
    if n_pending == 0 and needs_review:
        if st.button("🚀  Commit to Delta Lake", type="primary", use_container_width=True):
            st.session_state["committed"] = True

# ── Filter ────────────────────────────────────────────────────────────────────

if filter_mode == "Needs review":
    items = [x for x in all_items if x["confidence"] < THRESHOLD and x["asset_class"] in asset_filter]
elif filter_mode == "Approved":
    items = [x for x in all_items if decided.get((x["pdf"], x["field"]), {}).get("status") == "approved" and x["asset_class"] in asset_filter]
elif filter_mode == "Rejected":
    items = [x for x in all_items if decided.get((x["pdf"], x["field"]), {}).get("status") == "rejected" and x["asset_class"] in asset_filter]
else:
    items = [x for x in all_items if x["asset_class"] in asset_filter]

# ── Header ────────────────────────────────────────────────────────────────────

st.title("Human Review Queue")
st.caption(
    "Every extraction is shown with its source highlighted in the original document. "
    "Approve, reject, or correct the value — without opening the PDF."
)
st.divider()

if not items:
    st.success("Nothing to show for the current filter.")
    st.stop()

# ── Review cards ──────────────────────────────────────────────────────────────

for item in items:
    key = (item["pdf"], item["field"])
    decision = decided.get(key, {})

    conf = item["confidence"]
    badge = "🟢" if conf >= 0.9 else "🟡" if conf >= 0.7 else "🔴"

    with st.container(border=True):
        # ── Card header ───────────────────────────────────────────────────────
        h1, h2 = st.columns([5, 2])
        with h1:
            st.markdown(
                f"**{item['field']}** &nbsp;·&nbsp; "
                f"`{item['broker']}` &nbsp;·&nbsp; "
                f"`{item['market']}` &nbsp;·&nbsp; "
                f"`{item['asset_class']}`"
            )
        with h2:
            status_label = ""
            if decision.get("status") == "approved":
                status_label = "✅ Approved"
            elif decision.get("status") == "rejected":
                status_label = "❌ Rejected"
            st.markdown(f"{badge} **{conf:.0%}** &nbsp; {status_label}")

        # ── Main body: edit on left, PDF on right ─────────────────────────────
        left, right = st.columns([1, 2])

        with left:
            current_val = decision.get("value", item["value"])
            new_val = st.number_input(
                f"Value ({item['unit']})",
                value=float(current_val) if current_val is not None else float(item["value"]),
                key=f"val_{key}",
            )

            b1, b2 = st.columns(2)
            with b1:
                if st.button("✅ Approve", key=f"ok_{key}", type="primary"):
                    st.session_state.decisions[key] = {"status": "approved", "value": new_val}
                    st.rerun()
            with b2:
                if st.button("❌ Reject", key=f"no_{key}"):
                    st.session_state.decisions[key] = {"status": "rejected", "value": None}
                    st.rerun()

            if decision.get("status") == "approved" and decision.get("value") != item["value"]:
                st.info(f"Value corrected: {item['value']} → {decision['value']} {item['unit']}")

        with right:
            img, found = render_page(item["pdf"], item["page"], item["quote"])
            if img:
                caption = (
                    f"Page {item['page']} — quote highlighted"
                    if found
                    else f"Page {item['page']} — quote not found in text layer (image-based PDF)"
                )
                st.caption(caption)
                st.image(img, use_container_width=True)
                if item["quote"]:
                    st.markdown(f"> *\"{item['quote'][:120]}\"*")
            else:
                st.warning("Could not render PDF page.")

# ── Commit view ───────────────────────────────────────────────────────────────

if st.session_state.get("committed"):
    st.divider()
    approved = [
        {**x, "final_value": decided[(x["pdf"], x["field"])]["value"]}
        for x in all_items
        if decided.get((x["pdf"], x["field"]), {}).get("status") == "approved"
    ]
    if approved:
        st.success(f"**{len(approved)} fields written to `gold.real_estate_metrics`**")
        st.dataframe(
            pd.DataFrame(approved)[["broker", "market", "asset_class", "field", "final_value", "unit"]],
            hide_index=True,
            use_container_width=True,
        )
