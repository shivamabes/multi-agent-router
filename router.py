"""
Query Router — Classifies queries into agent type + complexity.
Uses fast cheap model (LLaMA 8B) so routing overhead is minimal.
"""

import json
import time
import litellm
from config import ROUTER_MODEL, ALL_MODELS, TIER_DEFAULTS

litellm.drop_params = True

ROUTER_PROMPT = """You are a query classifier for a multi-agent AI system.

OUTPUT: Only valid JSON, nothing else.
{
  "agent": "<coding|reasoning|math>",
  "complexity": "<simple|medium|complex>",
  "confidence": <0.0 to 1.0>,
  "reason": "<brief explanation>"
}

AGENT RULES:
- coding → needs CODE output (write/debug/implement code, SQL, scripts, algorithms)
- math → needs MATH work (calculations, equations, proofs, statistics)
- reasoning → needs ANALYSIS (comparisons, explanations, planning, facts, logic)

COMPLEXITY:
- simple → one-step obvious answer ("2+2", "hello world", "capital of France")
- medium → multi-step standard task ("binary search", "quadratic equation", "X vs Y")
- complex → deep expertise needed ("system design", "proofs", "architecture decisions")

EDGE CASES:
- "explain quicksort" → reasoning (wants explanation)
- "implement quicksort" → coding (wants code)
- Unsure about complexity → default "medium"
- Unsure about agent → default "reasoning"

Output ONLY the JSON."""


def route_query(query: str) -> dict:
    start = time.time()

    response = litellm.completion(
        model=ROUTER_MODEL["model"],
        api_key=ROUTER_MODEL["api_key"],
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
        max_tokens=200,
    )

    latency = (time.time() - start) * 1000

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"agent": "reasoning", "complexity": "medium", "confidence": 0.3, "reason": "Parse failed"}

    agent = parsed.get("agent", "reasoning")
    if agent not in ("coding", "math", "reasoning"):
        agent = "reasoning"

    complexity = parsed.get("complexity", "medium")
    if complexity not in ("simple", "medium", "complex"):
        complexity = "medium"

    confidence = parsed.get("confidence", 0.5)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.5

    tier = {"simple": "lite", "medium": "standard", "complex": "pro"}[complexity]
    model_key = TIER_DEFAULTS[tier]
    model_cfg = ALL_MODELS[model_key]

    return {
        "agent": agent,
        "complexity": complexity,
        "confidence": confidence,
        "reason": parsed.get("reason", ""),
        "tier": tier,
        "model_key": model_key,
        "model": model_cfg["model"],
        "model_label": model_cfg["label"],
        "routing_latency_ms": round(latency, 1),
        "router_tokens": response.usage.total_tokens if response.usage else 0,
    }