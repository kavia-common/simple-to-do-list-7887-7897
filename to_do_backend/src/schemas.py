"""Pydantic schemas for the To-Do REST API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    """A task as returned by the API."""

    id: int = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Short task title")
    description: str = Field("", description="Optional task details")
    completed: bool = Field(False, description="Whether the task is completed")
    created_at: str = Field(..., description="UTC timestamp when created (ISO-8601 string)")
    updated_at: str = Field(..., description="UTC timestamp when last updated (ISO-8601 string)")


class TaskCreate(BaseModel):
    """Payload to create a task."""

    title: str = Field(..., min_length=1, max_length=200, description="Short task title")
    description: Optional[str] = Field("", max_length=2000, description="Optional task details")


class TaskUpdate(BaseModel):
    """Payload to update a task (partial update)."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Short task title")
    description: Optional[str] = Field(None, max_length=2000, description="Optional task details")
    completed: Optional[bool] = Field(None, description="Whether the task is completed")
