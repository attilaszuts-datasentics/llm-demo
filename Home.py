"""
Workshop landing page — visual intro to the problem and the demos.
Entry point for Streamlit Community Cloud: streamlit run Home.py
"""
import fitz
import streamlit as st
from fixtures import REPORTS
from ui import inject_brand_css, brand_footer, ICON_AZURE, ICON_OPENAI, ICON_DATABRICKS

st.set_page_config(
    page_title="Report Extraction Workshop",
    layout="wide",
    page_icon="assets/DS_favicon_color.svg",
    initial_sidebar_state="collapsed",
)

inject_brand_css()

# ── Thumbnail helper ──────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def thumbnail(pdf_path: str, width_px: int = 200) -> bytes | None:
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        scale = width_px / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        return pix.tobytes("png")
    except Exception:
        return None

# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown("""
<h1 style="font-size:2.6rem; margin-bottom:0.2rem;">
    LLMs for Deterministic Data
</h1>
<p style="font-size:1.2rem; color:#888; margin-top:0;">
    Azure Document Intelligence &nbsp;·&nbsp; Azure OpenAI &nbsp;·&nbsp; Databricks
</p>
""", unsafe_allow_html=True)

st.divider()

# ── Section 1: The real question ──────────────────────────────────────────────

st.markdown("## The question")

col_q, col_gap = st.columns([3, 1])
with col_q:
    st.markdown("""
LLMs are good at generating, summarising, and reasoning — tasks where
**close enough is good enough**. But a large class of real-world problems
needs something different: a specific number, in a specific unit, that can
be traced back to a specific source. Not a paraphrase. Not an approximation.
The actual answer.

This workshop is about that tension — **how do you use LLMs when the output
has to be deterministic, structured, and verifiable?** — and the techniques
that make it work: grounding, validation, self-consistency, and human-in-the-loop review.
""")

st.divider()

# ── Section 2: The concrete example ──────────────────────────────────────────

st.markdown("## A concrete example")

col_text, col_gap = st.columns([3, 1])
with col_text:
    st.markdown("""
Every quarter, real estate teams receive market reports from **10+ brokers**
across multiple markets and asset classes. Someone needs to extract a handful
of KPIs from each one — prime yield, vacancy rate, take-up volume — and
land them in a structured table.

The answer has to be **exactly right**: 7.0%, not 7%, not "around 7", not the
figure from last quarter. And it needs to be traceable — if a number is wrong,
you need to know which page it came from.

This is the problem. The reports below are the actual source material.
""")

# Report thumbnail grid
st.markdown("#### The source material — 7 reports, 4 brokers, 2 languages, 4 asset classes, arriving the same week")

REPORT_META = {
    "CZ_Office_Q12025_Savills.pdf":              ("Savills",             "CZ · Office",      "Clean tables"),
    "AT_Investment_Q12025_Otto.pdf":             ("Otto Immobilien",     "AT · Investment",  "German, 8 pages"),
    "AT_Office_Q12025_VRF.pdf":                  ("Vienna Research Forum","AT · Office",     "Press release"),
    "AT_Retail_Q12025_CBRE.pdf":                 ("CBRE",                "AT · Retail",      "⚠ Image-heavy"),
    "CZ_Retail_Q12025_CW.pdf":                   ("Cushman & Wakefield", "CZ · Retail",      "Landscape layout"),
    "CZ_Investment_Q12025_Knight Frank.pdf":     ("Knight Frank",        "CZ · Investment",  "⚠ Charts only"),
    "CZ_Industrial_Q12025_Colliers.pdf":         ("Colliers",            "CZ · Industrial",  "6 pages"),
}

thumb_cols = st.columns(7)
for col, (pdf_name, (broker, market, note)) in zip(thumb_cols, REPORT_META.items()):
    with col:
        img = thumbnail(pdf_name, width_px=180)
        if img:
            st.image(img, use_container_width=True)
        warn = note.startswith("⚠")
        st.markdown(
            f"<div style='font-size:0.72rem; font-weight:600; margin-top:4px;'>{broker}</div>"
            f"<div style='font-size:0.68rem; color:#888;'>{market}</div>"
            f"<div style='font-size:0.68rem; color:{'#d97706' if warn else '#888'};'>{note}</div>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Section 3: Why LLMs alone aren't enough ──────────────────────────────────

st.markdown("## Why LLMs alone aren't enough")

c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.markdown("### Probabilistic by nature")
        st.markdown("""
        Ask the same question twice, get slightly different answers.
        For a summary that's fine. For a yield that feeds a pricing model,
        it isn't. You need to know when to trust the output — and when not to.
        """)
with c2:
    with st.container(border=True):
        st.markdown("### They hallucinate")
        st.markdown("""
        If the information isn't clearly in the text, the model will often
        invent a plausible-sounding value rather than say it doesn't know.
        A hallucinated vacancy rate looks identical to a real one in the output.
        """)
with c3:
    with st.container(border=True):
        st.markdown("### No citations by default")
        st.markdown("""
        A number without a source is unverifiable. If an extracted figure is
        wrong, you can't tell whether the model misread the document, picked
        up a figure from the wrong year, or made it up entirely.
        """)

st.divider()

# ── Section 3: The solution ───────────────────────────────────────────────────

st.markdown("## Making LLMs deterministic enough")
st.markdown(
    "The answer isn't to avoid LLMs — it's to wrap them with structure. "
    "Force citations. Validate outputs against a schema. Run extraction multiple times and measure agreement. "
    "Gate anything uncertain behind a human. The pipeline below is what that looks like in practice."
)

st.markdown("""
<style>
.pipe-box {
    border-radius: 10px;
    padding: 14px 10px;
    text-align: center;
    color: white;
    font-size: 0.82rem;
    line-height: 1.5;
    height: 90px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.pipe-arrow {
    font-size: 1.6rem;
    color: #888;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 90px;
}
</style>
""", unsafe_allow_html=True)

steps = [
    ("📄", "PDF Reports",             "Brokers",                "#64748b"),
    ("→",  None, None, None),
    (ICON_AZURE,       "Azure Blob",              "Storage",                "#0078d4"),
    ("→",  None, None, None),
    (ICON_AZURE,       "Doc Intelligence",        "Layout & tables",        "#0078d4"),
    ("→",  None, None, None),
    (ICON_OPENAI,      "Azure OpenAI",            "GPT-4o extraction",      "#107c10"),
    ("→",  None, None, None),
    ("✅", "Human Review",            "Confidence gating",      "#d97706"),
    ("→",  None, None, None),
    (ICON_DATABRICKS,  "Delta Lake",              "Bronze→Silver→Gold",     "#e63946"),
    ("→",  None, None, None),
    (ICON_DATABRICKS,  "Genie",                   "NL queries",             "#e63946"),
]

pipe_cols = st.columns([3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3])
for col, (icon, title, subtitle, color) in zip(pipe_cols, steps):
    with col:
        if title is None:
            st.markdown(f'<div class="pipe-arrow">{icon}</div>', unsafe_allow_html=True)
        else:
            # icon is either an emoji string or an <img> tag
            icon_html = icon if icon.startswith("<") else f'<span style="font-size:1.4rem">{icon}</span>'
            st.markdown(
                f'<div class="pipe-box" style="background:{color};">'
                f'{icon_html}'
                f'<strong>{title}</strong>'
                f'<span style="opacity:0.85">{subtitle}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.divider()

# ── Section 4: Key design choices ────────────────────────────────────────────

st.markdown("## Key design choices")

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown("**Layer the strategies**")
    st.caption("Document Intelligence handles layout so the LLM doesn't have to guess structure. Regex pre-scan anchors the search. OpenAI resolves ambiguity.")
with k2:
    st.markdown("**Every value has a source**")
    st.caption("The model is forced to cite the exact sentence it extracted from. If the quote isn't in the document, it's flagged.")
with k3:
    st.markdown("**Confidence gates production**")
    st.caption("High-confidence fields go straight to Gold. Low-confidence go to a review queue. Bad data never reaches the Delta table silently.")
with k4:
    st.markdown("**Analysts query, not SQL**")
    st.caption("Once in Delta Lake, Databricks Genie lets anyone ask questions in plain English — no SQL, no table names, no column mapping.")

st.divider()

# ── Section 5: Demo navigation ────────────────────────────────────────────────

st.markdown("## The demos")
st.caption("Use the sidebar or click below to navigate between demos.")

d1, d2, d3, d4, d5 = st.columns(5)

with d1:
    with st.container(border=True):
        st.markdown("### Pipeline")
        st.markdown("Watch a report travel from raw PDF to validated Delta table, step by step.")
        st.page_link("pages/1_⚙️_Pipeline.py", label="Open demo →")

with d2:
    with st.container(border=True):
        st.markdown("### Compare")
        st.markdown("Four extraction strategies on the same report — see where each one wins and fails.")
        st.page_link("pages/2_🔬_Compare.py", label="Open demo →")

with d3:
    with st.container(border=True):
        st.markdown("### Review")
        st.markdown("Low-confidence extractions surface for analyst sign-off, with the source highlighted in the PDF.")
        st.page_link("pages/3_✅_Review.py", label="Open demo →")

with d4:
    with st.container(border=True):
        st.markdown("### Genie")
        st.markdown("Ask questions about the extracted data in plain English — Genie writes the SQL.")
        st.page_link("pages/4_🧞_Genie.py", label="Open demo →")

with d5:
    with st.container(border=True):
        st.markdown("### How it works")
        st.markdown("Prompting patterns, validation techniques, pipeline wiring, gotchas, and doc links.")
        st.page_link("pages/5_📚_How_it_works.py", label="Open guide →")

brand_footer()
