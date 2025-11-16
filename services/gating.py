"""Keyword-based gating utilities for deciding whether to summarize content."""

from __future__ import annotations

import hashlib
import logging
import threading
import time
import unicodedata
import re
from typing import Iterable

from config import (
    ENABLE_GATING,
    GATING_CACHE_TTL_SECONDS,
    GATING_DEFAULT_ON_ERROR,
    GATING_KEYWORDS,
    GATING_MATCH_MODE,
    GATING_STRATEGY,
    USE_MODEL_BASED_GATING,
    MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS,
)
from services.ai_services import is_article_relevant

_CACHE: dict[str, tuple[float, bool]] = {}
_CACHE_LOCK = threading.Lock()
_ALLOWED_MATCH_MODES = {"allow_if_any", "deny_if_any"}

# Log once per session if gating is disabled so operators are aware of the runtime config.
# Imported at module load time, so this executes only once per process.
if not ENABLE_GATING:
    logging.warning(
        "Keyword gating is DISABLED. Set ENABLE_GATING=true to enable content filtering."
    )


def should_summarize(text: str | None) -> bool:
    """Return True if the content should be summarized based on configured strategy.

    This is a convenience wrapper that returns only the boolean decision. Use
    `should_summarize_with_matches` for details about which keywords matched.
    """
    if not ENABLE_GATING:
        return True
    if not text:
        return True

    strategy = GATING_STRATEGY.lower().strip()
    # If configured to use model-based gating and the model is available, try it first.
    if USE_MODEL_BASED_GATING and strategy == "model":
        try:
            model_decision = is_article_relevant(text)
            if model_decision is True:
                logging.info("Model-based gating: allow")
                return True
            if model_decision is False:
                logging.info("Model-based gating: deny")
                return False
            # model_decision is None -> fall through to fallback logic
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception("Model-based gating check failed: %s", exc)
            if not MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS:
                return GATING_DEFAULT_ON_ERROR

    if strategy != "keywords" and strategy != "model":
        logging.warning("Unsupported gating strategy '%s'. Defaulting to allow.", strategy)
        return True

    normalized = _normalize_text(text)
    cache_key = _cache_key(normalized)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        matches = _find_keyword_matches(normalized, GATING_KEYWORDS)
        decision = _evaluate_matches(matches)
        _set_cached(cache_key, decision)
        if decision:
            logging.info("Gating allow: keywords matched %s", matches)
        else:
            logging.info("Gating deny: no keyword match")
        return decision
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Keyword gating failed: %s", exc)
        return GATING_DEFAULT_ON_ERROR


def should_summarize_with_matches(text: str | None, *, force: bool = False) -> tuple[bool, list[str]]:
    """Return (decision, matches) for the given text.

    This function exposes which tokens matched and the boolean decision so
    callers can log or present triggers to users. It respects caching and
    configuration, similar to `should_summarize`.
    """
    if not text:
        return True, []
    if not ENABLE_GATING and not force:
        return True, []
    normalized = _normalize_text(text)
    cache_key = _cache_key(normalized)
    cached = _get_cached(cache_key)
    if cached is not None:
        # We can't reconstruct matches from the cached bool; return empty list
        return cached, []
    # If model gating is enabled and configured, prefer the model.
    strategy = GATING_STRATEGY.lower().strip()
    if USE_MODEL_BASED_GATING and strategy == "model":
        try:
            model_decision = is_article_relevant(text)
            if model_decision is True:
                _set_cached(cache_key, True)
                return True, []
            if model_decision is False:
                _set_cached(cache_key, False)
                return False, []
            # model_decision is None: fall back to keywords if configured
            if not MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS:
                return GATING_DEFAULT_ON_ERROR, []
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception("Model-based gating check failed: %s", exc)
            if not MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS:
                return GATING_DEFAULT_ON_ERROR, []

    try:
        matches = _find_keyword_matches(normalized, GATING_KEYWORDS)
        decision = _evaluate_matches(matches)
        _set_cached(cache_key, decision)
        return decision, matches
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Keyword gating failed: %s", exc)
        return GATING_DEFAULT_ON_ERROR, []


def _normalize_text(text: str) -> str:
    """Lowercase and strip accents to make keyword checks stable."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii", "ignore")
    return text.lower()


def _cache_key(text: str) -> str:
    snippet = text[:4096]
    return hashlib.sha256(snippet.encode("utf-8")).hexdigest()


def _get_cached(key: str) -> bool | None:
    if GATING_CACHE_TTL_SECONDS <= 0:
        return None
    now = time.monotonic()
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if not entry:
            return None
        expires_at, decision = entry
        if now >= expires_at:
            del _CACHE[key]
            return None
        return decision


def _set_cached(key: str, decision: bool) -> None:
    if GATING_CACHE_TTL_SECONDS <= 0:
        return
    expires_at = time.monotonic() + GATING_CACHE_TTL_SECONDS
    with _CACHE_LOCK:
        _CACHE[key] = (expires_at, decision)


def _find_keyword_matches(text: str, keywords: Iterable[str]) -> list[str]:
    matches: list[str] = []
    for keyword in keywords:
        token = keyword.strip().lower()
        if not token:
            continue
        # Use regex word boundary matching to avoid substring false positives.
        # For multi-word phrases, word boundaries at the ends are sufficient.
        try:
            pattern = r"\b" + re.escape(token) + r"\b"
            if re.search(pattern, text):
                matches.append(token)
        except re.error:
            # Fallback to substring matching if token causes regex issues
            if token in text:
                matches.append(token)
    return matches


def _evaluate_matches(matches: list[str]) -> bool:
    if not GATING_KEYWORDS:
        return True

    match_mode = GATING_MATCH_MODE.lower()
    if match_mode not in _ALLOWED_MATCH_MODES:
        logging.warning(
            "Unknown GATING_MATCH_MODE '%s'; defaulting to allow", GATING_MATCH_MODE
        )
        return True

    if match_mode == "allow_if_any":
        return bool(matches)
    if match_mode == "deny_if_any":
        return not matches
    return True


__all__ = ["should_summarize", "should_summarize_with_matches"]
