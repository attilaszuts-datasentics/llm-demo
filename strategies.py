"""
Five extraction strategies for real estate market reports.
Each returns a dict with at minimum: market, asset_class, period.
"""
import json
import re

import anthropic

from schema import EXTRACTION_TOOL, GROUNDED_TOOL
from utils import full_text, get_pages, get_tables, tables_as_text, verify_quote

MODEL = "claude-haiku-4-5-20251001"
_client = None


def _llm() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _call(messages: list, tool, max_tokens=1024) -> dict:
    resp = _llm().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=messages,
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    return {}


# ── Strategy 1: Vanilla LLM ──────────────────────────────────────────────────

def vanilla(pdf_path: str) -> dict:
    """All text → Claude → structured JSON. Baseline."""
    pages = get_pages(pdf_path)
    text = full_text(pages)
    return _call(
        [{"role": "user", "content": f"Extract real estate market metrics from this report.\n\n{text[:8000]}"}],
        EXTRACTION_TOOL,
    )


# ── Strategy 2: Table-first ──────────────────────────────────────────────────

def table_first(pdf_path: str) -> dict:
    """Extract tables with pdfplumber first; LLM fills gaps from prose."""
    pages = get_pages(pdf_path)
    tables = get_tables(pdf_path)
    table_text = tables_as_text(tables)

    prompt = (
        "Extract real estate market metrics. "
        "Prefer values from the structured tables below over the prose text.\n\n"
        f"TABLES:\n{table_text}\n\nFULL TEXT:\n{full_text(pages)[:5000]}"
    )
    return _call([{"role": "user", "content": prompt}], EXTRACTION_TOOL)


# ── Strategy 3: Regex + LLM ──────────────────────────────────────────────────

REGEX_PATTERNS = [
    (r"(?:prime\s+)?yield[^\n]{0,60}?(\d+\.?\d*)\s*%", "yield_candidates"),
    (r"vacancy[^\n]{0,60}?(\d+\.?\d*)\s*%", "vacancy_candidates"),
    (r"(?:prime\s+)?rent[^\n]{0,80}?[€$£]?\s*(\d[\d,\.]+)", "rent_candidates"),
    (r"take.?up[^\n]{0,60}?(\d[\d,\.]+)\s*(?:sq|m²)", "take_up_candidates"),
    (r"(\d[\d,\.]+)\s*(?:million\s+)?sq\s*m[^\n]{0,40}?stock", "stock_candidates"),
    (r"(?:transaction\s+)?volume[^\n]{0,60}?([\d,\.]+)\s*(?:Mrd|Mio|billion|bn|million)", "volume_candidates"),
]


def regex_llm(pdf_path: str) -> dict:
    """Regex anchors find numeric candidates; LLM normalizes and selects."""
    pages = get_pages(pdf_path)
    text = full_text(pages)

    candidates: dict[str, list] = {}
    for pattern, label in REGEX_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            candidates[label] = matches[:4]

    prompt = (
        "Extract real estate market metrics. "
        "A regex pre-scan found these candidate values — use them as anchors:\n"
        f"{json.dumps(candidates, indent=2)}\n\n"
        f"FULL TEXT:\n{text[:7000]}"
    )
    return _call([{"role": "user", "content": prompt}], EXTRACTION_TOOL)


# ── Strategy 4: Grounded (with citations) ────────────────────────────────────

def grounded(pdf_path: str) -> dict:
    """
    Forces LLM to supply a verbatim quote for each value.
    Each numeric field becomes {value, quote, page, verified}.
    """
    pages = get_pages(pdf_path)
    text = full_text(pages)

    raw = _call(
        [{"role": "user", "content": (
            "Extract real estate market metrics. "
            "For every numeric field include the exact verbatim quote from the text "
            "and the page number where you found it.\n\n" + text[:8000]
        )}],
        GROUNDED_TOOL,
        max_tokens=2048,
    )

    result = {
        "market": raw.get("market"),
        "asset_class": raw.get("asset_class"),
        "period": raw.get("period"),
    }
    for field in ["prime_yield", "vacancy_rate", "prime_rent", "gross_take_up", "net_take_up"]:
        entry = raw.get(field)
        if not entry:
            continue
        quote = entry.get("quote", "")
        result[field] = {
            "value": entry.get("value"),
            "quote": quote,
            "page": entry.get("page"),
            "verified": verify_quote(quote, pages),
        }
    return result


# ── Strategy 5: Self-consistency ─────────────────────────────────────────────

def self_consistency(pdf_path: str, n: int = 3) -> dict:
    """
    Runs extraction n times independently.
    Confidence = fraction of runs that agree on the same value.
    """
    pages = get_pages(pdf_path)
    text = full_text(pages)
    messages = [{"role": "user", "content": f"Extract real estate market metrics.\n\n{text[:8000]}"}]

    runs = [_call(messages, EXTRACTION_TOOL) for _ in range(n)]

    result = {
        "market": runs[0].get("market"),
        "asset_class": runs[0].get("asset_class"),
        "period": runs[0].get("period"),
    }

    for field in ["prime_yield", "vacancy_rate", "prime_rent", "gross_take_up", "net_take_up", "transaction_volume_eur_bn"]:
        values = [r[field] for r in runs if r.get(field) is not None]
        if not values:
            continue
        # Round floats to 1dp so near-identical answers count as equal
        normed = [round(v, 1) if isinstance(v, float) else v for v in values]
        counts = {str(v): normed.count(v) for v in normed}
        top_val_str = max(counts, key=counts.__getitem__)
        top_count = counts[top_val_str]
        confidence = top_count / n
        result[field] = {
            "value": values[normed.index(float(top_val_str) if "." in top_val_str else int(top_val_str))],
            "all_values": values,
            "confidence": round(confidence, 2),
            "agreement": "high" if confidence >= 0.67 else "low",
        }

    return result
