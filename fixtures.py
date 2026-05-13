"""
Pre-baked realistic data for all 7 PDFs.
Real values from the actual documents — no LLM calls needed for demos.
"""

REPORTS = {
    "CZ_Office_Q12025_Savills.pdf": {
        "broker": "Savills",
        "market": "Prague",
        "asset_class": "Office",
        "period": "Q1 2025",
        "fields": {
            "total_stock_sqm":           {"value": 3_960_000, "unit": "sqm",           "confidence": 0.98},
            "gross_take_up":             {"value": 87_700,    "unit": "sqm",           "confidence": 0.97},
            "net_take_up":               {"value": 47_900,    "unit": "sqm",           "confidence": 0.96},
            "vacancy_rate":              {"value": 7.0,       "unit": "%",             "confidence": 0.99},
            "completions":               {"value": 8_700,     "unit": "sqm",           "confidence": 0.95},
            "under_construction":        {"value": 173_100,   "unit": "sqm",           "confidence": 0.91},
        },
        "quotes": {
            "vacancy_rate":       ("The vacancy rate decreased to 7.0% (278,200 sq m)", 2),
            "gross_take_up":      ("total leasing activity, including renegotiations and subleases, reached 87,700 sq m", 3),
            "net_take_up":        ("Net take-up increased by 5% y-o-y, reaching 47,900 sq m in Q1", 2),
            "total_stock_sqm":    ("the total stock of modern office space in Prague stood at nearly 3.96 million sq m", 2),
        },
        "doc_intelligence_tables": [
            {
                "header": ["Indicator", "Q1 2025", "Q1 2024", "YoY"],
                "rows": [
                    ["Total Stock",    "3.96 mil. sqm", "3.91 mil. sqm", "+1%"],
                    ["Gross Take-Up",  "87,700 sqm",    "101,400 sqm",   "-14%"],
                    ["Net Take-Up",    "47,900 sqm",    "45,700 sqm",    "+5%"],
                    ["Vacancy Rate",   "7.0%",          "7.4%",          "-38 bps"],
                    ["Completions",    "8,700 sqm",     "21,700 sqm",    "-60%"],
                ],
                "page": 1,
                "confidence": 0.97,
            },
        ],
        "validation_issues": [],
    },

    "AT_Investment_Q12025_Otto.pdf": {
        "broker": "Otto Immobilien",
        "market": "Austria",
        "asset_class": "Investment",
        "period": "Q1 2025",
        "fields": {
            "transaction_volume_eur_bn": {"value": 2.9,   "unit": "€ bn",  "confidence": 0.96},
            "prime_yield_office":        {"value": 5.00,  "unit": "%",     "confidence": 0.94},
            "prime_yield_residential":   {"value": 4.50,  "unit": "%",     "confidence": 0.93},
            "prime_yield_logistics":     {"value": 5.00,  "unit": "%",     "confidence": 0.91},
            "prime_yield_office_2025f":  {"value": 4.70,  "unit": "%",     "confidence": 0.82},
        },
        "quotes": {
            "transaction_volume_eur_bn": ("Das gesamte Transaktionsvolumen in Österreich betrug im Jahr 2024 2,9 Milliarden Euro", 2),
            "prime_yield_office":        ("Spitzenrendite Büros 5,00%", 1),
            "prime_yield_residential":   ("Spitzenrendite Wohnen 4,50%", 1),
            "prime_yield_logistics":     ("Spitzenrendite Logistik 5,00%", 1),
        },
        "doc_intelligence_tables": [
            {
                "header": ["Asset Class", "Current Yield", "2025 Forecast"],
                "rows": [
                    ["Office",      "5.00%", "4.70%"],
                    ["Residential", "4.50%", "4.20%"],
                    ["Logistics",   "5.00%", "4.75%"],
                ],
                "page": 1,
                "confidence": 0.89,
            },
        ],
        "validation_issues": [],
    },

    "AT_Office_Q12025_VRF.pdf": {
        "broker": "Vienna Research Forum",
        "market": "Vienna",
        "asset_class": "Office",
        "period": "Q1 2025",
        "fields": {
            "gross_take_up":             {"value": 34_062,  "unit": "sqm",  "confidence": 0.97},
            "vacancy_rate":              {"value": 3.77,    "unit": "%",    "confidence": 0.98},
            "contracts_signed":          {"value": 45,      "unit": "count","confidence": 0.95},
            "new_lettings_sqm":          {"value": 25_843,  "unit": "sqm",  "confidence": 0.93},
            "preletting_sqm":            {"value": 8_220,   "unit": "sqm",  "confidence": 0.90},
        },
        "quotes": {
            "gross_take_up":   ("the letting performance of space on the Vienna office market totalled 34,062 m²", 1),
            "vacancy_rate":    ("Vacancy rate: 3.77%", 1),
            "contracts_signed":("45 contracts signed / 34,062 m²", 1),
        },
        "doc_intelligence_tables": [
            {
                "header": ["Submarket", "Total Area (sqm)", "Vacancy Rate", "Q1 2025 Take-Up"],
                "rows": [
                    ["Inner Districts / CBD", "2,042,805", "3.72%", "11,812"],
                    ["Donaucity",              "530,878",   "2.30%", "1,331"],
                    ["Airport / Surrounding",  "310,400",   "5.10%", "2,840"],
                    ["Other Submarkets",       "890,200",   "4.20%", "8,079"],
                ],
                "page": 2,
                "confidence": 0.94,
            },
        ],
        "validation_issues": [],
    },

    "AT_Retail_Q12025_CBRE.pdf": {
        "broker": "CBRE",
        "market": "Austria",
        "asset_class": "Retail",
        "period": "Q1 2025",
        "fields": {
            "prime_yield":               {"value": 4.75,   "unit": "%",           "confidence": 0.52},
            "prime_rent_high_street":    {"value": 300.0,  "unit": "€/sqm/month", "confidence": 0.48},
            "prime_rent_shopping_centre":{"value": 145.0,  "unit": "€/sqm/month", "confidence": 0.45},
        },
        "quotes": {},
        "doc_intelligence_tables": [],
        "validation_issues": ["Low text density — report is image-heavy. Consider using Document Intelligence layout model for better coverage."],
        "_note": "Mostly image-based PDF — low confidence extraction, good demo of limitations",
    },

    "CZ_Retail_Q12025_CW.pdf": {
        "broker": "Cushman & Wakefield",
        "market": "Czech Republic",
        "asset_class": "Retail",
        "period": "Q1 2025",
        "fields": {
            "prime_yield":               {"value": 4.25,   "unit": "%",            "confidence": 0.99},
            "prime_rent":                {"value": 235.0,  "unit": "€/sqm/month",  "confidence": 0.99},
            "gdp_growth":                {"value": 1.9,    "unit": "%",            "confidence": 0.97},
            "unemployment_rate":         {"value": 2.6,    "unit": "%",            "confidence": 0.97},
            "avg_monthly_wage_eur":      {"value": 1_953,  "unit": "€/month",      "confidence": 0.96},
        },
        "quotes": {
            "prime_yield":   ("4.25% Prime Yield — Prime rent and yield for High Street units", 1),
            "prime_rent":    ("€235.00 Prime Rent, sq m/month", 1),
            "gdp_growth":    ("1.9% GDP Growth*", 1),
            "unemployment_rate": ("2.6% Unemployment Rate", 1),
        },
        "doc_intelligence_tables": [
            {
                "header": ["Indicator", "Value", "YoY Change", "12-Month Forecast"],
                "rows": [
                    ["Prime Rent (sqm/month)",  "€235.00", "↑",  "Stable"],
                    ["Prime Yield",             "4.25%",   "→",  "Stable"],
                    ["GDP Growth",              "1.9%",    "↑",  "Positive"],
                    ["Unemployment Rate",       "2.6%",    "→",  "Stable"],
                    ["Average Monthly Wage",    "€1,953",  "↑",  "Positive"],
                ],
                "page": 1,
                "confidence": 0.99,
            },
        ],
        "validation_issues": [],
    },

    "CZ_Investment_Q12025_Knight Frank.pdf": {
        "broker": "Knight Frank",
        "market": "Czech Republic",
        "asset_class": "Investment",
        "period": "Q1 2025",
        "fields": {
            "prime_yield_office":        {"value": 5.25,  "unit": "%",  "confidence": 0.71},
            "prime_yield_high_street":   {"value": 4.50,  "unit": "%",  "confidence": 0.68},
            "prime_yield_shopping_ctr":  {"value": 6.00,  "unit": "%",  "confidence": 0.65},
            "prime_yield_industrial":    {"value": 5.50,  "unit": "%",  "confidence": 0.63},
        },
        "quotes": {},
        "doc_intelligence_tables": [],
        "validation_issues": ["Chart-heavy PDF — values read from chart axes, higher uncertainty."],
        "_note": "Mostly charts — low confidence, good demo of limitations",
    },

    "CZ_Industrial_Q12025_Colliers.pdf": {
        "broker": "Colliers",
        "market": "Czech Republic",
        "asset_class": "Industrial",
        "period": "Q1 2025",
        "fields": {
            "total_stock_sqm":           {"value": 12_400_000, "unit": "sqm",           "confidence": 0.98},
            "vacancy_rate":              {"value": 3.1,        "unit": "%",             "confidence": 0.97},
            "new_supply_sqm":            {"value": 155_900,    "unit": "sqm",           "confidence": 0.96},
            "gross_take_up":             {"value": 511_600,    "unit": "sqm",           "confidence": 0.97},
            "under_construction":        {"value": 1_617_800,  "unit": "sqm",           "confidence": 0.93},
            "prime_rent_min":            {"value": 7.00,       "unit": "€/sqm/month",   "confidence": 0.95},
            "prime_rent_max":            {"value": 7.50,       "unit": "€/sqm/month",   "confidence": 0.95},
        },
        "quotes": {
            "total_stock_sqm":  ("The total stock reached 12.4 million sqm, representing 4.7% growth year-on-year", 2),
            "vacancy_rate":     ("The vacancy rate has seemingly stabilized at 3.1%, where it has been for the third consecutive quarter", 3),
            "gross_take_up":    ("Gross take-up in the first quarter of 2025 exceeded five-year average and was dominated by renegotiations; volume reached 511,600 sqm", 3),
            "prime_rent_min":   ("Prime rent is stable around €7.00 – 7.50", 2),
        },
        "doc_intelligence_tables": [
            {
                "header": ["Metric", "Q1 2025", "FY 2024"],
                "rows": [
                    ["Total Stock",       "12.4 mil. sqm",  "11.8 mil. sqm"],
                    ["Vacancy Rate",      "3.1%",           "1.9%"],
                    ["New Supply",        "155,900 sqm",    "517,900 sqm"],
                    ["Gross Take-Up",     "511,600 sqm",    "1,445,500 sqm"],
                    ["Under Construction","1,617,800 sqm",  "1,255,600 sqm"],
                    ["Prime Rent",        "€7.00–7.50/sqm", "€7.00–7.50/sqm"],
                ],
                "page": 2,
                "confidence": 0.96,
            },
        ],
        "validation_issues": [],
    },
}

# Pre-baked Azure Document Intelligence "API response" structure
def mock_doc_intelligence_response(pdf_name: str) -> dict:
    report = REPORTS.get(pdf_name, {})
    tables = report.get("doc_intelligence_tables", [])
    n_tables = len(tables)
    n_fields = len(report.get("fields", {}))
    has_issues = bool(report.get("validation_issues"))

    return {
        "status": "succeeded",
        "model_id": "prebuilt-layout",
        "pages": [{"page_number": i + 1} for i in range(4)],
        "tables_found": n_tables,
        "key_value_pairs_found": n_fields + 2,
        "overall_confidence": 0.94 if not has_issues else 0.61,
        "language": "de" if "Otto" in pdf_name else "en",
        "tables": tables,
    }


# Pre-baked Azure OpenAI "response" structure
def mock_openai_response(pdf_name: str) -> dict:
    report = REPORTS.get(pdf_name, {})
    extracted = {k: v["value"] for k, v in report.get("fields", {}).items()}
    extracted["market"] = report.get("market")
    extracted["asset_class"] = report.get("asset_class")
    extracted["period"] = report.get("period")
    avg_conf = sum(v["confidence"] for v in report.get("fields", {}).values()) / max(len(report.get("fields", {})), 1)

    return {
        "model": "gpt-4o",
        "usage": {
            "prompt_tokens": 2_840,
            "completion_tokens": 312,
            "total_tokens": 3_152,
        },
        "extracted": extracted,
        "avg_confidence": round(avg_conf, 3),
    }
