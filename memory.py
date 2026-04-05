# memory.py
"""
Conversation Memory + Semantic Cache — Phase 1
Features:
  - Session-based conversation history (JSON persistence)
  - Sliding window (last 5 exchanges = 10 messages)
  - Fuzzy semantic query cache (difflib)
  - Agent handoff memory (context survives model upgrades)
  - Export conversation (markdown + JSON)
"""

import os
import json
import uuid
import datetime
import difflib
from typing import Optional

# ── Storage Directories ──
SESSIONS_DIR = "sessions"
CACHE_FILE   = "query_cache.json"

os.makedirs(SESSIONS_DIR, exist_ok=True)

# ── Constants ──
MAX_TURNS          = 5          # last 5 exchanges (10 messages)
CACHE_SIMILARITY   = 0.85       # fuzzy match threshold
MAX_CACHE_ENTRIES  = 500        # cap cache size


# ══════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ══════════════════════════════════════════════════════

def create_session() -> str:
    """
    Generate unique session ID and create empty JSON file.
    Returns session_id string.
    """
    ts         = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    uid        = uuid.uuid4().hex[:8]
    session_id = f"session_{ts}_{uid}"

    session_data = {
        "session_id"  : session_id,
        "created_at"  : datetime.datetime.now().isoformat(),
        "last_active" : datetime.datetime.now().isoformat(),
        "turn_count"  : 0,
        "agents_used" : [],
        "turns"       : [],          # list of turn dicts
    }

    _save_session(session_id, session_data)
    return session_id


def _session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def _load_session(session_id: str) -> Optional[dict]:
    """Load session from JSON file. Returns None if not found."""
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_session(session_id: str, data: dict):
    """Persist session data to JSON file."""
    path = _session_path(session_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ══════════════════════════════════════════════════════
# TURN MANAGEMENT
# ══════════════════════════════════════════════════════

def add_turn(
    session_id : str,
    query      : str,
    response   : str,
    routing    : dict,
    result     : dict,
):
    """
    Append one full exchange (user + assistant) to session.
    Stores rich metadata alongside content.
    """
    data = _load_session(session_id)
    if data is None:
        # Session file missing — recreate silently
        session_id = create_session()
        data       = _load_session(session_id)

    turn_number = data["turn_count"] + 1
    now         = datetime.datetime.now().isoformat()

    turn = {
        "turn"       : turn_number,
        "timestamp"  : now,
        # ── Content ──
        "user"       : query,
        "assistant"  : response,
        # ── Routing metadata ──
        "agent"      : routing.get("agent", "reasoning"),
        "complexity" : routing.get("complexity", "medium"),
        "confidence" : routing.get("confidence", 0.5),
        "tier"       : routing.get("tier", "standard"),
        # ── Model metadata ──
        "model_key"  : result.get("model_key", ""),
        "model_label": result.get("model_label", ""),
        "provider"   : result.get("provider", ""),
        # ── Performance ──
        "latency_ms" : result.get("latency_ms", 0),
        "tokens"     : result.get("total_tokens", 0),
        "cost"       : result.get("estimated_cost", 0),
    }

    data["turns"].append(turn)
    data["turn_count"]   = turn_number
    data["last_active"]  = now

    # Track unique agents used in this session
    agent = routing.get("agent", "reasoning")
    if agent not in data["agents_used"]:
        data["agents_used"].append(agent)

    _save_session(session_id, data)


# ══════════════════════════════════════════════════════
# HISTORY RETRIEVAL
# ══════════════════════════════════════════════════════

def get_history(session_id: str, last_n: int = MAX_TURNS) -> list:
    """
    Return last N turns as raw dicts.
    last_n=5 means last 5 exchanges.
    """
    data = _load_session(session_id)
    if data is None:
        return []
    turns = data.get("turns", [])
    return turns[-last_n:]  # sliding window


def get_messages_for_llm(
    session_id : str,
    last_n     : int = MAX_TURNS,
    agent_filter: Optional[str] = None,
) -> list:
    """
    Format history as OpenAI-style messages list.
    Inject between system prompt and current user message.

    agent_filter: if set, only include turns from that agent
                  (per-agent namespacing)

    Returns:
        [
          {"role": "user",      "content": "..."},
          {"role": "assistant", "content": "..."},
          ...
        ]
    """
    turns = get_history(session_id, last_n)

    # Apply per-agent filter if requested
    if agent_filter:
        turns = [t for t in turns if t.get("agent") == agent_filter]
        # Still respect last_n after filtering
        turns = turns[-last_n:]

    messages = []
    for turn in turns:
        messages.append({"role": "user",      "content": turn["user"]})
        messages.append({"role": "assistant",  "content": turn["assistant"]})

    return messages


def get_context_summary(session_id: str) -> str:
    """
    One-liner context string for the router.
    Helps router classify follow-up queries like
    "add error handling to it" correctly.

    Returns empty string if no history.
    """
    turns = get_history(session_id, last_n=3)
    if not turns:
        return ""

    lines = []
    for t in turns:
        # Truncate long content for router context
        user_preview = t["user"][:150].replace("\n", " ")
        asst_preview = t["assistant"][:200].replace("\n", " ")
        lines.append(
            f"Turn {t['turn']} [{t['agent']}]: "
            f"User asked: '{user_preview}' | "
            f"Assistant: '{asst_preview}...'"
        )

    return "\n".join(lines)


def get_session_info(session_id: str) -> Optional[dict]:
    """Return session metadata (no turns content)."""
    data = _load_session(session_id)
    if data is None:
        return None
    return {
        "session_id"  : data["session_id"],
        "created_at"  : data["created_at"],
        "last_active" : data["last_active"],
        "turn_count"  : data["turn_count"],
        "agents_used" : data["agents_used"],
    }


# ══════════════════════════════════════════════════════
# SESSION LISTING & LOADING
# ══════════════════════════════════════════════════════

def list_sessions(limit: int = 10) -> list:
    """
    Return last N sessions sorted by last_active desc.
    Used in sidebar session selector.
    """
    sessions = []
    if not os.path.exists(SESSIONS_DIR):
        return sessions

    for fname in os.listdir(SESSIONS_DIR):
        if not fname.endswith(".json"):
            continue
        sid  = fname.replace(".json", "")
        info = get_session_info(sid)
        if info:
            sessions.append(info)

    # Sort by last_active descending
    sessions.sort(key=lambda x: x["last_active"], reverse=True)
    return sessions[:limit]


def clear_session(session_id: str):
    """Wipe all turns from session (keeps metadata)."""
    data = _load_session(session_id)
    if data is None:
        return
    data["turns"]       = []
    data["turn_count"]  = 0
    data["agents_used"] = []
    _save_session(session_id, data)


def delete_session(session_id: str):
    """Delete session file entirely."""
    path = _session_path(session_id)
    if os.path.exists(path):
        os.remove(path)


# ══════════════════════════════════════════════════════
# AGENT HANDOFF MEMORY
# ══════════════════════════════════════════════════════

def get_handoff_context(session_id: str) -> str:
    """
    When user upgrades to a more powerful model,
    the new model gets full conversation context
    so it doesn't start from scratch.

    Returns a formatted string injected into system prompt.
    """
    turns = get_history(session_id, last_n=MAX_TURNS)
    if not turns:
        return ""

    lines = [
        "=== CONVERSATION CONTEXT (Previous turns) ===",
        "You are continuing an existing conversation. "
        "Here is what has been discussed so far:\n",
    ]

    for t in turns:
        lines.append(f"--- Turn {t['turn']} ---")
        lines.append(f"User: {t['user']}")
        lines.append(
            f"Assistant ({t['model_label']}): "
            f"{t['assistant'][:500]}..."
            if len(t['assistant']) > 500
            else f"Assistant ({t['model_label']}): {t['assistant']}"
        )
        lines.append("")

    lines.append("=== END CONTEXT — Continue from here ===\n")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════
# EXPORT CONVERSATION
# ══════════════════════════════════════════════════════

def export_markdown(session_id: str) -> str:
    """
    Export full conversation as clean Markdown string.
    User can download as .md file.
    """
    data = _load_session(session_id)
    if data is None:
        return "# No conversation found"

    lines = [
        f"# Deep Agent Conversation",
        f"**Session:** `{session_id}`",
        f"**Created:** {data['created_at']}",
        f"**Turns:** {data['turn_count']}",
        f"**Agents Used:** {', '.join(data['agents_used'])}",
        "",
        "---",
        "",
    ]

    for turn in data["turns"]:
        lines += [
            f"## Turn {turn['turn']}",
            f"*{turn['timestamp']} · {turn['agent'].title()} Agent · "
            f"{turn['model_label']} · {turn['tokens']} tokens · "
            f"${turn['cost']:.6f}*",
            "",
            f"### 🧑 User",
            turn["user"],
            "",
            f"### 🤖 Assistant",
            turn["assistant"],
            "",
            "---",
            "",
        ]

    return "\n".join(lines)


def export_json(session_id: str) -> str:
    """Export full session as formatted JSON string."""
    data = _load_session(session_id)
    if data is None:
        return "{}"
    return json.dumps(data, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════
# SEMANTIC QUERY CACHE
# ══════════════════════════════════════════════════════

def _load_cache() -> dict:
    """Load cache from JSON file."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict):
    """Persist cache to JSON file."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _normalize(query: str) -> str:
    """
    Normalize query for comparison.
    Lowercase, strip whitespace, remove punctuation.
    """
    import re
    q = query.lower().strip()
    q = re.sub(r"[^\w\s]", "", q)
    q = re.sub(r"\s+", " ", q)
    return q


def cache_lookup(query: str, agent: str) -> Optional[dict]:
    """
    Fuzzy search cache for similar query in same agent type.
    Returns cached result dict or None.

    Uses difflib SequenceMatcher:
    - ratio() computes similarity 0.0 to 1.0
    - threshold: CACHE_SIMILARITY (0.85)
    """
    cache    = _load_cache()
    norm_q   = _normalize(query)
    best_hit = None
    best_sim = 0.0

    for key, entry in cache.items():
        # Only match same agent type
        if entry.get("agent") != agent:
            continue

        cached_norm = _normalize(entry["original_query"])
        sim = difflib.SequenceMatcher(
            None, norm_q, cached_norm
        ).ratio()

        if sim > best_sim:
            best_sim = sim
            best_hit = entry

    if best_sim >= CACHE_SIMILARITY and best_hit:
        return {
            "hit"             : True,
            "similarity"      : round(best_sim, 3),
            "original_query"  : best_hit["original_query"],
            "response"        : best_hit["response"],
            "agent"           : best_hit["agent"],
            "model_label"     : best_hit["model_label"],
            "model_key"       : best_hit["model_key"],
            "tier"            : best_hit["tier"],
            "provider"        : best_hit["provider"],
            "tokens"          : best_hit["tokens"],
            "cost"            : best_hit["cost"],
            "hits"            : best_hit["hits"] + 1,
            "saved_cost"      : best_hit["saved_cost"] + best_hit["cost"],
            "cached_at"       : best_hit["cached_at"],
        }

    return None


def cache_store(
    query   : str,
    agent   : str,
    routing : dict,
    result  : dict,
):
    """
    Store query+response in cache.
    Enforces MAX_CACHE_ENTRIES cap (evicts oldest).
    Only caches if response is meaningful (> 50 chars).
    """
    response = result.get("response", "")
    if len(response.strip()) < 50:
        return  # Don't cache empty/bad responses

    cache     = _load_cache()
    cache_key = f"{agent}_{uuid.uuid4().hex[:12]}"

    # Evict oldest if at cap
    if len(cache) >= MAX_CACHE_ENTRIES:
        oldest_key = min(
            cache.keys(),
            key=lambda k: cache[k].get("cached_at", "")
        )
        del cache[oldest_key]

    cache[cache_key] = {
        "original_query" : query,
        "response"       : response,
        "agent"          : agent,
        "model_key"      : result.get("model_key", ""),
        "model_label"    : result.get("model_label", ""),
        "tier"           : result.get("tier", ""),
        "provider"       : result.get("provider", ""),
        "tokens"         : result.get("total_tokens", 0),
        "cost"           : result.get("estimated_cost", 0.0),
        "hits"           : 0,
        "saved_cost"     : 0.0,
        "cached_at"      : datetime.datetime.now().isoformat(),
    }

    _save_cache(cache)


def get_cache_stats() -> dict:
    """
    Aggregate cache statistics for analytics dashboard.
    """
    cache = _load_cache()
    if not cache:
        return {
            "total_entries" : 0,
            "total_hits"    : 0,
            "total_saved"   : 0.0,
            "by_agent"      : {},
            "hit_rate"      : 0.0,
        }

    total_hits  = sum(e.get("hits", 0) for e in cache.values())
    total_saved = sum(e.get("saved_cost", 0.0) for e in cache.values())

    by_agent = {}
    for e in cache.values():
        a = e.get("agent", "unknown")
        if a not in by_agent:
            by_agent[a] = {"entries": 0, "hits": 0, "saved": 0.0}
        by_agent[a]["entries"] += 1
        by_agent[a]["hits"]    += e.get("hits", 0)
        by_agent[a]["saved"]   += e.get("saved_cost", 0.0)

    total_entries = len(cache)
    total_requests = total_entries + total_hits
    hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

    return {
        "total_entries" : total_entries,
        "total_hits"    : total_hits,
        "total_saved"   : round(total_saved, 6),
        "by_agent"      : by_agent,
        "hit_rate"      : round(hit_rate, 1),
    }


def clear_cache():
    """Wipe entire cache."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)