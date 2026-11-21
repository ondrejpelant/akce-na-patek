from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PriceType = Literal["regular", "promo", "loyalty"]
SourceKind = Literal["catalog", "leaflet"]


class ScrapedItem(BaseModel):
    """One price observation returned by a source.

    A source may emit several items with the same `store_sku` when the item has
    multiple price types (e.g. Tesco regular + Clubcard).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    store_code: str
    store_sku: str  # stable id in the source; for leaflets: sha1(norm_name|volume_ml)
    raw_name: str
    price_czk: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    price_type: PriceType
    regular_czk: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    promo_from: date | None = None
    promo_to: date | None = None
    volume_ml: int | None = Field(default=None, gt=0)
    abv: Decimal | None = Field(default=None, ge=0, le=100, max_digits=4, decimal_places=1)
    ean: str | None = None
    url: str | None = None
    image_url: str | None = None
    source_category: str | None = None
    source_kind: SourceKind
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("promo_to")
    @classmethod
    def _promo_range(cls, v: date | None, info) -> date | None:
        promo_from = info.data.get("promo_from")
        if v is not None and promo_from is not None and v < promo_from:
            raise ValueError("promo_to is before promo_from")
        return v
