"""Common Issue model. Single source of truth for ingest + dedup + ranker.

All timestamps normalized to UTC. Pydantic v2 frozen model; extra fields raise.
"""
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Tool = Literal["aider", "cline", "continue"]
State = Literal["open", "closed"]


class Issue(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., description="Stable id, e.g. 'aider:1234'")
    tool: Tool
    repo: str
    number: int
    title: str
    body: str = ""
    url: str
    state: State
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    labels: list[str] = Field(default_factory=list)
    author_login_sha256: str = Field(..., description="SHA-256 of login for privacy")
    comments_count: int = 0
    reactions_count: int = 0

    @field_validator("created_at", "updated_at", "closed_at", mode="before")
    @classmethod
    def to_utc(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
