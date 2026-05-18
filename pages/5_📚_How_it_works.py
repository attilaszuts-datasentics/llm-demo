"""
How it works — reference guide for the workshop.
Prompting, validation, pipeline wiring, experimentation, gotchas, and doc links.
"""
import streamlit as st

st.set_page_config(page_title="How it works", layout="wide", page_icon="📚")

st.title("📚 How it works")
st.caption("Reference guide — skimmable companion to the demos. Come back to this after the session.")
st.divider()

tabs = st.tabs([
    "✍️  Prompting",
    "✅  Validation",
    "⚙️  Pipeline",
    "🧪  Experimentation",
    "⚠️  Gotchas",
    "🔗  Docs & links",
])

# ── Tab 1: Prompting ──────────────────────────────────────────────────────────

with tabs[0]:
    st.markdown("## Prompting for structured extraction")
    st.markdown("The biggest lever is *how* you ask. Small changes in prompt structure can swing accuracy by 20–30 percentage points.")

    c1, c2 = st.columns(2)

    with c1:
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
            }
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

    with c2:
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
 If you cannot find the value, omit the field."
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
  Output: {"prime_yield": {"value": 4.25, "quote": "Prime yields for
           high-street retail compressed to 4.25%", "page": 1}}
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

    c1, c2 = st.columns(2)

    with c1:
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

        Add these as validators or post-processing rules.
        """)

    with c2:
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
        Flag large deviations for review — they're almost always errors.
        """)
        st.code("""
def plausibility_check(current, previous, field, max_delta):
    if previous is None:
        return True
    delta = abs(current - previous)
    return delta <= max_delta

# Example: flag yield changes > 1 percentage point
plausibility_check(5.0, 4.9, "prime_yield", max_delta=1.0)
""", language="python")

        st.markdown("### 6 — Confidence threshold gating")
        st.info("""
        **The key pattern:** don't try to fix every extraction.
        Instead, set a confidence threshold and route anything below it to a human review queue.
        High-confidence → auto-approve. Low-confidence → human checks.
        This keeps the automation fast while ensuring data quality.
        """)

# ── Tab 3: Pipeline ───────────────────────────────────────────────────────────

with tabs[2]:
    st.markdown("## Building the pipeline")

    c1, c2 = st.columns(2)

    with c1:
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
# Workflow with three tasks:
# Task 1 — ingest_and_preprocess
#   Reads from Blob, calls Doc Intelligence, writes Bronze Delta table
# Task 2 — extract_and_validate (depends on task 1)
#   Reads Bronze, calls Azure OpenAI, validates, writes Silver + review queue
# Task 3 — promote_approved (depends on task 2, or triggered by review)
#   Merges approved rows from review queue into Gold table

# Each task is a Databricks notebook or Python wheel.
# Schedule: daily at 08:00 or triggered by new blob arrival.
""", language="python")

    with c2:
        st.markdown("### Bronze / Silver / Gold for extractions")
        st.code("""
# Bronze — raw LLM response, exactly as returned
CREATE TABLE bronze.extractions (
    pdf_name        STRING,
    run_id          STRING,
    extracted_at    TIMESTAMP,
    raw_json        STRING,   -- full LLM response
    model_version   STRING
) USING DELTA;

# Silver — parsed, typed, one row per field
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

# Gold — approved, ready for analytics
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

        st.markdown("### Idempotency")
        st.markdown("""
        Running the same report twice should not create duplicates.
        Use `MERGE INTO` (Delta Lake upsert) keyed on `(pdf_name, field_name)`.
        Store a hash of the PDF content — if it hasn't changed, skip re-extraction.
        """)
        st.code("""
MERGE INTO silver.extraction_fields AS target
USING new_extractions AS source
ON target.pdf_name = source.pdf_name
   AND target.field_name = source.field_name
WHEN MATCHED AND source.confidence > target.confidence
  THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
""", language="sql")

# ── Tab 4: Experimentation ────────────────────────────────────────────────────

with tabs[3]:
    st.markdown("## Experimentation & iteration")
    st.markdown("Treat prompt engineering as an experiment, not a one-shot task. The first prompt is never the best one.")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Build a ground truth set first")
        st.markdown("""
        Before writing a single prompt, manually annotate 20–30 reports.
        Record the correct value, unit, page number, and source quote for each field.
        This is your eval set — you'll run every prompt version against it.

        Without ground truth you're guessing whether a change made things better.
        """)

        st.markdown("### What to measure")
        st.markdown("""
        - **Field accuracy** — % of fields with the correct value (within ±0.1%)
        - **Quote verification rate** — % of quotes found verbatim in the document
        - **Hallucination rate** — % of fields where the model returned a value not in the document
        - **Coverage** — % of fields successfully extracted (vs. omitted)
        - **Schema pass rate** — % of extractions that pass all validators
        """)

        st.markdown("### Track with MLflow")
        st.code("""
import mlflow

with mlflow.start_run(run_name="prompt_v3_with_citations"):
    mlflow.log_param("model", "claude-haiku-4-5")
    mlflow.log_param("temperature", 0)
    mlflow.log_param("prompt_version", "v3")
    mlflow.log_param("strategy", "table_first + grounded")

    # Run on ground truth set
    results = evaluate_on_ground_truth(prompt_v3, ground_truth)

    mlflow.log_metric("field_accuracy", results["accuracy"])
    mlflow.log_metric("quote_verification_rate", results["quote_rate"])
    mlflow.log_metric("hallucination_rate", results["hallucination_rate"])
    mlflow.log_metric("schema_pass_rate", results["schema_pass_rate"])
""", language="python")

    with c2:
        st.markdown("### What to iterate on (in order)")
        st.markdown("""
        1. **Field definitions** — are units explicit? are field names unambiguous?
        2. **Few-shot examples** — add one example per field that regularly fails
        3. **Pre-processing** — is Doc Intelligence helping or are you sending raw text?
        4. **Chunking** — are you losing data at chunk boundaries?
        5. **Model size** — try a larger model only after optimizing the prompt
        6. **Self-consistency** — if a field is noisy, run it 3× instead of 1×
        """)

        st.markdown("### Per-field analysis")
        st.markdown("""
        Aggregate accuracy by field, not just overall. You'll usually find:
        - 2–3 fields that are always right (vacancy rate, take-up — clearly labelled)
        - 2–3 fields that regularly fail (prime rent units, transaction volume scale)

        Focus effort on the failing fields. Don't re-engineer what's already working.
        """)

        st.markdown("### Use the hardest reports for development")
        st.warning("""
        Develop on the *worst* reports in your corpus (image-heavy, multilingual, unusual layout).
        A prompt that works on clean Savills-style tables will almost certainly work on them too.
        The reverse is not true.
        """)

        st.markdown("### Register the winning prompt")
        st.markdown("""
        Once you have a prompt version that beats the baseline on your eval set,
        register it as an MLflow model artifact. This gives you versioning,
        rollback, and an audit trail of which prompt was running in production and when.
        """)

# ── Tab 5: Gotchas ────────────────────────────────────────────────────────────

with tabs[4]:
    st.markdown("## Gotchas — things that will bite you in production")

    items = [
        (
            "⚠️ Hallucinated plausible values",
            """
            The model's worst failure mode is returning a number that looks right but isn't in the document.
            It fills in what it expects to find, not what's there.
            **Mitigation:** always require a source quote. If the quote isn't in the document, the value is suspect.
            Never ship to production without citation verification.
            """,
        ),
        (
            "⚠️ Unit confusion — a silent 12× error",
            """
            `€235/sqm/month` and `€2,820/sqm/year` are the same number.
            The model will often return one when the source says the other,
            especially if your prompt doesn't specify the target unit explicitly.
            This passes schema validation (both are plausible rents) and only surfaces when you compare across reports.
            **Mitigation:** specify the target unit in the field description. Validate against a known range for that unit.
            """,
        ),
        (
            "⚠️ Prior-year figures",
            """
            Reports frequently quote last year's figure for comparison: "vs 7.4% in Q1 2024".
            The model sometimes picks up the comparison figure instead of the current one.
            **Mitigation:** include the target period in the prompt ("extract Q1 2025 figures only").
            Check extracted values against `period` metadata.
            """,
        ),
        (
            "⚠️ German decimal commas",
            """
            `5,00%` in German means 5.00%, not 500%.
            The model usually handles this correctly, but regex-based pre-processing won't.
            **Mitigation:** detect document language (Doc Intelligence returns it) and adjust numeric parsing accordingly.
            """,
        ),
        (
            "⚠️ Data only in charts",
            """
            If a number appears exclusively in a chart image — not in any caption or table —
            text extraction returns nothing. The model will either omit the field (good) or hallucinate (bad).
            **Mitigation:** use Doc Intelligence's figure extraction (available in the layout model).
            Or flag image-heavy PDFs and route them to manual entry.
            """,
        ),
        (
            "⚠️ 'It worked on 3 reports' ≠ production-ready",
            """
            Every broker will eventually change their template.
            A new quarter brings a redesigned report.
            Rule-based extraction breaks immediately. LLM-based extraction degrades gracefully but still degrades.
            **Mitigation:** monitor extraction quality per-broker over time (MLflow metrics per run).
            Set up alerts when schema pass rate drops below a threshold.
            """,
        ),
        (
            "⚠️ High confidence ≠ correct",
            """
            Self-consistency confidence measures *agreement*, not *accuracy*.
            If the model consistently picks up the wrong value (e.g. always grabs last year's figure),
            confidence will be high and the value will still be wrong.
            **Mitigation:** confidence gating reduces noise but doesn't replace ground-truth evaluation.
            Maintain your eval set and re-run it whenever you change the prompt or model.
            """,
        ),
        (
            "⚠️ Token limits truncate long reports",
            """
            An 8-page report with charts, tables, and full-page images can exceed
            the context window when converted to text.
            Data on page 6 is never seen — and the model won't tell you.
            **Mitigation:** extract page by page and merge, or log token usage per call
            and alert when a document is near-truncated.
            """,
        ),
    ]

    for title, body in items:
        with st.expander(title):
            st.markdown(body.strip())

# ── Tab 6: Docs & links ───────────────────────────────────────────────────────

with tabs[5]:
    st.markdown("## Documentation & reference links")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Azure AI services")
        st.markdown("""
**Azure Document Intelligence**
- [Overview](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview)
- [Layout model (tables & key-value pairs)](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-layout)
- [Confidence scores explained](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-confidence)
- [Python SDK quickstart](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api?pivots=programming-language-python)

**Azure OpenAI / Azure AI Foundry**
- [Overview](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview)
- [Structured outputs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs)
- [Function calling / tool use](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/function-calling)
- [Prompt engineering guide](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/prompt-engineering)
- [JSON mode](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/json-mode)

**Azure Blob Storage**
- [Blob Storage docs](https://learn.microsoft.com/en-us/azure/storage/blobs/)
- [Blob trigger for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob-trigger)
""")

    with col2:
        st.markdown("### Databricks")
        st.markdown("""
**Delta Lake**
- [Delta Lake docs](https://www.databricks.com/aws/en/delta/)
- [MERGE INTO (upsert)](https://docs.delta.io/latest/delta-update.html)
- [Table constraints](https://docs.delta.io/latest/delta-constraints.html)

**MLflow**
- [MLflow docs](https://mlflow.org/docs/latest/index.html)
- [Tracking experiments](https://mlflow.org/docs/latest/tracking.html)
- [Model registry](https://mlflow.org/docs/latest/model-registry.html)
- [Databricks MLflow integration](https://www.databricks.com/aws/en/mlflow/)

**Databricks AI/BI**
- [Genie — AI/BI natural language queries](https://www.databricks.com/aws/en/genie/)
- [Databricks Workflows](https://learn.microsoft.com/en-us/azure/databricks/jobs/)
- [Unity Catalog](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/)
- [LLM serving on Databricks](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/)
""")

    with col3:
        st.markdown("### Libraries used in this demo")
        st.markdown("""
**PDF processing**
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) — rendering, text search, annotations
- [pdfplumber](https://github.com/jsvine/pdfplumber) — table extraction

**Validation**
- [Pydantic v2](https://docs.pydantic.dev/latest/) — schema validation and field validators

**LLM SDKs**
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [OpenAI Python SDK](https://github.com/openai/openai-python) — same API surface for Azure OpenAI

**Further reading**
- [BAML — structured LLM outputs](https://docs.boundaryml.com/)
- [Instructor — Pydantic + LLMs](https://python.useinstructor.com/)
- [LangChain document loaders](https://python.langchain.com/docs/how_to/#document-loaders)
- [Azure AI Document Intelligence Studio](https://documentintelligence.ai.azure.com/) — test your PDFs interactively
""")

    st.divider()
    st.caption("Links verified May 2026. Azure OpenAI docs have moved to the Azure AI Foundry path (`/azure/foundry/openai/`). Databricks docs moved from `docs.databricks.com` to `www.databricks.com/aws/en/`.")
