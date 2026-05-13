import re
import pdfplumber


def get_pages(pdf_path: str) -> dict[int, str]:
    with pdfplumber.open(pdf_path) as pdf:
        return {i + 1: (p.extract_text() or "") for i, p in enumerate(pdf.pages)}


def get_tables(pdf_path: str) -> list[dict]:
    result = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            for table in page.extract_tables():
                clean = [r for r in table if any(c for c in r if c)]
                if clean:
                    result.append({"page": i + 1, "rows": clean})
    return result


def full_text(pages: dict[int, str]) -> str:
    return "\n\n".join(f"[PAGE {p}]\n{t}" for p, t in pages.items() if t.strip())


def tables_as_text(tables: list[dict]) -> str:
    lines = []
    for t in tables:
        lines.append(f"\n[TABLE page {t['page']}]")
        for row in t["rows"]:
            lines.append(" | ".join(str(c or "").strip() for c in row))
    return "\n".join(lines)


def verify_quote(quote: str, pages: dict[int, str]) -> bool:
    if not quote or len(quote) < 10:
        return False
    all_text = " ".join(pages.values()).lower()
    # Normalize whitespace before checking
    needle = re.sub(r"\s+", " ", quote.lower().strip())[:60]
    return needle in re.sub(r"\s+", " ", all_text)
