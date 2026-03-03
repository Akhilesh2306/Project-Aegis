# Project Aegis — Autonomous Compliance Agent
## Architecture & Design Document

---

## 1. Problem Statement

Contract compliance reviews traditionally involve multiple legal, procurement, and policy teams manually cross-referencing contract clauses against internal policies, regulatory requirements, and external standards. This process takes **several days** and is prone to inconsistency.

**Goal:** Build an autonomous, production-grade AI agent that:
- Ingests contracts (PDF/DOCX)
- Retrieves relevant internal policies and external regulations
- Identifies non-compliant clauses
- Drafts remediation suggestions
- Produces a structured compliance report
- Reduces review cycle from days to **hours**

---

## 2. High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                           │
│          REST API  /  Async Webhook  /  UI Dashboard          │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                      ORCHESTRATION LAYER                      │
│                LangGraph Compliance Agent Graph               │
│                                                               │
│  [Ingest] → [Parse] → [Policy Retrieval] → [Compliance       │
│   Check] → [Web Search] → [Clause Drafting] → [Report Gen]   │
└──────────┬──────────────────────────────────────┬────────────┘
           │                                      │
┌──────────▼──────────┐              ┌────────────▼────────────┐
│   TOOL LAYER        │              │   MEMORY & STATE LAYER  │
│ - Document Parser   │              │ - Agent State (Redis)   │
│ - Policy RAG Tool   │              │ - Conversation Memory   │
│ - Web Search Tool   │              │ - Run Checkpoints       │
│ - Clause Drafter    │              │ - Vector Store (Chroma/ │
│ - Report Builder    │              │   Pinecone)             │
└──────────┬──────────┘              └────────────┬────────────┘
           │                                      │
┌──────────▼──────────────────────────────────────▼────────────┐
│                    INFRASTRUCTURE LAYER                       │
│       PostgreSQL │ Redis │ S3/MinIO │ LLM Provider (OpenAI)  │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. LangGraph Agent Design

### 3.1 Agent State

The central `ComplianceState` TypedDict is threaded through every node:

| Field | Type | Purpose |
|---|---|---|
| `contract_id` | str | Unique job identifier |
| `raw_text` | str | Extracted contract text |
| `clauses` | List[Clause] | Parsed, segmented clauses |
| `policy_chunks` | List[PolicyChunk] | Retrieved policy context |
| `web_results` | List[WebResult] | External regulation snippets |
| `findings` | List[Finding] | Non-compliant clause findings |
| `drafted_clauses` | List[DraftedClause] | Suggested remediated text |
| `report` | ComplianceReport | Final output artifact |
| `messages` | List[BaseMessage] | LLM conversation history |
| `error` | Optional[str] | Error propagation |
| `next_node` | Optional[str] | Conditional routing override |

### 3.2 Graph Nodes

```
START
  │
  ▼
[ingest_node]         — Download & extract raw text from S3
  │
  ▼
[parse_node]          — Segment contract into labeled clauses
  │
  ▼
[policy_retrieval_node] — RAG lookup against internal policy store
  │
  ▼
[web_search_node]     — Search for relevant external regulations
  │
  ▼
[compliance_check_node] — LLM + tools to flag non-compliant clauses
  │
  ├── [all_compliant] ──────────────────────────────────┐
  │                                                      │
  ▼                                                      │
[clause_drafting_node] — Regenerate/fix flagged clauses │
  │                                                      │
  ▼                                                      │
[report_generation_node] ◄─────────────────────────────┘
  │
  ▼
END
```

### 3.3 Conditional Edges

- After `compliance_check_node`: if `findings` is empty → skip to `report_generation_node`, else → `clause_drafting_node`
- After any node: if `error` is set → `error_handler_node` (retry up to N times, then fail gracefully)
- `compliance_check_node` runs as a **ReAct loop** (reason + act) — the LLM can invoke tools iteratively before emitting findings

### 3.4 Tool Definitions

| Tool | Description | Implementation |
|---|---|---|
| `retrieve_policies` | Semantic search over internal policy vector store | LangChain retriever wrapper |
| `web_search` | Fetch external regulations, recent case law | Tavily / SerpAPI |
| `get_clause_context` | Fetch surrounding contract context for a clause | In-memory lookup |
| `draft_clause` | Generate a compliant replacement clause | LLM sub-chain |
| `lookup_regulation` | Fetch specific regulation by ID from database | DB query tool |

---

## 4. Folder Structure

```
project-aegis/
│
├── api/                         # FastAPI application
│   ├── main.py                  # App entrypoint, lifespan, routers
│   ├── routers/
│   │   ├── contracts.py         # POST /contracts/analyze
│   │   └── reports.py           # GET /reports/{job_id}
│   ├── models/
│   │   ├── request.py           # Pydantic request schemas
│   │   └── response.py          # Pydantic response schemas
│   └── dependencies.py          # DI: DB, Redis, agent factory
│
├── agent/                       # LangGraph agent (core logic)
│   ├── graph.py                 # Graph definition & compilation
│   ├── state.py                 # ComplianceState TypedDict
│   ├── nodes/
│   │   ├── ingest.py
│   │   ├── parse.py
│   │   ├── policy_retrieval.py
│   │   ├── web_search.py
│   │   ├── compliance_check.py
│   │   ├── clause_drafting.py
│   │   ├── report_generation.py
│   │   └── error_handler.py
│   ├── tools/
│   │   ├── policy_retriever.py
│   │   ├── web_search_tool.py
│   │   ├── clause_drafter.py
│   │   └── regulation_lookup.py
│   ├── prompts/
│   │   ├── compliance_check.yaml
│   │   ├── clause_drafting.yaml
│   │   └── report_generation.yaml
│   └── checkpointer.py          # Redis/Postgres checkpointer setup
│
├── services/
│   ├── document_parser.py       # PDF/DOCX extraction (pypdf, python-docx)
│   ├── vector_store.py          # Chroma/Pinecone abstraction
│   ├── storage.py               # S3/MinIO abstraction
│   └── llm_factory.py           # LLM provider abstraction
│
├── workers/                     # Async background processing
│   ├── celery_app.py            # Celery + Redis broker config
│   └── tasks.py                 # analyze_contract Celery task
│
├── db/
│   ├── models.py                # SQLAlchemy ORM models
│   ├── migrations/              # Alembic migrations
│   └── session.py               # Async DB session factory
│
├── config/
│   ├── settings.py              # Pydantic BaseSettings
│   └── logging.py               # Structured JSON logging
│
├── tests/
│   ├── unit/
│   │   ├── test_nodes.py
│   │   └── test_tools.py
│   ├── integration/
│   │   └── test_graph.py
│   └── fixtures/
│       └── sample_contracts/
│
├── infra/
│   ├── docker-compose.yml       # Local dev stack
│   ├── Dockerfile
│   └── k8s/                     # Kubernetes manifests (optional)
│
├── scripts/
│   ├── ingest_policies.py       # One-time policy vectorization
│   └── seed_db.py
│
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 5. Key Implementation Steps

### Phase 1 — Foundation (Week 1–2)
1. Set up FastAPI skeleton with async lifespan, health check, and structured logging
2. Define `ComplianceState` and all Pydantic data models
3. Implement document parser service (PDF → text, DOCX → text, clause segmentation heuristics)
4. Stand up PostgreSQL + Redis + Chroma locally via Docker Compose

### Phase 2 — Agent Core (Week 2–3)
5. Build and wire all LangGraph nodes (stub implementations first)
6. Implement `compliance_check_node` as a full ReAct agent with tool binding
7. Integrate policy vector store with semantic retrieval tool
8. Integrate Tavily/SerpAPI for web search tool
9. Implement `clause_drafting_node` as an LLM sub-chain with structured output

### Phase 3 — Persistence & Reliability (Week 3–4)
10. Configure LangGraph `RedisCheckpointer` for mid-run state persistence and resumability
11. Wrap graph execution in Celery task for async processing
12. Add retry logic on nodes with exponential backoff
13. Implement `error_handler_node` with graceful degradation

### Phase 4 — API & Output (Week 4)
14. Wire Celery task to `POST /contracts/analyze` endpoint (returns `job_id`)
15. Implement `GET /reports/{job_id}` with polling or webhook callback
16. Build report generation node to produce structured JSON + DOCX output
17. Store completed reports in S3/MinIO

### Phase 5 — Production Hardening (Week 5)
18. Add PII redaction before sending text to external LLM APIs
19. Add token budget guardrails per node to prevent runaway costs
20. Set up Prometheus metrics (node latency, tool call counts, error rates)
21. Write integration tests using a set of known-compliant and non-compliant fixture contracts

---

## 6. Data Flow Diagram

```
Contract Upload (S3)
        │
        ▼
   [ingest_node]
   Extract text → raw_text
        │
        ▼
   [parse_node]
   Segment → clauses[]  (numbered, typed: liability/IP/payment/termination…)
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
[policy_retrieval_node]              [web_search_node]
 RAG → policy_chunks[]               Search → web_results[]
        │                                      │
        └───────────────┬──────────────────────┘
                        ▼
          [compliance_check_node]  ← ReAct loop
           LLM + Tools → findings[]
           (clause_id, policy_ref, severity, reason)
                        │
              ┌─────────┴─────────┐
         findings?              no findings
              │                    │
              ▼                    │
  [clause_drafting_node]           │
   LLM → drafted_clauses[]         │
              │                    │
              └─────────┬──────────┘
                        ▼
          [report_generation_node]
           → ComplianceReport (JSON + DOCX)
           → Stored to S3, status written to DB
```

---

## 7. Production Best Practices

### Reliability
- **Checkpointing:** Use LangGraph's `PostgresSaver` or `RedisSaver` so interrupted runs can be resumed from any node without re-processing
- **Idempotency:** Each node checks if its output already exists in state before re-running — safe for retries
- **Dead letter queue:** Celery tasks that exhaust retries are pushed to a DLQ for manual inspection

### Performance
- **Parallel tool calls:** `compliance_check_node` invokes `retrieve_policies` and `web_search` in parallel using `asyncio.gather` before the LLM reasoning step
- **Chunked processing:** Large contracts are processed clause-batch by clause-batch to stay within LLM context limits
- **Vector store caching:** Policy embeddings are pre-computed and cached; only re-indexed when policies change

### Security & Compliance
- **PII scrubbing:** Named entity recognition pass before any text leaves the internal network to an LLM API
- **Audit trail:** Every node transition, tool call, and LLM response is logged with `contract_id` and `run_id` for full traceability
- **Secret management:** All API keys via environment variables + AWS Secrets Manager / Vault in production; no secrets in code

### Cost Control
- **Token budgets:** Each node has a `max_tokens` cap; the agent summarizes intermediate context rather than passing full history
- **LLM tiering:** Fast/cheap model for parsing and retrieval nodes; capable model only for compliance check and drafting
- **Caching:** LLM responses for identical clause + policy pairs are cached in Redis with a TTL

### Observability
- **Structured logging:** JSON logs with `contract_id`, `node`, `duration_ms`, `token_usage` on every operation
- **Distributed tracing:** LangSmith integration for full agent trace visualization
- **Metrics:** Prometheus + Grafana dashboards tracking p50/p95 node latency, compliance finding rates, and error rates

### Testing Strategy
- **Unit tests:** Each node and tool tested in isolation with mocked LLM and tool outputs
- **Graph integration tests:** Full graph runs against a curated set of fixture contracts with known expected findings
- **Contract regression suite:** A golden set of contracts that must always produce deterministic severity classifications

---

## 8. Technology Stack Summary

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph (LangChain ecosystem) |
| LLM Provider | OpenAI GPT-4o (swappable via factory) |
| API Framework | FastAPI + Uvicorn |
| Task Queue | Celery + Redis |
| State Persistence | Redis (short-term) + PostgreSQL (long-term) |
| Vector Store | Chroma (dev) / Pinecone (prod) |
| Document Parsing | pypdf, python-docx, pdfplumber |
| Web Search | Tavily API |
| Object Storage | MinIO (dev) / AWS S3 (prod) |
| Observability | LangSmith + Prometheus + Grafana |
| Containerization | Docker + Docker Compose (dev) / K8s (prod) |

---

*Document version 1.0 — Project Aegis*
