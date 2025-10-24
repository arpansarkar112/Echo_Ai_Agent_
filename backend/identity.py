"""Shared helpers for Echo's identity messaging."""

from __future__ import annotations

import re

_IDENTITY_PHRASES = {
    "what are you",
    "who are you",
    "what is your name",
    "whats your name",
    "tell me about yourself",
    "who made you",
    "who built you",
    "are you from google",
    "are you google",
    "are you built by google",
    "did google make you",
    "are you trained by google",
}

_IDENTITY_RESPONSE = (
    "I'm Echo, the CSV AI agent. I help you work directly with CSV files - "
    "running math and comparisons, visualising trends, and updating rows or columns. "
    "I'm built specifically for the Echo application, not by Google."
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def is_identity_query(message: str | None) -> bool:
    """Return True when the user is asking about the agent's identity."""
    if not message:
        return False
    normalized = _normalize_text(message)
    return any(phrase in normalized for phrase in _IDENTITY_PHRASES)


def identity_response() -> str:
    """Return the canonical Echo identity response."""
    return _IDENTITY_RESPONSE
