from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class Category(str, Enum):
    fiction = "fiction"
    nonfiction = "nonfiction"
    poetry = "poetry"
    childrens = "childrens"
    other = "other"

class QualityFlag(str, Enum):
    missing_description = "missing_description"
    very_short_description = "very_short_description"
    price_looks_off = "price_looks_off"
    none = "none"


class EnrichRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    price_gbp: float


class EnrichResponse(BaseModel):
    category: Category
    summary: str = Field(..., max_length=250)
    quality_flags: List[QualityFlag]
    confidence: float = Field(..., ge=0.0, le=1.0)
