# 🤖 Deep Agent v2.0 — Dynamic Multi-Agent Router

An intelligent multi-agent AI system that routes queries to specialized sub-agents (Coding, Reasoning, Math), dynamically selects the optimal LLM model tier at runtime, maintains conversational memory across turns, and serves repeated queries instantly from a semantic cache.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)
![LiteLLM](https://img.shields.io/badge/LiteLLM-Powered-green)
![Groq](https://img.shields.io/badge/Groq-API-orange)
![Gemini](https://img.shields.io/badge/Google-Gemini-blue)

---

## 🏗️ Architecture

```
                       USER QUERY
                            │
                            ▼
               ┌─────────────────────────┐
               │   INPUT GUARDRAILS 🛡️   │
               │ Injection • PII • Rate  │
               └────────────┬────────────┘
                            │
                            ▼
               ┌─────────────────────────┐
               │   SEMANTIC CACHE ⚡     │
               │  Fuzzy match (≥0.85)   │
               │  HIT → instant, $0 cost │
               └────────────┬────────────┘
                            │ MISS
                            ▼
               ┌─────────────────────────┐
               │  QUERY ROUTER 🔀       │
               │  (LLaMA 8B)             │
               │  + Conversation Context │
               └────┬────────┬───────┬──┘
                    │        │       │
                    ▼        ▼       ▼
              ┌───────┐ ┌──────┐ ┌────┐
              │Coding │ │Reason│ │Math │
              │Agent  │ │Agent │ │Agent│
              └───┬───┘ └──┬───┘ └─┬──┘
                  │        │       │
                  └────┬───────┬──┘
                       │ (+history)
                       ▼
         ┌─────────────────────────────┐
         │  Dynamic Model Selection    │
         │                             │
         │ 🟢 Simple  → Flash-Lite     │
         │ 🟠 Medium  → LLaMA 8B       │
         │ 🔴 Complex → LLaMA 70B      │
         └────────────┬────────────────┘
                      │
           ┌──────────────────────┐
           │ 3-LEVEL FALLBACK     │
           │ Primary → Alternate  │
           │ → Last Resort (8B)   │
           └──────────┬───────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │  OUTPUT GUARDRAILS 🛡️   │
         │ Code • Uncertainty • Len│
         └────────────┬────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │  MEMORY + CACHE STORE   │
         │  Sessions: JSON         │
         │  Cache: query_cache.json│
         └────────────┬────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │  📊 ANALYTICS & LOGS    │
         │  CSV + Real-time Metrics│
         └─────────────────────────┘
```

---

## ✨ Key Features

### 🎯 Core Intelligence

- **Intelligent Routing** — LLaMA 8B automatically classifies queries into agent type (Coding/Reasoning/Math) + complexity (Simple/Medium/Complex) at runtime
- **Dynamic Model Selection** — Maps complexity to optimal model tier:
  - Simple → Gemini Flash-Lite ($0.00005/1K)
  - Medium → LLaMA 8B ($0.0001/1K)
  - Complex → LLaMA 70B ($0.0008/1K)
- **Cost Optimization** — Up to 94% cost reduction by right-sizing model selection

### 💬 Conversational Memory

- **Session-Based History** — Each conversation stored as JSON with full metadata
- **Sliding Window** — Last 5 exchanges (10 messages) injected into every LLM call
- **Per-Agent Namespacing** — Separate memory streams for Coding/Reasoning/Math agents
- **Context-Aware Routing** — Router reads conversation history for follow-up query understanding
- **Agent Handoff** — Upgrading to a stronger model injects full conversation context so it doesn't start from scratch
- **Export** — Download conversation as Markdown or JSON

### ⚡ Semantic Query Cache

- **Fuzzy Matching** — Uses `difflib.SequenceMatcher` with 0.85 similarity threshold
- **Instant Retrieval** — Identical/similar queries served from cache at $0 cost instantly
- **Intelligent Normalization** — Lowercase, punctuation removal, whitespace normalization
- **LRU Eviction** — Max 500 entries with automatic oldest-first eviction
- **Per-Agent** — Only matches within same agent type
- **Analytics** — Cache hit rate, cost savings displayed in real-time

### 🛡️ 3-Layer Guardrails

**Layer 1 — Input Validation**

- Prompt injection detection (30+ block phrases)
- PII detection (email, phone, SSN, credit card)
- Query length limit (5000 chars)
- Rate limiting (20 req/min)

**Layer 2 — Output Safety**

- Dangerous code detection (os.system, eval, rm -rf, etc.)
- Response length validation
- Uncertainty phrase detection

**Layer 3 — Budget Control**

- Daily cost ceiling ($5.00)
- Per-query billing tracking
- Automatic midnight reset

### 🔄 Automatic Fallback

Three-level fallback strategy ensures reliability:

1. Primary model (configured tier)
2. Alternate model (same tier, different provider)
3. Last resort (LLaMA 8B - reliable universal fallback)

All fallbacks transparent to user with error details displayed.

---

## 📊 Model Registry

| Key          | Model                 | Provider | Tier        | Cost/1K   | Speed   |
| ------------ | --------------------- | -------- | ----------- | --------- | ------- |
| `lite_a`     | Gemini 2.5-Flash-Lite | Google   | 🟢 Lite     | $0.00005  | 400ms   |
| `lite_b`     | GPT-OSS 20B           | Groq     | 🟢 Lite     | $0.000075 | 500ms   |
| `standard_a` | LLaMA 3.1 8B          | Groq     | 🟠 Standard | $0.0001   | 500ms   |
| `standard_b` | GPT-OSS 120B          | Groq     | 🟠 Standard | $0.00015  | 800ms   |
| `pro_a`      | LLaMA 3.3 70B         | Groq     | 🔴 Pro      | $0.0008   | 2500ms  |
| `pro_b`      | Gemini 2.5-Flash      | Google   | 🔴 Pro      | $0.0005   | 2000ms  |
| **Router**   | LLaMA 3.1 8B          | Groq     | —           | Minimal   | Minimal |

**Upgrade chain:** lite_a → lite_b → standard_a → standard_b → pro_a → pro_b

**Tier defaults:** lite → lite_a, standard → standard_a, pro → pro_a

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-router.git
cd multi-agent-router
```

### 2. Set Up Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

- `streamlit>=1.30.0` — Web UI framework
- `litellm>=1.30.0` — LLM API abstraction
- `pandas` — Data processing
- `plotly` — Interactive charts

### 4. Configure API Keys

```bash
# Windows PowerShell
$env:GROQ_API_KEY = "gsk_your_groq_key_here"
$env:GEMINI_API_KEY = "your_gemini_key_here"

# Mac/Linux for this session
export GROQ_API_KEY="gsk_your_groq_key_here"
export GEMINI_API_KEY="your_gemini_key_here"

# Or add to ~/.bashrc / ~/.zshrc for persistence
```

**Get API Keys:**

- **Groq:** https://console.groq.com/keys
- **Gemini:** https://aistudio.google.com/app/apikey

### 5. Run Application

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## 📁 Project Structure

```
multi-agent-router/
├── app.py                           # 🎨 Streamlit UI + main orchestration
├── router.py                        # 🔀 Query classifier (routing logic)
├── agents.py                        # 🤖 Sub-agent executors (Coding/Math/Reasoning)
├── config.py                        # ⚙️  Model registry + API keys + guardrail config
├── guardrails.py                    # 🛡️ 3-layer safety checks
├── analytics.py                     # 📊 CSV logging + cost analysis
├── memory.py                        # 💾 Sessions + semantic cache + export
│
├── sessions/                        # Auto-created
│   └── session_YYYYMMDD_HHMMSS_xxxxx.json
├── query_cache.json                # Auto-created
├── query_logs.csv                  # Auto-created
│
├── requirements.txt
├── README.md                        # This file
├── PRESENTATION.md                  # Detailed technical deep-dive
├── GCP_INTEGRATION_ROADMAP.md      # Production deployment roadmap
└── .gitignore
```

---

## 🧠 How Conversational Memory Works

### Mechanism

Sessions store complete turn history with metadata:

```json
{
  "session_id": "session_20240115_143022_a1b2c3d4",
  "created_at": "2024-01-15T14:30:22.123456",
  "turn_count": 3,
  "agents_used": ["coding", "reasoning"],
  "turns": [
    {
      "turn": 1,
      "user": "Implement a stack in Python",
      "assistant": "class Stack: ...",
      "agent": "coding",
      "model_label": "LLaMA 3.1 8B",
      "tokens": 250,
      "cost": 0.000025
    },
    ...
  ]
}
```

### Memory Injection

When executing current query, history is injected as OpenAI-style messages:

```
[system: Coding Agent Prompt]
[user: "Implement a stack in Python"]
[assistant: "class Stack: ..."]
[user: "Now add minimum tracking in O(1)"]  ← current query
```

LLM understands full context and can properly interpret "it", "the above", "that method", etc.

### Last 5 Exchanges

- Sliding window keeps last 5 turns = 10 messages
- Balances context richness with token efficiency
- Per-agent filtering prevents noise from other agent types

### Agent Handoff

When user upgrades to stronger model:

```
User upgrades: LLaMA 8B → LLaMA 70B

New system prompt includes:
=== CONVERSATION CONTEXT ===
Turn 1: [previous exchange]
Turn 2: [previous exchange]
Turn 3: [previous exchange from previous model]
=== END CONTEXT — Continue here ===

LLaMA 70B gets full conversation and can seamlessly continue
```

---

## ⚡ How the Semantic Cache Works

### Mechanism

```
Query normalization: lowercase, strip punctuation, collapse whitespace

Query 1: "implement binary search in Python"
         → Normalize: "implement binary search in python"
         → Cache MISS → LLM call → store with metadata

Query 2: "implement binary search in Python"
         → Normalize: same
         → Similarity: 1.00 (exact match)
         → Cache HIT → instant return, cost $0.000000 ✅

Query 3: "Implement Binary Search in python"
         → Normalize: same
         → Similarity: 0.99 → Cache HIT ✅

Query 4: "Write binary search – step by step implementation in Python"
         → Normalize: "write binary search step by step implementation in python"
         → Similarity: 0.88 → Cache HIT (above 0.85 threshold) ✅

Query 5: "implement bubble sort in Python"
         → Normalize: "implement bubble sort in python"
         → Similarity: 0.71 → Cache MISS → new LLM call
```

### Smart Filtering

- **Only same agent** — Coding cache doesn't apply to Reasoning queries
- **Min response size** — Won't cache < 50 char responses
- **Per-agent stats** — Track hit rate per agent type

### Configuration

From `memory.py`:

```python
MAX_TURNS          = 5      # last 5 exchanges
CACHE_SIMILARITY   = 0.85   # fuzzy match threshold
MAX_CACHE_ENTRIES  = 500    # cap with LRU
```

---

## 🛡️ Guardrails System

### Layer 1 — Input Validation

```
Empty query           → ❌ Block
Length > 5000 chars   → ⚠️  Truncate + warn
Injection phrases     → ❌ Block + explain
PII detected          → ⚠️  Warn (email, phone, ssn, card)
Rate limit (20/min)   → ❌ Block
```

**30+ Injection Block Phrases:**

- "ignore all instructions", "reveal your system prompt"
- "jailbreak", "bypass your rules", "pretend you are"
- And 25+ more...

### Layer 2 — Output Validation

```
Response < 10 chars   → ⚠️  Warn, suggest upgrade
Dangerous code        → ⚠️  Warn (os.system, eval, rm -rf)
Uncertainty phrases   → ⚠️  Warn ("i'm not sure", "cannot verify")
```

**Dangerous Patterns:**

- Python: `os.system()`, `subprocess.run()`, `eval()`, `exec()`, `__import__()`
- Shell: `rm -rf`, database: `DROP TABLE`, `DELETE FROM`, etc.

### Layer 3 — System Budget

```
Daily cost ceiling    → $5.00 (configurable)
Auto-reset            → Midnight UTC
Cost tracking         → Per-query + daily aggregate
```

---

## 🧪 Example Test Queries

| #   | Query                                                      | Expected Agent | Expected Tier |
| --- | ---------------------------------------------------------- | -------------- | ------------- |
| 1   | What is 25 × 48?                                           | Math           | 🟢 Lite       |
| 2   | Prove that √2 is irrational                                | Math           | 🔴 Pro        |
| 3   | Write a Python function to add two numbers                 | Coding         | 🟢 Lite       |
| 4   | Implement binary search in Python                          | Coding         | 🟠 Standard   |
| 5   | Design a thread-safe LRU cache with TTL expiration         | Coding         | 🔴 Pro        |
| 6   | What is the capital of Japan?                              | Reasoning      | 🟢 Lite       |
| 7   | Compare SQL vs NoSQL for e-commerce                        | Reasoning      | 🟠 Standard   |
| 8   | Analyze microservices vs monolithic for a 5-person startup | Reasoning      | 🔴 Pro        |
| 9   | Solve 3x² - 12x + 9 = 0                                    | Math           | 🟠 Standard   |
| 10  | Implement a sliding window rate limiter with async support | Coding         | 🔴 Pro        |

---

## 💰 Cost Optimization Example

### Simple Query: "What is 2 + 2?"

```
Pro Model (LLaMA 70B)   → Cost: $0.0001  Latency: ~3000ms
Standard (LLaMA 8B)     → Cost: $0.00003 Latency: ~800ms
Lite (Gemini)           → Cost: $0.00003 Latency: ~400ms

Deep Agent selects     → LITE TIER ✅
Savings vs Pro         → ~94% cost reduction + 3x faster
Quality               → Identical for simple arithmetic
```

### Complex Query: "Design a distributed cache with TTL, LRU eviction, and async I/O"

```
Lite (would fail)       → Insufficient reasoning
Standard               → Incomplete solution
Pro (LLaMA 70B)        → Deep Agent selects → BEST QUALITY ✅

No cost savings possible — complexity requires power
```

---

## 🔄 Fallback Strategy

### Why Fallback Matters

External APIs can fail:

- Rate limits (429)
- Quota exceeded
- Service degradation
- Region unavailable

### Three-Level Fallback

**Level 1: Primary Model**

```
Example: lite_a (Gemini Flash-Lite)
Failed? → Try Level 2
```

**Level 2: Same-Tier Alternate**

```
Example: lite_b (GPT-OSS 20B by Groq)
If lite_a fails → automatically try lite_b
Failed? → Try Level 3
```

**Level 3: Last Resort**

```
Always falls back to: lite_b (GPT-OSS 20B)
Guaranteed to succeed (Groq is very reliable)
User sees: "Primary model failed, used fallback ⚠️"
```

All handled transparently. User sees results + info about which fallback was used.

---

## ☁️ Deployment

### Local Development

```bash
streamlit run app.py
```

### Streamlit Cloud

1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect repo → create app → set to app.py
4. Add secrets:

```
GROQ_API_KEY = "gsk_..."
GEMINI_API_KEY = "..."
```

5. Deploy → get shareable URL

### Production (GCP)

See `GCP_INTEGRATION_ROADMAP.md` for Cloud Run, Vertex AI, BigQuery, etc.

---

## 🛠️ Tech Stack

| Component           | Technology    | Version  |
| ------------------- | ------------- | -------- |
| **Frontend**        | Streamlit     | 1.30+    |
| **LLM API**         | LiteLLM       | 1.30+    |
| **Language**        | Python        | 3.9+     |
| **Primary LLM**     | Groq (LLaMA)  | 3.1, 3.3 |
| **Fast LLM**        | Google Gemini | 2.5      |
| **Data Processing** | Pandas        | Latest   |
| **Visualization**   | Plotly        | Latest   |

---

## 📚 Documentation

- **README.md** (this file) — Quick start, features, usage
- **PRESENTATION.md** — Deep technical architecture, component details, workflow walkthroughs
- **GCP_INTEGRATION_ROADMAP.md** — Production deployment on Google Cloud

---

## 🔮 Future Enhancements

- [ ] Additional agents (web search, code executor, summarizer)
- [ ] User feedback system (thumbs up/down)
- [ ] Advanced analytics (cost trends, performance metrics)
- [ ] Authentication + multi-user support
- [ ] A/B testing between model tiers
- [ ] GCP integration (Cloud Run, Vertex AI, BigQuery)
- [ ] Vector database for semantic search
- [ ] Custom agent creation framework



## 🤝 Contributing

Contributions welcome! Areas of interest:

- New agents (search, code execution, data analysis)
- Additional LLM providers
- Enhanced analytics
- Deployment templates (Docker, Kubernetes)

Please open an issue or PR to discuss improvements.

---

## 💡 Questions?

Refer to `PRESENTATION.md` for deep technical details on:

- Router algorithm and classification logic
- Agent system prompts and execution flow
- Memory and cache implementation details
- Guardrails architecture
- Cost calculation methodology
- Error handling strategies
