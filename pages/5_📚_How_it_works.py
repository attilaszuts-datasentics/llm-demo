"""
How it works — reference guide for the workshop.
Prompting, validation, pipeline wiring, experimentation, gotchas, and doc links.
"""
import streamlit as st
from ui import brand_sidebar, brand_footer

st.set_page_config(page_title="How it works", layout="wide", page_icon="assets/DS_favicon_color.svg")
brand_sidebar()

st.title("How it works")
st.caption("Reference guide — skimmable companion to the demos. Come back to this after the session.")
st.divider()

tabs = st.tabs([
    "Prompting",
    "Validation",
    "Pipeline",
    "Experimentation",
    "Gotchas",
    "Docs & links",
])

# ── Tab 1: Prompting ──────────────────────────────────────────────────────────

with tabs[0]:
    st.markdown("## Prompting for structured extraction")
    st.markdown("The biggest lever is *how* you ask. Small changes in prompt structure can swing accuracy by 20–30 percentage points.")

    st.markdown("### Use tool/function calling, not free JSON")
    st.markdown("""
    Asking the model to "return JSON" produces fragile output — it may add prose,
    wrap it in markdown fences, or skip fields silently.
    Tool calling forces the schema at the API level: the model *must* return
    the exact fields you declared, typed correctly.
    """)
    st.code("""
# With Anthropic SDK
tools = [{
    "name": "extract_metrics",
    "input_schema": {
        "type": "object",
        "properties": {
            "vacancy_rate": {
                "type": "number",
                "description": "Vacancy rate in %, e.g. 7.0"
            },
            "prime_yield": {
                "type": "number",
                "description": "Prime yield in %, e.g. 4.25"
            },
        },
        "required": ["vacancy_rate", "prime_yield"]
    }
}]

client.messages.create(
    model="claude-haiku-4-5-20251001",
    tools=tools,
    tool_choice={"type": "tool", "name": "extract_metrics"},
    messages=[{"role": "user", "content": text}]
)
""", language="python")

    st.markdown("### Force citations")
    st.markdown("""
    Add a `quote` field to every numeric field.
    Instruct the model to copy the *exact* sentence from the source.
    You can then verify the quote exists in the document — a strong signal that the value is real.
    """)
    st.code("""
"prime_yield": {
    "type": "object",
    "properties": {
        "value":  {"type": "number"},
        "quote":  {"type": "string",
                   "description": "Exact verbatim sentence from the text"},
        "page":   {"type": "integer"}
    }
}
""", language="json")

    st.markdown("### Specify units explicitly")
    st.markdown("""
    Never leave units implicit. Different brokers write the same number differently:
    `5,00%` / `500 bps` / `5.0 per cent` / `5 pct`. Tell the model what unit to normalise to.
    """)
    st.code("""
"Extract prime_yield as a percentage float.
 Examples of how it may appear in the text:
   '5,00%'  →  5.0
   '500 bps'  →  5.0
   '5.0 per cent'  →  5.0
 If you cannot find the value, omit the field — do not guess."
""", language="text")

    st.markdown("### Few-shot examples improve consistency")
    st.markdown("""
    One well-chosen example in the system prompt significantly reduces
    unit errors and field confusion. Use a real excerpt from a known-good report.
    """)
    st.code("""
system = \"\"\"
You extract real estate metrics from market reports.

Example:
  Text: "Prime yields for high-street retail compressed to 4.25%"
  Output: {"prime_yield": {"value": 4.25,
            "quote": "Prime yields for high-street retail compressed to 4.25%",
            "page": 1}}
\"\"\"
""", language="python")

    st.markdown("### Keep temperature low")
    st.info("Set `temperature=0` for extraction. You want the most likely answer, not a creative one. Randomness is the enemy of determinism.")

    st.markdown("### Chunk long documents")
    st.markdown("""
    Most extraction models have an 8k–128k token context window.
    For long reports, extract page by page and merge results.
    Page-level extraction also gives you exact page numbers for free.
    """)

# ── Tab 2: Validation ─────────────────────────────────────────────────────────

with tabs[1]:
    st.markdown("## Validation techniques")
    st.markdown("Validation is what separates a demo from a production system. Layer multiple checks — each catches different failure modes.")

    st.markdown("### 1 — Schema validation (Pydantic)")
    st.markdown("Define expected types and value ranges. Catches unit errors (42.5% instead of 4.25%) and impossible values before they reach the database.")
    st.code("""
from pydantic import BaseModel, field_validator

class ReportMetrics(BaseModel):
    prime_yield: float | None = None
    vacancy_rate: float | None = None
    period: str

    @field_validator("prime_yield")
    @classmethod
    def yield_range(cls, v):
        if v is not None and not (0.5 <= v <= 20.0):
            raise ValueError(f"yield {v}% outside 0.5–20%")
        return v

    @field_validator("period")
    @classmethod
    def period_format(cls, v):
        import re
        if not re.match(r"Q[1-4] 20\\d\\d", v):
            raise ValueError(f"period '{v}' not Q1 2025 format")
        return v
""", language="python")

    st.markdown("### 2 — Citation verification")
    st.markdown("Search for the quote string in the document text. If it's not there, the model paraphrased or invented it.")
    st.code("""
import re

def verify_quote(quote: str, full_text: str) -> bool:
    needle = re.sub(r"\\s+", " ", quote.lower().strip())[:60]
    haystack = re.sub(r"\\s+", " ", full_text.lower())
    return needle in haystack
""", language="python")

    st.markdown("### 3 — Cross-field checks")
    st.markdown("""
    Some field combinations are logically impossible:
    - Net take-up > gross take-up
    - Vacancy rate > 100%
    - Completions > total stock

    Add these as post-processing rules after the Pydantic pass.
    """)

    st.markdown("### 4 — Self-consistency confidence")
    st.markdown("Run the extraction N times independently (temperature > 0). Agreement across runs is a strong proxy for confidence.")
    st.code("""
def self_consistency(text, n=3):
    results = [extract(text) for _ in range(n)]
    confidence = {}
    for field in ["prime_yield", "vacancy_rate"]:
        values = [r[field] for r in results if r.get(field)]
        if values:
            top = max(set(str(v) for v in values),
                      key=lambda x: [str(v) for v in values].count(x))
            confidence[field] = [str(v) for v in values].count(top) / n
    return confidence
""", language="python")

    st.markdown("### 5 — Historical plausibility")
    st.markdown("""
    Compare against the previous quarter's value if you have it.
    Prime yields don't move 200bps in a quarter.
    Flag large deviations for review — they're almost always extraction errors, not real market moves.
    """)
    st.code("""
def plausibility_check(current, previous, max_delta):
    if previous is None:
        return True
    return abs(current - previous) <= max_delta

# Flag yield changes > 1 percentage point quarter-on-quarter
ok = plausibility_check(current=5.0, previous=4.9, max_delta=1.0)
""", language="python")

    st.markdown("### 6 — Confidence threshold gating")
    st.info("""
    **The key pattern:** don't try to fix every extraction in code.
    Set a threshold and route anything below it to a human review queue.
    High-confidence → auto-approve. Low-confidence → human checks.
    This keeps the automation fast while ensuring data quality at the edges.
    """)

# ── Tab 3: Pipeline ───────────────────────────────────────────────────────────

with tabs[2]:
    st.markdown("## Building the pipeline")

    st.markdown("### The stages")
    st.markdown("""
    **1. Ingest** — PDF lands in Azure Blob Storage. A trigger (Blob trigger on Azure Function,
    or a Databricks Workflow watching the container) fires the pipeline.

    **2. Pre-process** — Azure Document Intelligence analyzes the layout.
    Use the `prebuilt-layout` model for general reports, or train a custom model
    if you have a consistent format. Output: structured tables + key-value pairs + raw text.

    **3. Extract** — Send the Doc Intelligence output + raw text to Azure OpenAI.
    Use tool calling with a schema that matches your target Delta table columns.
    Force citations for every numeric field.

    **4. Validate** — Run Pydantic validators, verify quotes, check cross-field logic.
    Compute a per-field confidence score (from self-consistency or Doc Intelligence confidence).

    **5. Route** — Fields above your confidence threshold write directly to Silver.
    Fields below go to a review queue table (also Delta) for human sign-off.

    **6. Promote** — Approved fields merge into the Gold table.
    Rejected fields are logged with reason for reprocessing or manual entry.
    """)

    st.markdown("### Databricks Workflows approach")
    st.code("""
# Three tasks, each a notebook or Python wheel:

# Task 1 — ingest_and_preprocess
#   Mount Azure Blob, call Doc Intelligence, write Bronze Delta table

# Task 2 — extract_and_validate  (depends on task 1)
#   Read Bronze, call Azure OpenAI, validate, write Silver + review_queue tables

# Task 3 — promote_approved  (depends on task 2, or triggered after human review)
#   MERGE approved rows from review_queue into Gold table

# Schedule: daily 08:00, or event-triggered on new blob arrival
""", language="python")

    st.markdown("### Bronze / Silver / Gold for extractions")
    st.code("""
-- Bronze: raw LLM response, untouched
CREATE TABLE bronze.extractions (
    pdf_name        STRING,
    run_id          STRING,
    extracted_at    TIMESTAMP,
    raw_json        STRING,
    model_version   STRING
) USING DELTA;

-- Silver: parsed, typed, one row per field
CREATE TABLE silver.extraction_fields (
    pdf_name        STRING,
    field_name      STRING,
    value           DOUBLE,
    unit            STRING,
    confidence      DOUBLE,
    source_quote    STRING,
    source_page     INT,
    validated       BOOLEAN,
    validation_errors STRING
) USING DELTA;

-- Gold: approved, ready for analytics and Genie
CREATE TABLE gold.real_estate_metrics (
    market          STRING,
    asset_class     STRING,
    period          STRING,
    field_name      STRING,
    value           DOUBLE,
    unit            STRING,
    approved_by     STRING,
    approved_at     TIMESTAMP,
    source_pdf      STRING
) USING DELTA;
""", language="sql")

    st.markdown("### Idempotency — running twice should not create duplicates")
    st.markdown("""
    Store a hash of the PDF content. If the file hasn't changed since last run, skip re-extraction.
    For the Delta writes, use `MERGE INTO` keyed on `(pdf_name, field_name)`.
    """)
    st.code("""
MERGE INTO silver.extraction_fields AS target
USING new_extractions AS source
ON  target.pdf_name   = source.pdf_name
AND target.field_name = source.field_name
WHEN MATCHED AND source.confidence > target.confidence
    THEN UPDATE SET *
WHEN NOT MATCHED
    THEN INSERT *;
""", language="sql")

# ── Tab 4: Experimentation ────────────────────────────────────────────────────

with tabs[3]:
    st.markdown("## Experimentation & iteration")
    st.markdown("Treat prompt engineering as an experiment, not a one-shot task. The first prompt is never the best one.")

    st.markdown("### Build a ground truth set first")
    st.markdown("""
    Before writing a single prompt, manually annotate 20–30 reports.
    Record the correct value, unit, page number, and source quote for each field.
    This becomes your eval set — run every prompt version against it.

    Without ground truth you're guessing whether a change made things better or worse.
    """)

    st.markdown("### What to measure")
    st.markdown("""
    - **Field accuracy** — % of fields with the correct value (within ±0.1%)
    - **Quote verification rate** — % of quotes found verbatim in the document
    - **Hallucination rate** — % of fields where the model returned a value absent from the document
    - **Coverage** — % of fields successfully extracted (vs. omitted or null)
    - **Schema pass rate** — % of extractions that pass all Pydantic validators
    """)

    st.markdown("### Track with MLflow")
    st.code("""
import mlflow

with mlflow.start_run(run_name="prompt_v3_citations"):
    mlflow.log_param("model", "claude-haiku-4-5")
    mlflow.log_param("temperature", 0)
    mlflow.log_param("prompt_version", "v3")
    mlflow.log_param("strategy", "table_first + grounded")

    results = evaluate_on_ground_truth(prompt_v3, ground_truth)

    mlflow.log_metric("field_accuracy",          results["accuracy"])
    mlflow.log_metric("quote_verification_rate", results["quote_rate"])
    mlflow.log_metric("hallucination_rate",      results["hallucination_rate"])
    mlflow.log_metric("schema_pass_rate",        results["schema_pass_rate"])
""", language="python")

    st.markdown("### What to iterate on — in this order")
    st.markdown("""
    1. **Field definitions** — are units explicit? are field names unambiguous?
    2. **Few-shot examples** — add one example per field that regularly fails
    3. **Pre-processing** — is Doc Intelligence helping or are you sending raw text?
    4. **Chunking strategy** — are you losing data at page boundaries?
    5. **Model size** — try a larger model only after optimising the prompt
    6. **Self-consistency** — if a field is noisy, run 3× and take the majority answer
    """)

    st.markdown("### Per-field analysis")
    st.markdown("""
    Aggregate accuracy by field, not just overall. You'll typically find:
    - 2–3 fields that are always right (clearly labelled in every report)
    - 2–3 fields that regularly fail (unit ambiguity, buried in prose)

    Focus effort on the failing fields. Don't re-engineer what's already working.
    """)

    st.warning("""
    **Develop on your hardest reports, not your cleanest ones.**
    A prompt that works on a well-structured Savills table will almost certainly
    work on a clean CBRE report too. The reverse is not true.
    """)

    st.markdown("### Register the winning prompt")
    st.markdown("""
    Once a prompt version beats the baseline on your eval set, register it as an MLflow
    model artifact. This gives you versioning, rollback, and an audit trail of which
    prompt was running in production and when.
    """)

# ── Tab 5: Gotchas ────────────────────────────────────────────────────────────

with tabs[4]:
    st.markdown("## Gotchas — things that will bite you in production")

    items = [
        (
            "⚠️ Hallucinated plausible values",
            """The model's worst failure mode: returning a number that *looks* right but isn't in the document.
It fills in what it expects to find, not what's there. A hallucinated vacancy rate is indistinguishable from a real one in the JSON output.

**Mitigation:** always require a source quote and verify it against the document text. If the quote isn't there, the value is suspect. Never ship to production without citation verification.""",
        ),
        (
            "⚠️ Unit confusion — a silent 12× error",
            """€235/sqm/month and €2,820/sqm/year are the same rent. The model will often return one when the source says the other, especially if your prompt doesn't specify the target unit. This passes schema validation and only surfaces when you compare figures across reports.

**Mitigation:** specify the exact target unit in every field description. Validate extracted values against a known plausible range *for that specific unit*.""",
        ),
        (
            "⚠️ Prior-year comparison figures",
            """Reports routinely quote the prior year for context: "vacancy fell to 7.0%, down from 7.4% in Q1 2024".
The model sometimes picks up 7.4% as the current figure.

**Mitigation:** include the target period explicitly in the prompt ("extract Q1 2025 values only, ignore prior-year comparisons"). Cross-check extracted `period` metadata against the expected quarter.""",
        ),
        (
            "⚠️ German decimal commas",
            """`5,00%` in German means 5.00%, not 500%. LLMs usually handle this correctly — regex pre-processing won't.

**Mitigation:** detect document language (Azure Document Intelligence returns it in the response) and adjust any regex-based numeric parsing accordingly. Don't mix regex and LLM normalisation on the same field.""",
        ),
        (
            "⚠️ Data exists only in charts",
            """If a number appears exclusively in a chart image — not in any caption, table, or paragraph — text extraction returns nothing. The model will either omit the field (good) or hallucinate a plausible value (bad).

**Mitigation:** use Azure Document Intelligence's figure/caption extraction available in the layout model. For persistently image-heavy brokers, consider flagging the report type and routing to manual entry.""",
        ),
        (
            '⚠️ "It worked on 3 reports" ≠ production-ready',
            """Every broker will eventually redesign their template. A new quarter brings new layouts. Rule-based extraction breaks immediately. LLM-based extraction degrades more gracefully — but it still degrades.

**Mitigation:** monitor extraction quality per-broker over time using MLflow metrics. Set an alert when schema pass rate or quote verification rate drops below your threshold for any broker.""",
        ),
        (
            "⚠️ High confidence ≠ correct",
            """Self-consistency confidence measures *agreement*, not *accuracy*. If the model consistently picks up the wrong value (e.g. always grabs last year's figure), confidence will be high and the value will still be wrong.

**Mitigation:** confidence gating reduces noise but does not replace ground-truth evaluation. Maintain your eval set and re-run it whenever you change the prompt or switch model versions.""",
        ),
        (
            "⚠️ Token limits silently truncate long reports",
            """A dense 10-page report can exceed the context window when converted to text, especially if tables expand to many tokens. The model processes whatever fits and ignores the rest — without warning you.

**Mitigation:** log token usage per extraction call. Alert when a document is within 20% of the context limit. Switch to page-by-page extraction for long documents.""",
        ),
    ]

    for title, body in items:
        with st.expander(title):
            st.markdown(body)

# ── Tab 6: Docs & links ───────────────────────────────────────────────────────

with tabs[5]:
    st.markdown("## Documentation & reference links")

    st.markdown("### Azure Document Intelligence")
    st.markdown("""
- [Overview](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview)
- [Layout model — tables & key-value pairs](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-layout)
- [Confidence scores explained](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-confidence)
- [Python SDK quickstart](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api?pivots=programming-language-python)
- [Document Intelligence Studio](https://documentintelligence.ai.azure.com/) — test your PDFs interactively without writing code
""")

    st.markdown("### Azure OpenAI / Azure AI Foundry")
    st.markdown("""
- [Overview](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview)
- [Structured outputs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs)
- [Function calling / tool use](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/function-calling)
- [Prompt engineering guide](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/prompt-engineering)
- [JSON mode](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/json-mode)
""")

    st.markdown("### Azure Blob Storage")
    st.markdown("""
- [Blob Storage docs](https://learn.microsoft.com/en-us/azure/storage/blobs/)
- [Blob trigger for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob-trigger)
""")

    st.markdown("### Azure Databricks — Delta Lake")
    st.markdown("""
- [Delta Lake on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/delta/)
- [Delta Lake table constraints](https://learn.microsoft.com/en-us/azure/databricks/delta/delta-constraints)
- [MERGE INTO — upsert](https://learn.microsoft.com/en-us/azure/databricks/delta/merge)
- [Medallion architecture](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
""")

    st.markdown("### Azure Databricks — MLflow")
    st.markdown("""
- [MLflow on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/mlflow/)
- [Track ML experiments](https://learn.microsoft.com/en-us/azure/databricks/mlflow/tracking)
- [MLflow Model Registry](https://learn.microsoft.com/en-us/azure/databricks/mlflow/model-registry)
- [MLflow main docs](https://mlflow.org/docs/latest/index.html)
""")

    st.markdown("### Azure Databricks — AI/BI & Workflows")
    st.markdown("""
- [Databricks AI/BI Genie](https://learn.microsoft.com/en-us/azure/databricks/genie/)
- [Databricks Workflows](https://learn.microsoft.com/en-us/azure/databricks/jobs/)
- [Unity Catalog](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/)
- [LLM / Foundation Model serving](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/)
""")

    st.markdown("### Libraries used in this demo")
    st.markdown("""
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) — PDF rendering, text search, highlight annotations
- [pdfplumber](https://github.com/jsvine/pdfplumber) — table extraction from PDFs
- [Pydantic v2](https://docs.pydantic.dev/latest/) — schema validation and field validators
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude API
- [OpenAI Python SDK](https://github.com/openai/openai-python) — same interface works for Azure OpenAI
""")

    st.markdown("### Further reading")
    st.markdown("""
- [Instructor — Pydantic + LLMs](https://python.useinstructor.com/) — structured outputs library that wraps any LLM
- [BAML — typed LLM functions](https://docs.boundaryml.com/) — alternative approach to enforcing output structure
- [LangChain document loaders](https://python.langchain.com/docs/how_to/#document-loaders) — pre-built connectors for PDF, Word, HTML, etc.
""")

    st.divider()
    st.caption(
        "Links verified May 2026. "
        "Azure OpenAI docs now live under the Azure AI Foundry path (`/azure/foundry/openai/`). "
        "All Databricks links use the Azure Databricks docs (`learn.microsoft.com/en-us/azure/databricks/`)."
    )
