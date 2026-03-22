# 🤖 Deep Agent — Dynamic Multi-Agent Router

A multi-agent AI system that intelligently routes queries to specialized sub-agents (Coding, Reasoning, Math) and dynamically selects the optimal LLM model tier (Pro, Standard, Lite) based on query complexity — all at runtime.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)
![LiteLLM](https://img.shields.io/badge/LiteLLM-Powered-green)
![Groq](https://img.shields.io/badge/Groq-API-orange)
![Gemini](https://img.shields.io/badge/Google-Gemini-blue)

---

## 🏗️ Architecture

                  ┌─────────────────┐
                  │   USER QUERY    │
                  └────────┬────────┘
                           │
                           ▼
           ┌───────────────────────────────┐
           │      🧠 DEEP AGENT (Router)   │
           │    groq/llama-3.1-8b-instant   │
           │                               │
           │  Classifies:                  │
           │  1. Agent (coding/math/reason)│
           │  2. Complexity (simple/med/cx)│
           │  3. Model Tier (lite/std/pro) │
           └───┬───────────┬───────────┬───┘
               │           │           │
               ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │💻 Coding │ │🧠 Reason │ │🔢 Math   │
        │  Agent   │ │  Agent   │ │  Agent   │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └──────┬─────┘────────────┘
                    │
                    ▼ (Dynamic Model Selection)
     ┌──────────────────────────────────────┐
     │ 🟢 Simple  → Gemini Flash-Lite       │
     │              (fallback: Groq 8B)     │
     │ 🟠 Medium  → Groq LLaMA 8B          │
     │ 🔴 Complex → Groq LLaMA 70B         │
     └──────────────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  📊 Response + Metrics + Comparison  │
     └──────────────────────────────────────┘

---

## ✨ Key Features

- **🤖 Intelligent Routing** — Deep Agent classifies every query and picks the right sub-agent + model automatically
- **💰 Cost Optimization** — Simple tasks use cheap models, complex tasks get powerful models
- **⚡ Dynamic Model Selection** — Model tier decided at runtime, not hardcoded
- **🔄 Fallback Strategy** — If Gemini fails (rate limit), automatically falls back to Groq with error visibility
- **📊 Full Observability** — Latency, token usage, cost comparison shown for every query
- **🎯 3 Specialized Agents** — Coding, Reasoning, and Math each with optimized system prompts

---

## 📊 Model Tiers

| Tier                 | Model                          | Use Case                                | Cost    |
| -------------------- | ------------------------------ | --------------------------------------- | ------- |
| 🟢 **Lite**          | `gemini/gemini-2.0-flash-lite` | Simple tasks (add numbers, basic facts) | Lowest  |
| 🟢 **Lite Fallback** | `groq/llama-3.1-8b-instant`    | When Gemini rate-limited                | Low     |
| 🟠 **Standard**      | `groq/llama-3.1-8b-instant`    | Medium tasks (algorithms, comparisons)  | Medium  |
| 🔴 **Pro**           | `groq/llama-3.3-70b-versatile` | Complex tasks (system design, proofs)   | Highest |
| 🔧 **Router**        | `groq/llama-3.1-8b-instant`    | Query classification only               | Minimal |

---
