"""
Report extraction — live demo
Usage: python demo.py [pdf_file]
Default: CZ_Office_Q12025_Savills.pdf
"""
import sys
import time

from pydantic import ValidationError

from schema import ReportMetrics
from strategies import grounded, regex_llm, self_consistency, table_first, vanilla

W = 64


def validate(data: dict) -> tuple[bool, list[str]]:
    flat = {k: v["value"] if isinstance(v, dict) and "value" in v else v for k, v in data.items()}
    try:
        ReportMetrics(**flat)
        return True, []
    except ValidationError as e:
        return False, [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]


def print_section(label: str, data: dict) -> None:
    ok, errors = validate(data)
    status = "✓ VALID" if ok else f"✗  {' | '.join(errors)}"
    print(f"\n{'─' * W}")
    print(f"  {label}")
    print(f"  Validation: {status}")
    print()

    FIELDS = [
        "market", "asset_class", "period",
        "prime_yield", "vacancy_rate",
        "prime_rent", "prime_rent_unit",
        "gross_take_up", "net_take_up", "total_stock_sqm",
        "transaction_volume_eur_bn",
    ]
    for f in FIELDS:
        v = data.get(f)
        if v is None:
            continue
        if isinstance(v, dict):
            val = v.get("value")
            if val is None:
                continue
            if "verified" in v:
                icon = "✓" if v["verified"] else "✗"
                quote = (v.get("quote") or "")[:60]
                print(f"  {f:<26} {val}  [{icon} p.{v.get('page')}] \"{quote}\"")
            elif "confidence" in v:
                bar = "█" * int(v["confidence"] * 10) + "░" * (10 - int(v["confidence"] * 10))
                print(f"  {f:<26} {val}  {bar} {v['confidence']:.0%}  {v['all_values']}")
        else:
            print(f"  {f:<26} {v}")


def run(label: str, fn, pdf: str) -> dict:
    print(f"\n  → {label}...", end="", flush=True)
    t = time.time()
    result = fn(pdf)
    print(f" {time.time() - t:.1f}s")
    return result


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "CZ_Office_Q12025_Savills.pdf"

    print(f"\n{'═' * W}")
    print(f"  REPORT EXTRACTION DEMO")
    print(f"  File: {pdf}")
    print(f"{'═' * W}")

    r1 = run("1. Vanilla LLM", vanilla, pdf)
    print_section("1. VANILLA LLM  — just text → Claude → JSON", r1)

    r2 = run("2. Table-first", table_first, pdf)
    print_section("2. TABLE-FIRST  — parse tables, LLM fills gaps", r2)

    r3 = run("3. Regex + LLM", regex_llm, pdf)
    print_section("3. REGEX + LLM  — anchored candidates, LLM normalizes", r3)

    r4 = run("4. Grounded (citations)", grounded, pdf)
    print_section("4. GROUNDED     — every value has a verifiable source quote", r4)

    r5 = run("5. Self-consistency (3×)", self_consistency, pdf)
    print_section("5. SELF-CONSISTENCY  — confidence from run agreement", r5)

    print(f"\n{'═' * W}\n")

    # ── Schema validation demo: inject a bad value ────────────────────────────
    print(f"{'═' * W}")
    print("  SCHEMA VALIDATION — catching bad extractions")
    print(f"{'═' * W}\n")

    bad = dict(r1)
    bad["prime_yield"] = 42.5      # typo: decimal point off
    bad["vacancy_rate"] = 107.0    # impossible
    bad["period"] = "First quarter 2025"  # wrong format

    ok, errors = validate(bad)
    print("  Injected errors:")
    print("    prime_yield = 42.5  (should be 4.25)")
    print("    vacancy_rate = 107.0  (impossible)")
    print("    period = 'First quarter 2025'  (wrong format)")
    print()
    print(f"  Validation: {'✓ VALID' if ok else '✗ CAUGHT'}")
    for err in errors:
        print(f"    • {err}")
    print(f"\n{'═' * W}\n")
