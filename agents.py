# agents.py
"""
Sub-Agent Engine — Sophisticated prompts + automatic fallback.
Updated: Injects conversation history + handoff context.
"""

import time
import litellm
from config import ALL_MODELS

litellm.drop_params = True

AGENT_PROMPTS = {
    "coding": """You are a senior software engineer with 10+ years of experience.

EVERY response must follow this structure:
1. **Problem Understanding** — restate in one line
2. **Approach** — explain your strategy in 2-3 bullets
3. **Solution** — complete, runnable code with:
   - Language-tagged code block
   - Type hints on functions
   - Docstring explaining purpose
   - Comments for non-obvious logic
   - Edge case handling
4. **Example Usage** — show how to use it
5. **Complexity** — Time: O(?), Space: O(?)

RULES: Never give partial code. Handle edge cases. State assumptions.""",

    "math": """You are an expert mathematician and patient tutor.

EVERY response must follow this structure:
1. **Problem Type** — classify it (algebra, calculus, proof, etc.)
2. **Given** — list known information
3. **Method** — state which formula/theorem you'll use
4. **Solution** — numbered steps, show EVERY calculation
5. **Verification** — check answer using different method
6. **Final Answer** — clearly highlighted

RULES: Never skip steps. Always verify. Show all arithmetic.""",

    "reasoning": """You are a senior analyst and strategic thinker.

EVERY response must follow this structure:
1. **Understanding** — restate the question
2. **Key Factors** — list important considerations
3. **Analysis** — structured exploration:
   - Comparisons → use a table
   - Explanations → use numbered steps
   - Decisions → list options with pros/cons
4. **Conclusion** — clear direct answer
5. **Recommendation** — actionable next steps

RULES: Be specific. Use tables for comparisons. Consider multiple angles.""",
}


def run_agent(
    query      : str,
    agent_type : str,
    model_key  : str,
    history    : list = None,       # NEW: OpenAI-style message history
    handoff    : str  = "",         # NEW: Handoff context string
) -> dict:
    """
    Execute agent with specified model. Auto-fallback on failure.

    Args:
        query:      Current user query
        agent_type: "coding" | "math" | "reasoning"
        model_key:  Key from ALL_MODELS
        history:    List of {"role":..,"content":..} from memory
        handoff:    Context string injected into system prompt on upgrade
    """
    history = history or []

    base_prompt = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["reasoning"])

    # ── Inject handoff context into system prompt if upgrading ──
    system_prompt = (
        f"{handoff}\n\n{base_prompt}"
        if handoff.strip()
        else base_prompt
    )

    if model_key not in ALL_MODELS:
        model_key = "standard_a"

    cfg        = ALL_MODELS[model_key]
    error_msg  = None
    fallback_used = False
    attempted  = cfg["label"]

    # ── Build messages: system + history + current query ──
    def build_messages(sys_prompt: str) -> list:
        msgs = [{"role": "system", "content": sys_prompt}]
        msgs.extend(history)                                  # inject history
        msgs.append({"role": "user", "content": query})      # current query last
        return msgs

    # ── Primary attempt ──
    try:
        start    = time.time()
        response = litellm.completion(
            model      = cfg["model"],
            api_key    = cfg["api_key"],
            messages   = build_messages(system_prompt),
            temperature= 0.3,
            max_tokens = 2048,
        )
        latency = (time.time() - start) * 1000

    except Exception as e:
        error_msg     = str(e)
        fallback_used = True

        # ── Fallback: same tier, different model ──
        tier         = cfg["tier"]
        fallback_key = None
        for k, v in ALL_MODELS.items():
            if v["tier"] == tier and k != model_key:
                fallback_key = k
                break
        if not fallback_key:
            fallback_key = "standard_a"

        fb = ALL_MODELS[fallback_key]
        try:
            start    = time.time()
            response = litellm.completion(
                model      = fb["model"],
                api_key    = fb["api_key"],
                messages   = build_messages(system_prompt),
                temperature= 0.3,
                max_tokens = 2048,
            )
            latency   = (time.time() - start) * 1000
            cfg       = fb
            model_key = fallback_key

        except Exception as e2:
            error_msg = f"Primary: {error_msg} | Fallback: {str(e2)}"

            # ── Last resort: lite_b ──
            last = ALL_MODELS["lite_b"]
            start    = time.time()
            response = litellm.completion(
                model      = last["model"],
                api_key    = last["api_key"],
                messages   = build_messages(system_prompt),
                temperature= 0.3,
                max_tokens = 2048,
            )
            latency   = (time.time() - start) * 1000
            cfg       = last
            model_key = "lite_b"

    usage        = response.usage
    total_tokens = usage.total_tokens if usage else 0
    cost         = (total_tokens / 1000) * cfg["cost_per_1k_tokens"]

    return {
        "response"          : response.choices[0].message.content,
        "model_used"        : cfg["model"],
        "model_label"       : cfg["label"],
        "model_key"         : model_key,
        "tier"              : cfg["tier"],
        "provider"          : cfg["provider"],
        "agent"             : agent_type,
        "latency_ms"        : round(latency, 1),
        "prompt_tokens"     : usage.prompt_tokens if usage else 0,
        "completion_tokens" : usage.completion_tokens if usage else 0,
        "total_tokens"      : total_tokens,
        "estimated_cost"    : cost,
        "fallback_used"     : fallback_used,
        "attempted_model"   : attempted,
        "error"             : error_msg,
        "history_turns"     : len(history) // 2,   # how many turns were injected
    }