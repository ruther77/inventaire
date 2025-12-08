from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class FinanceRuleKeyword(BaseModel):
    value: str = Field(..., min_length=1, description="Mot-clé à matcher sur libellé/note.")


class FinanceRuleCreate(BaseModel):
    entity_id: int
    category_id: int
    name: str = Field(..., description="Nom de la règle")
    keywords: List[str] = Field(default_factory=list, description="Liste de mots-clés")
    apply_to_autre_only: bool = True
    is_active: bool = True


class FinanceRule(BaseModel):
    id: int
    entity_id: int
    category_id: int
    name: str
    keywords: List[str]
    apply_to_autre_only: bool
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    category_name: Optional[str] = None
    category_code: Optional[str] = None
