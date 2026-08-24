"""JSON schema for website e-commerce indicators (T04 pin / T05 cascade).

Each field carries a value, confidence, abstain flag, and reason so later
tasks can report selective prediction without inventing missing evidence.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentToken = Literal["vnpay", "momo", "cod", "other", "none"]
LanguageCode = Literal["vi", "en", "ja", "mixed", "unknown"]
MarketplacePlatform = Literal["shopee", "tiktok", "lazada", "other"]
SocialPlatform = Literal[
    "facebook",
    "youtube",
    "linkedin",
    "zalo",
    "instagram",
    "x",
    "tiktok",
    "other",
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BoolField(_Strict):
    value: bool | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    abstain: bool
    reason: str = ""


class PaymentField(_Strict):
    value: list[PaymentToken] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    abstain: bool
    reason: str = ""


class SocialLink(_Strict):
    platform: SocialPlatform
    url: str


class SocialField(_Strict):
    value: list[SocialLink] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    abstain: bool
    reason: str = ""


class MarketplaceLink(_Strict):
    platform: MarketplacePlatform
    url: str


class MarketplaceField(_Strict):
    value: list[MarketplaceLink] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    abstain: bool
    reason: str = ""


class LanguageField(_Strict):
    value: LanguageCode | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    abstain: bool
    reason: str = ""


class ExtractionResult(_Strict):
    """Structured indicators extracted from one rendered page."""

    has_product_catalog: BoolField
    has_order_cart: BoolField
    payment_methods: PaymentField
    social_links: SocialField
    marketplace_links: MarketplaceField
    website_language: LanguageField

    def all_fields_abstain(self) -> bool:
        return all(
            getattr(self, name).abstain
            for name in (
                "has_product_catalog",
                "has_order_cart",
                "payment_methods",
                "social_links",
                "marketplace_links",
                "website_language",
            )
        )


def extraction_json_schema() -> dict:
    """JSON Schema sent to Ollama ``format`` (and echoed in the prompt)."""
    return ExtractionResult.model_json_schema()


def abstain_result(reason: str) -> ExtractionResult:
    """Entire record abstains — no invented field values."""
    bool_f = BoolField(value=None, confidence=0.0, abstain=True, reason=reason)
    pay_f = PaymentField(value=[], confidence=0.0, abstain=True, reason=reason)
    soc_f = SocialField(value=[], confidence=0.0, abstain=True, reason=reason)
    mkt_f = MarketplaceField(value=[], confidence=0.0, abstain=True, reason=reason)
    lang_f = LanguageField(value=None, confidence=0.0, abstain=True, reason=reason)
    return ExtractionResult(
        has_product_catalog=bool_f,
        has_order_cart=bool_f.model_copy(),
        payment_methods=pay_f,
        social_links=soc_f,
        marketplace_links=mkt_f,
        website_language=lang_f,
    )


def parse_extraction(raw: str) -> ExtractionResult:
    return ExtractionResult.model_validate_json(raw)
