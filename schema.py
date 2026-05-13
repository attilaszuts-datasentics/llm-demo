import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReportMetrics(BaseModel):
    market: str = Field(description="City or country, e.g. Prague, Austria")
    asset_class: str = Field(description="Office, Retail, Industrial, or Investment")
    period: str = Field(description="Quarter and year, e.g. Q1 2025")
    prime_yield: Optional[float] = Field(None, description="Prime yield in %")
    vacancy_rate: Optional[float] = Field(None, description="Vacancy rate in %")
    prime_rent: Optional[float] = Field(None, description="Prime rent value")
    prime_rent_unit: Optional[str] = Field(None, description="e.g. €/sqm/month")
    gross_take_up: Optional[int] = Field(None, description="Gross take-up in sqm")
    net_take_up: Optional[int] = Field(None, description="Net take-up in sqm")
    total_stock_sqm: Optional[int] = Field(None, description="Total stock in sqm")
    transaction_volume_eur_bn: Optional[float] = Field(None, description="Transaction volume in € billions")

    @field_validator("prime_yield")
    @classmethod
    def yield_range(cls, v):
        if v is not None and not (0.5 <= v <= 20.0):
            raise ValueError(f"yield {v}% is outside expected range 0.5–20%")
        return v

    @field_validator("vacancy_rate")
    @classmethod
    def vacancy_range(cls, v):
        if v is not None and not (0.0 <= v <= 60.0):
            raise ValueError(f"vacancy {v}% is outside 0–60% range")
        return v

    @field_validator("prime_rent")
    @classmethod
    def rent_range(cls, v):
        if v is not None and not (0 < v < 10_000):
            raise ValueError(f"prime_rent {v} is outside plausible range")
        return v

    @field_validator("period")
    @classmethod
    def period_format(cls, v):
        if v and not re.match(r"Q[1-4]\s*20\d\d", v):
            raise ValueError(f"period '{v}' doesn't match Q1 2025 format")
        return v

    @field_validator("transaction_volume_eur_bn")
    @classmethod
    def volume_range(cls, v):
        if v is not None and not (0 < v < 1_000):
            raise ValueError(f"transaction volume {v}bn is implausible")
        return v


# Tool schema for Claude tool_use calls
EXTRACTION_TOOL = {
    "name": "extract_metrics",
    "description": "Extract real estate market metrics from report text",
    "input_schema": {
        "type": "object",
        "properties": {
            "market": {"type": "string"},
            "asset_class": {"type": "string"},
            "period": {"type": "string"},
            "prime_yield": {"type": "number", "description": "% e.g. 4.25"},
            "vacancy_rate": {"type": "number", "description": "% e.g. 7.0"},
            "prime_rent": {"type": "number"},
            "prime_rent_unit": {"type": "string"},
            "gross_take_up": {"type": "integer", "description": "sqm"},
            "net_take_up": {"type": "integer", "description": "sqm"},
            "total_stock_sqm": {"type": "integer", "description": "sqm"},
            "transaction_volume_eur_bn": {"type": "number", "description": "€ billions"},
        },
        "required": ["market", "asset_class", "period"],
    },
}

GROUNDED_TOOL = {
    "name": "extract_grounded",
    "description": "Extract real estate metrics with exact source quotes for each value",
    "input_schema": {
        "type": "object",
        "properties": {
            "market": {"type": "string"},
            "asset_class": {"type": "string"},
            "period": {"type": "string"},
            "prime_yield": {
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "quote": {"type": "string", "description": "Exact verbatim text containing this value"},
                    "page": {"type": "integer"},
                },
            },
            "vacancy_rate": {
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "quote": {"type": "string"},
                    "page": {"type": "integer"},
                },
            },
            "prime_rent": {
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "quote": {"type": "string"},
                    "page": {"type": "integer"},
                },
            },
            "gross_take_up": {
                "type": "object",
                "properties": {
                    "value": {"type": "integer"},
                    "quote": {"type": "string"},
                    "page": {"type": "integer"},
                },
            },
            "net_take_up": {
                "type": "object",
                "properties": {
                    "value": {"type": "integer"},
                    "quote": {"type": "string"},
                    "page": {"type": "integer"},
                },
            },
        },
        "required": ["market", "asset_class", "period"],
    },
}
