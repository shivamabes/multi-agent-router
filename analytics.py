# analytics.py
"""
Local Analytics — Logs queries to CSV, computes cost savings.
Updated: session_id column + cache statistics.
Production: replace with BigQuery.
"""

import os
import csv
import datetime
from config import ALL_MODELS

LOG_FILE = "query_logs.csv"
HEADERS  = [
    "timestamp", "session_id", "query", "agent", "complexity", "confidence",
    "tier", "model_key", "model_label", "latency_ms", "routing_latency_ms",
    "tokens", "cost", "fallback", "upgraded_from", "cache_hit",
    "history_turns", "context_used",
]


def _ensure():
    """Create CSV with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADERS)


def log_query(
    routing        : dict,
    result         : dict,
    upgraded_from  : str  = "",
    session_id     : str  = "",
    cache_hit      : bool = False,
):
    """Append one query row to CSV log."""
    _ensure()
    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.datetime.now().isoformat(),
                session_id,
                (routing.get("original_query") or "")[:300],
                routing.get("agent", ""),
                routing.get("complexity", ""),
                routing.get("confidence", 0),
                result.get("tier", ""),
                result.get("model_key", ""),
                result.get("model_label", ""),
                result.get("latency_ms", 0),
                routing.get("routing_latency_ms", 0),
                result.get("total_tokens", 0),
                result.get("estimated_cost", 0),
                result.get("fallback_used", False),
                upgraded_from,
                cache_hit,
                result.get("history_turns", 0),
                routing.get("context_used", False),
            ])
    except Exception:
        pass


def load_logs():
    """Load CSV into pandas DataFrame."""
    _ensure()
    try:
        import pandas as pd
        df = pd.read_csv(LOG_FILE)
        if len(df) == 0:
            return None
        for col in ["latency_ms", "routing_latency_ms", "tokens",
                    "cost", "confidence", "history_turns"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    except Exception:
        return None


def compute_savings(result: dict) -> dict:
    """Per-query cost intelligence vs pro_a baseline."""
    tokens    = result.get("total_tokens", 0)
    actual    = result.get("estimated_cost", 0)
    pro_cost  = (tokens / 1000) * ALL_MODELS["pro_a"]["cost_per_1k_tokens"]
    savings   = pro_cost - actual
    pct       = (savings / pro_cost * 100) if pro_cost > 0 else 0

    all_costs = {}
    for key, cfg in ALL_MODELS.items():
        c = (tokens / 1000) * cfg["cost_per_1k_tokens"]
        all_costs[key] = {
            "label"      : cfg["label"],
            "tier"       : cfg["tier"],
            "provider"   : cfg["provider"],
            "cost"       : c,
            "latency"    : cfg["avg_latency_ms"],
            "is_current" : key == result.get("model_key", ""),
        }

    return {
        "actual"      : actual,
        "pro_cost"    : pro_cost,
        "savings"     : savings,
        "savings_pct" : round(pct, 1),
        "all_costs"   : all_costs,
    }


def session_stats(df) -> dict:
    """Aggregate stats across all logged queries."""
    if df is None or len(df) == 0:
        return None

    total_cost   = df["cost"].sum()
    total_tokens = df["tokens"].sum()
    pro_rate     = ALL_MODELS["pro_a"]["cost_per_1k_tokens"]
    hyp_cost     = (total_tokens / 1000) * pro_rate
    saved        = hyp_cost - total_cost

    # Fallback count
    fallback_count = 0
    if "fallback" in df.columns:
        fallback_count = int(
            df["fallback"].astype(str).str.contains("True", case=False).sum()
        )

    # Cache hits
    cache_hits = 0
    if "cache_hit" in df.columns:
        cache_hits = int(
            df["cache_hit"].astype(str).str.contains("True", case=False).sum()
        )

    # Unique sessions
    unique_sessions = 0
    if "session_id" in df.columns:
        unique_sessions = df["session_id"].nunique()

    # Avg history turns injected
    avg_history = 0.0
    if "history_turns" in df.columns:
        avg_history = round(df["history_turns"].mean(), 1)

    return {
        "queries"         : len(df),
        "cost"            : round(total_cost, 6),
        "tokens"          : int(total_tokens),
        "avg_latency"     : round(df["latency_ms"].mean(), 1),
        "hyp_cost"        : round(hyp_cost, 6),
        "saved"           : round(saved, 6),
        "saved_pct"       : round((saved / hyp_cost * 100), 1) if hyp_cost > 0 else 0,
        "tiers"           : df["tier"].value_counts().to_dict(),
        "agents"          : df["agent"].value_counts().to_dict(),
        "fallbacks"       : fallback_count,
        "cache_hits"      : cache_hits,
        "unique_sessions" : unique_sessions,
        "avg_history"     : avg_history,
    }


def clear_logs():
    """Delete log file."""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)