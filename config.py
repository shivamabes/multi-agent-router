"""
Configuration — Single source of truth.
Models: Only models that WORK reliably without rate limits.
  - Groq: LLaMA 8B, LLaMA 70B, GPT-OSS-20B, GPT-OSS-120B
  - Gemini: gemini-2.5-flash-lite, gemini-2.5-flash
"""

import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

try:
    import streamlit as st
    if hasattr(st, "secrets"):
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", GROQ_API_KEY)
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", GEMINI_API_KEY)
except Exception:
    pass

# ══════════════════════════════════════════════════════
# MODEL REGISTRY
# ══════════════════════════════════════════════════════
ALL_MODELS = {
    # ── LITE TIER ──
    "lite_a": {
        "model": "gemini/gemini-2.5-flash-lite",
        "api_key": GEMINI_API_KEY,
        "label": "Gemini 2.5 Flash-Lite",
        "tier": "lite",
        "provider": "Google",
        "params": "Optimized",
        "cost_per_1k_tokens": 0.00005,
        "avg_latency_ms": 400,
        "strength": "Fastest & cheapest",
    },
    "lite_b": {
        "model": "groq/openai/gpt-oss-20b",
        "api_key": GROQ_API_KEY,
        "label": "GPT-OSS 20B",
        "tier": "lite",
        "provider": "Groq",
        "params": "20B",
        "cost_per_1k_tokens": 0.000075,
        "avg_latency_ms": 500,
        "strength": "Fast 20B model, 1000 T/sec speed",
    },

    # ── STANDARD TIER ──
    "standard_a": {
        "model": "groq/llama-3.1-8b-instant",
        "api_key": GROQ_API_KEY,
        "label": "LLaMA 3.1 8B",
        "tier": "standard",
        "provider": "Groq",
        "params": "8B",
        "cost_per_1k_tokens": 0.0001,
        "avg_latency_ms": 500,
        "strength": "Balanced cost & quality",
    },
    "standard_b": {
        "model": "groq/openai/gpt-oss-120b",
        "api_key": GROQ_API_KEY,
        "label": "GPT-OSS 120B",
        "tier": "standard",
        "provider": "Groq",
        "params": "120B",
        "cost_per_1k_tokens": 0.00015,
        "avg_latency_ms": 800,
        "strength": "120B params, strong reasoning at low cost",
    },

    # ── PRO TIER ──
    "pro_a": {
        "model": "groq/llama-3.3-70b-versatile",
        "api_key": GROQ_API_KEY,
        "label": "LLaMA 3.3 70B",
        "tier": "pro",
        "provider": "Groq",
        "params": "70B",
        "cost_per_1k_tokens": 0.0008,
        "avg_latency_ms": 2500,
        "strength": "Smartest open-source model",
    },
    "pro_b": {
        "model": "gemini/gemini-2.5-flash",
        "api_key": GEMINI_API_KEY,
        "label": "Gemini 2.5 Flash",
        "tier": "pro",
        "provider": "Google",
        "params": "~65B equivalent",
        "cost_per_1k_tokens": 0.0005,
        "avg_latency_ms": 2000,
        "strength": "Google's best, strong analysis",
    },
}

# ── Router ──
ROUTER_MODEL = {
    "model": "groq/llama-3.1-8b-instant",
    "api_key": GROQ_API_KEY,
}

# ── Defaults ──
TIER_DEFAULTS = {
    "lite": "lite_a",
    "standard": "standard_a",
    "pro": "pro_a",
}

# ── Upgrade paths ──
UPGRADE_OPTIONS = {
    "lite_a":     ["lite_b", "standard_a", "standard_b", "pro_a", "pro_b"],
    "lite_b":     ["standard_a", "standard_b", "pro_a", "pro_b"],
    "standard_a": ["standard_b", "pro_a", "pro_b"],
    "standard_b": ["pro_a", "pro_b"],
    "pro_a":      ["pro_b"],
    "pro_b":      [],
}

# ── Guardrails ──
GUARDRAIL_CONFIG = {
    "max_query_length": 5000,
    "rate_limit_per_minute": 20,
    "daily_cost_ceiling": 5.0,
    "min_response_length": 10,
    "blocked_phrases": [
        "ignore all instructions", "ignore previous instructions",
        "ignore your instructions", "disregard all",
        "forget your prompt", "reveal your system prompt",
        "show your system prompt", "print your instructions",
        "you are now dan", "pretend you are",
        "act as an unrestricted", "jailbreak",
        "bypass your rules", "override safety",
    ],
    "dangerous_code_patterns": [
        "os.system(", "subprocess.call(", "subprocess.Popen(",
        "subprocess.run(", "eval(", "exec(",
        "rm -rf", "DROP TABLE", "DELETE FROM",
        "__import__(", "shutil.rmtree(",
    ],
    "pii_patterns": {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    },
}