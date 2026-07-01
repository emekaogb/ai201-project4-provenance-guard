"""
Audit log for tracking all submission and appeal decisions.
Stores structured entries for transparency and debugging.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

LOG_FILE = "audit_log.json"


def ensure_log_exists():
    """Create log file if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)


def log_submission(
    content_id: str,
    creator_id: str,
    attribution: str,
    confidence: float,
    llm_score: float,
    linguistic_score: float = None,
    status: str = "classified",
) -> None:
    """
    Log a submission decision.

    Args:
        content_id: Unique identifier for this submission
        creator_id: Creator identifier
        attribution: Classification result (e.g., "likely_ai", "likely_human", "uncertain")
        confidence: Confidence score (0-1)
        llm_score: Signal 1 (perplexity) score (0-1)
        linguistic_score: Signal 2 (linguistic) score (0-1), optional for M3
        status: Current status ("classified", "under_review", etc.)
    """
    ensure_log_exists()

    entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "linguistic_score": linguistic_score,
        "status": status,
    }

    with open(LOG_FILE, "r") as f:
        log = json.load(f)

    log.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def log_appeal(
    appeal_id: str,
    content_id: str,
    creator_id: str,
    reasoning: str,
    evidence: str = None,
) -> None:
    """
    Log an appeal submission.

    Args:
        appeal_id: Unique identifier for this appeal
        content_id: Original submission ID
        creator_id: Creator identifier
        reasoning: Why the creator disagrees with the classification
        evidence: Optional URL or reference
    """
    ensure_log_exists()

    with open(LOG_FILE, "r") as f:
        log = json.load(f)

    # Find and update the original submission entry
    for entry in log:
        if entry.get("content_id") == content_id:
            if "appeals" not in entry:
                entry["appeals"] = []
            entry["appeals"].append({
                "appeal_id": appeal_id,
                "creator_id": creator_id,
                "reasoning": reasoning,
                "evidence": evidence,
                "submitted_at": datetime.utcnow().isoformat() + "Z",
                "status": "under_review",
            })
            entry["status"] = "under_review"
            break

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def get_log(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieve log entries.

    Args:
        limit: Maximum number of entries to return
        offset: Number of entries to skip from the end

    Returns:
        List of log entries (most recent first)
    """
    ensure_log_exists()

    with open(LOG_FILE, "r") as f:
        log = json.load(f)

    # Return most recent entries first
    return log[-offset-limit:-offset] if offset + limit < len(log) else log[-offset:] if offset else log[-limit:]


def get_submission_by_id(content_id: str) -> Dict[str, Any] or None:
    """Retrieve a submission by content_id."""
    ensure_log_exists()

    with open(LOG_FILE, "r") as f:
        log = json.load(f)

    for entry in log:
        if entry.get("content_id") == content_id:
            return entry

    return None
