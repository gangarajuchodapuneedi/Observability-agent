"""Data classes for the observability pipeline."""

from dataclasses import dataclass


@dataclass
class UserRequest:
    """Represents a user's request."""
    text: str
    user_id: str


@dataclass
class RetrievedItem:
    """Represents an item retrieved from a source."""
    source: str  # "web" or "memory"
    content: str


@dataclass
class ContextPacket:
    """Contains the user request and retrieved items for context."""
    request: UserRequest
    items: list[RetrievedItem]


@dataclass
class ModelInput:
    """Input prepared for the model after guardrails."""
    context: ContextPacket
    cleaned_prompt: str


@dataclass
class ModelOutput:
    """Output from the model with a quality score."""
    answer: str
    score: float
    source: str = "ollama"  # Source of the answer: "ollama", "fallback", etc.


@dataclass
class ActionResult:
    """Result of performing a write action."""
    success: bool
    details: str

