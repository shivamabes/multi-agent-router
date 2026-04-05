# 🚀 GCP Integration Roadmap — From Prototype to Production

## Executive Summary

Deep Agent v2.0 is currently running as a **prototype on Streamlit Cloud**, designed for single-user exploration. To scale to production with 1000+ concurrent users, enterprise-grade reliability, and complete observability, we provide this roadmap for GCP integration.

**Current State:** Prototype (local + Streamlit Cloud)

- Single instance
- External APIs
- No logging/analytics
- Limited users

**Target State:** Production on GCP (Cloud Run, Vertex AI, BigQuery)

- Auto-scaling
- Complete observability
- Analytics suite
- 1000+ concurrent users
- 99.95%+ uptime

---

## Current Architecture

```
┌─────────────────────────┐
│   Streamlit Cloud       │
│   Single Instance       │
│                         │
│  app.py / agents.py     │
│  (all Python code)      │
└────────────┬────────────┘
             │
    ┌────────┴────────────────┬──────────┐
    │                         │          │
    ▼                         ▼          ▼
┌────────────┐      ┌──────────────┐  ┌──────────┐
│ Groq API   │      │ Gemini API   │  │ Local    │
│ (External) │      │ (External)   │  │ Storage  │
└────────────┘      └──────────────┘  │ (Limits) │
                                       └──────────┘

Limitations:
- No auto-scaling
- No built-in monitoring
- No enterprise logging
- Single point of failure
- Limited to 1-2 concurrent users
- Costs not optimized
```

---

## GCP Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USERS (WORLDWIDE)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────────────────┐
              │  Cloud Load Balancer │
              │  + CDN               │
              └──────────┬───────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │Cloud Run│      │Cloud Run│      │Cloud Run│
   │ (US)    │      │(Europe) │      │(Asia)   │
   │Auto 0-100      │Auto 0-100      │Auto 0-100
   └────┬────┘      └────┬────┘      └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   ┌──────────┐     ┌──────────┐    ┌──────────┐
   │ Secret   │     │ Firestore│   │  Redis   │
   │ Manager  │     │ (Sessions│   │  (Cache) │
   │(API Keys)│     │+Metadata)│   │ (Semantic)
   └──────────┘     └──────────┘   └──────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                   ┌────────────┐
                   │  Pub/Sub   │
                   │(Events)    │
                   └────┬───────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐    ┌────────────┐  ┌──────────┐
   │BigQuery │    │Vertex AI   │  │ Cloud    │
   │(Analytics)  │(Model Hub) │  │Logging   │
   └─────────┘    └────────────┘  └──────────┘
        │
        ▼
   ┌──────────────┐
   │ Looker Studio│
   │ (Dashboards) │
   └──────────────┘

Benefits:
✅ Auto-scales to 1000+ instances
✅ Global CDN for low latency
✅ Complete observability
✅ Enterprise security
✅ Managed services (no ops burden)
✅ Payment per actual usage
✅ Built-in redundancy
```

---

## Migration Phases

### Phase 0: Preparation (Week 1)

**Tasks:**

1. Set up GCP project and billing
2. Configure Cloud Build for CI/CD
3. Create Dockerfile
4. Test deployment pipeline locally

**Deliverables:**

- GCP project with APIs enabled
- Container registry configured
- Deployment automation ready

### Phase 1: Cloud Run Deployment (Week 2)

**Objective:** Get app running on Cloud Run with auto-scaling

**Steps:**

1. **Create Dockerfile**

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PORT 8080
CMD ["streamlit", "run", "app.py", \
     "--server.port=${PORT}", \
     "--server.address=0.0.0.0"]
```

2. **Build and push container**

```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/deep-agent:latest
```

3. **Deploy to Cloud Run**

```bash
gcloud run deploy deep-agent \
  --image gcr.io/PROJECT-ID/deep-agent:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 10 \
  --min-instances 1 \
  --max-instances 100 \
  --set-env-vars GROQ_API_KEY=$GROQ_API_KEY,GEMINI_API_KEY=$GEMINI_API_KEY
```

4. **Configure auto-scaling**
   - Min instances: 1 (saves cost)
   - Max instances: 100 (handles load)
   - Concurrency per instance: 10
   - CPU throttling: disabled
   - Memory: 2GB per instance

**Result:** App accessible at `https://deep-agent-xxxxx.run.app`

### Phase 2: Data Persistence (Week 3)

**Objective:** Move from local files to managed databases

**1. Firestore for Sessions**

```yaml
Collection: sessions
- Document ID: session_id
- Data:
    session_id: string
    created_at: timestamp
    last_active: timestamp
    turn_count: integer
    agents_used: array
    turns: array
      - turn: integer
      - user: string
      - assistant: string
      - metrics: {...}
```

**2. Cloud Storage for Cache**

- Bucket: `deep-agent-cache`
- File: `query_cache.json`
- Or stream to BigQuery for better querying

**3. BigQuery for Analytics**

```sql
Table: query_analytics
- timestamp
- session_id
- query
- agent
- tier
- cost
- latency_ms
- tokens
- cache_hit
- context_used
```

**Code Changes:**

```python
# memory.py update
from google.cloud import firestore

db = firestore.Client()

def _load_session(session_id):
    doc = db.collection("sessions").document(session_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

def _save_session(session_id, data):
    db.collection("sessions").document(session_id).set(data)
```

### Phase 3: Caching & Speed (Week 4)

**1. Redis on Memorystore**

```bash
gcloud redis instances create deep-agent-cache \
  --size 2 \
  --region us-central1 \
  --tier standard \
  --redis-version 7.0
```

**2. Use for semantic cache**

```python
import redis

redis_cli = redis.Redis(host="10.0.0.3", port=6379)

def cache_lookup(query, agent):
    key = f"cache:{agent}:{normalize(query)}"
    result = redis_cli.get(key)
    if result:
        return json.loads(result)
    return None

def cache_store(query, agent, response):
    key = f"cache:{agent}:{normalize(query)}"
    redis_cli.setex(key, 86400*7, json.dumps(response))  # 7-day TTL
```

**Benefits:**

- Fuzzy matching now instant (~1ms)
- Cache survives node restarts
- Shared across all instances
- Automatic expiration

### Phase 4: Observability (Week 5)

**1. Cloud Logging**

```python
from google.cloud import logging as cloud_logging

logging_client = cloud_logging.Client()
logging_client.setup_logging()

logger.info("Query routed", extra={
    "query": query,
    "agent": agent,
    "tier": tier,
    "latency_ms": latency,
})
```

**2. Cloud Monitoring**

- Create dashboard for
  - Queries per second
  - Latency p50/p95/p99
  - Error rate
  - Cost per query
  - Cache hit rate
  - Fallback usage

**3. Uptime Checks**

- Monitor endpoint every 5 min
- Alert if < 99.95% uptime

### Phase 5: Advanced Features (Week 6+)

**1. Pub/Sub for Events**

- Publish query events
- Subscribe to analytics jobs
- Decouple processing

**2. Cloud Tasks for Async**

- Queue long-running operations
- Retry with exponential backoff

**3. Looker Studio for Analytics**

- Connect BigQuery
- Create executive dashboard
- Share with stakeholders

---

## Deployment Configuration

### Environment Variables

```
GROQ_API_KEY = "gsk_..."
GEMINI_API_KEY = "..."

GCP_PROJECT_ID = "your-project"
FIRESTORE_COLLECTION = "sessions"
BIGQUERY_DATASET = "analytics"
BIGQUERY_TABLE = "queries"
REDIS_HOST = "10.0.0.3"
REDIS_PORT = "6379"

LOG_LEVEL = "INFO"
CACHE_TTL_DAYS = 7
SESSION_TTL_DAYS = 30
MAX_DAILY_COST = 50.0  # 10x higher for prod
```

### Secrets Manager Setup

```bash
# Store API keys securely
gcloud secrets create groq-api-key --data-file=- <<< "gsk_..."
gcloud secrets create gemini-api-key --data-file=- <<< "..."

# Reference in Cloud Run
gcloud run deploy deep-agent \
  --set-env-vars GROQ_API_KEY=$(gcloud secrets versions access latest \
    --secret="groq-api-key")
```

### IAM Permissions

Grant Cloud Run service account:

- `roles/firestore.user` (Firestore access)
- `roles/storage.objectUser` (Cloud Storage)
- `roles/bigquery.dataEditor` (BigQuery writes)
- `roles/redis.editor` (Memorystore)
- `roles/secretmanager.secretAccessor` (Secrets)
- `roles/logging.logWriter` (Cloud Logging)

---

## Database Schemas

### Firestore: Sessions

```
Collection: sessions
├─ Document: session_20240115_143022_a1b2c3d4
│  ├─ session_id: "session_20240115_143022_a1b2c3d4"
│  ├─ created_at: Timestamp
│  ├─ last_active: Timestamp
│  ├─ turn_count: 5
│  ├─ agents_used: ["coding", "reasoning"]
│  └─ turns: [
│      {
│        turn: 1,
│        user: "Implement a stack",
│        assistant: "class Stack: ...",
│        model_label: "LLaMA 3.1 8B",
│        tokens: 250,
│        cost: 0.000025
│      },
│      ...
│    ]
```

### BigQuery: Query Analytics

```sql
CREATE TABLE analytics.queries (
  timestamp TIMESTAMP,
  session_id STRING,
  query STRING,
  agent STRING,
  complexity STRING,
  tier STRING,
  model_key STRING,
  model_label STRING,
  routing_latency_ms FLOAT64,
  agent_latency_ms FLOAT64,
  total_latency_ms FLOAT64,
  tokens INTEGER,
  cost FLOAT64,
  fallback_used BOOLEAN,
  cache_hit BOOLEAN,
  history_turns INTEGER,
  context_used BOOLEAN,
)
PARTITION BY timestamp;
CREATE INDEX ON queries (session_id, timestamp);
```

---

## Cost Estimation

### Monthly Production Load (1000 concurrent users)

**Compute:**

- Cloud Run: pay-per-use, ~$50-150/month
- Firestore: ~$20-50/month
- Cloud Storage: ~$1-5/month
- Redis (Memorystore): ~$50-80/month
- Cloud Logging: ~$10-30/month
- BigQuery: ~$20-50/month (analytics queries)

**Total Infra Cost:** ~$150-350/month

**LLM Costs** (biggest):

- Assuming 100K queries/day
- Avg 500 tokens = 50M tokens/day
- At mixed rates (avg $0.0002/1K) = $10/day = $300/month

**Total Monthly:** ~$450-650/month infrastructure + LLM
**Per Query:** ~$0.0002 average (after caching)

---

## Monitoring & Alerting

### Key Metrics

**Latency:**

- p50 < 1000ms
- p95 < 3000ms
- p99 < 5000ms

**Availability:**

- Uptime > 99.95%
- Error rate < 0.1%

**Cost:**

- Cost per query < $0.0005 avg
- Daily spend < $15

**Cache:**

- Hit rate > 20%
- Miss rate < 80%

### Alert Rules

```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 1%
    action: Page on-call

  - name: HighLatency
    condition: latency_p95 > 3000ms
    action: Notify Slack

  - name: DailyBudgetExceeded
    condition: daily_cost > $15
    action: Email alerts

  - name: CacheHitRateLow
    condition: cache_hit_rate < 10%
    action: Email alerts
```

---

## Migration Checklist

- [ ] GCP project setup + billing
- [ ] Dockerfile creation + testing
- [ ] Cloud Build pipeline configured
- [ ] Cloud Run deployment working
- [ ] Load balancer configured
- [ ] Firestore collections created
- [ ] BigQuery dataset + tables created
- [ ] Redis instance running
- [ ] Secret Manager secrets stored
- [ ] IAM roles configured
- [ ] Cloud Logging enabled
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] Documentation updated
- [ ] Team trained on monitoring
- [ ] Production launch plan finalized

---

## Rollback Plan

If production issues occur:

1. **Immediate:** Route traffic back to Streamlit Cloud backup
2. **Within 1 hour:** Identify root cause via Cloud Logging
3. **Fix:** Update code, rebuild container, re-deploy
4. **Validate:** Test in staging before production
5. **Monitor:** Watch metrics closely post-rollback

---

## Future Enhancements

- [ ] Multi-region deployment (reduce latency)
- [ ] Kubernetes for complex microservices
- [ ] Machine learning model serving (Vertex AI)
- [ ] Custom fine-tuned models
- [ ] Advanced analytics dashboards (Looker)
- [ ] Custom agent framework
- [ ] Vector search for semantic retrieval
- [ ] Real-time A/B testing

---

## Conclusion

This roadmap enables Deep Agent v2.0 to scale from prototype (1-2 users) to production (1000+ concurrent users) while maintaining quality, cost-efficiency, and observability.

**Timeline:** 6 weeks to full production
**Cost:** $150-350/month infrastructure
**Uptime Target:** 99.95%
**Scalability:** 1000+ concurrent users

Ready to build! 🚀
