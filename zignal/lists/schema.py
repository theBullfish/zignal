"""Canonical row schema. Single source of truth for all surfaces."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class UnfinishedItem:
    host: str            # "temple" | "z13"
    source_path: str     # absolute path on host
    item_id: str         # "L22.05" etc.
    status: str          # "PENDING" | "DOING" | "BLOCKED"
    line: int            # 1-based line in source file
    excerpt: str         # the item line itself, trimmed
    age_days: int        # since first PENDING/DOING line for this id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def key(self) -> str:
        return f"{self.host}:{self.source_path}:{self.item_id}"
