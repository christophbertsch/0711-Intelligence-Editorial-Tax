# Editorial Engine

A comprehensive editorial agent platform for discovering, processing, and ingesting web knowledge into the 0711 Agent System. This platform continuously discovers, verifies, and ingests web knowledge using Tavily for live web access and LLMs for understanding, quality control, and summaries.

## Architecture Overview

**Dataflow**: Sources → Discovery (Tavily) → Fetch/Extract → Dedup/Canon → Classify/NER → Chunk/Embed → Summarize → Fact-Check → Ingest (0711: SQL/vector/graph) → Hybrid Search UI → Monitor/Refresh

### Core Technologies

- **LLMs**: OpenAI/Anthropic/Local (behind a thin provider interface)
- **Search/Web**: Tavily search/extract (with allow/deny lists & freshness filters)
- **Orchestration**: Celery workers + Redis broker + Flower dashboard
- **Storage**: 0711 API for everything persisted (no bespoke DB in this app)
- **Observability**: Prometheus + Grafana + structured JSON logs
- **Auth/Secrets**: .env + Docker secrets

## Project Structure

```
editorial-engine/
├── apps/
│   ├── orchestrator/            # FastAPI control plane + Celery beat (schedules)
│   ├── worker-discovery/        # runs Tavily discovery tasks
│   ├── worker-intake/           # fetch, extract, canonicalize, dedupe
│   ├── worker-understanding/    # classify, NER/link, chunk, embed
│   ├── worker-editorial/        # summarize, SEO/schema, fact-check
│   ├── worker-ingestion/        # 0711 writes (docs, vectors, graph), CSV-bulk
│   └── ui-search/               # end-user Search UI (Next.js) that calls 0711 /v1/search
├── libs/
│   ├── llm/                     # provider-agnostic LLM wrapper
│   ├── tavily_client/           # small typed client for Tavily
│   ├── seven011_client/         # typed client for 0711 API
│   └── common/                  # schemas, errors, metrics, robots.txt helper, pdf->text
├── configs/
│   ├── verticals/
│   │   ├── generic.yaml         # vertical-agnostic defaults
│   │   └── tax_de.yaml          # German tax law specialization
│   └── policies/
│       ├── sources-allowlist.txt
│       └── sources-denylist.txt
└── deploy/
    ├── docker-compose.yaml
    ├── grafana/
    └── prometheus/
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- API keys for:
  - Tavily API
  - OpenAI or Anthropic
  - 0711 Agent System

### Setup

1. **Clone and configure**:
   ```bash
   cd editorial-engine
   cp .env.example .env
   ```

2. **Edit `.env` with your API keys**:
   ```bash
   TAVILY_API_KEY=tvly-***
   OPENAI_API_KEY=***
   LLM_PROVIDER=openai
   VERTICAL_CONFIG=./configs/verticals/generic.yaml
   SEVEN011_BASE_URL=http://34.40.104.64:8000
   SEVEN011_API_KEY=***
   REDIS_URL=redis://redis:6379/0
   COLLECTION=vertical_generic
   ```

3. **Start the platform**:
   ```bash
   cd deploy
   docker compose up --build
   ```

### Access Points

- **Flower Dashboard**: http://localhost:5555 (monitor Celery tasks)
- **Search UI**: http://localhost:3000 (end-user search interface)
- **Orchestrator API**: http://localhost:8080 (control plane)
- **Prometheus**: http://localhost:9090 (metrics)
- **Grafana**: http://localhost:3001 (dashboards, admin/admin)

## Pipeline Stages

### 1. Discovery (Tavily)
- Expands queries from vertical configuration
- Searches with freshness filters and domain allow/deny lists
- Respects rate limits and robots.txt

### 2. Intake
- Fetches content with proper headers and caching
- Extracts text from HTML/PDF
- Canonicalizes URLs and deduplicates content

### 3. Understanding
- Classifies documents by type, audience, jurisdiction
- Extracts named entities and relationships
- Chunks text by semantic boundaries
- Generates embeddings for vector search

### 4. Editorial
- Generates neutral summaries with citations
- Extracts factual claims for verification
- Fact-checks claims using Tavily corroboration
- Routes questionable content to human review

### 5. Ingestion
- Creates collections in 0711 Agent System
- Upserts documents with full metadata
- Updates knowledge graph with entities/relationships
- Triggers reindexing for hybrid search

## Vertical Configuration

The platform supports domain-specific configurations through YAML files:

### Generic Configuration (`configs/verticals/generic.yaml`)
- Language-agnostic defaults
- Basic document types and entity schemas
- Standard quality thresholds

### German Tax Law (`configs/verticals/tax_de.yaml`)
- Specialized for German tax authorities
- Curated source whitelist (BMF, BFH, Gesetze-im-Internet, etc.)
- Tax-specific entity patterns and relationships
- Form mapping for ELSTER integration

## 0711 Agent System Integration

The platform integrates with the following 0711 API endpoints:

- **Collections**: `GET/POST /v1/collections` - Manage document collections
- **Documents**: `POST /v1/documents/`, `GET /v1/documents/{id}`, `POST /v1/documents/{id}/reindex`
- **Search**: `POST /v1/search` - Hybrid vector + keyword search
- **Graph**: `POST /v1/graph/query`, `GET /v1/graph/entities/{name}/related`
- **CSV Import**: Bulk data ingestion pipeline

## Security & Compliance

- **Source Validation**: Respects robots.txt and site ToS
- **Content Filtering**: PII scrubbing, profanity filters, malware detection
- **Rate Limiting**: Per-domain limits with burst allowances
- **Prompt Security**: Injection hardening for LLM interactions
- **Network Security**: Egress allow-list to Tavily & 0711 only

## Monitoring & Observability

### Metrics (Prometheus)
- Task execution times and success rates
- Queue depths and processing throughput
- API response times and error rates
- Resource utilization per worker type

### Dashboards (Grafana)
- Pipeline health overview
- Worker performance metrics
- Content quality trends
- Source reliability scores

### Logging
- Structured JSON logs with correlation IDs
- Per-task execution traces
- Error aggregation and alerting

## Scaling & Operations

### Horizontal Scaling
- Independent worker scaling per queue type
- Redis cluster support for high availability
- Load balancing across multiple orchestrator instances

### Data Management
- Idempotent writes with content hashing
- Incremental updates with change detection
- Automated cleanup of superseded documents

### Quality Assurance
- Multi-source fact verification
- Human review workflows for edge cases
- Continuous quality scoring and feedback loops

## Development

### Adding New Verticals

1. Create a new YAML configuration in `configs/verticals/`
2. Define domain-specific sources, patterns, and rules
3. Update environment variables to use the new config
4. Test with representative queries

### Extending Workers

Each worker is independently deployable and can be extended:

```python
# Add new task to any worker
@celery.task(name="tasks.{worker}.{task_name}", bind=True)
def new_task(self, payload):
    # Your processing logic
    pass
```

### Custom LLM Providers

Implement the provider interface in `libs/llm/providers/`:

```python
class CustomProvider(BaseLLMProvider):
    def classify_json(self, text: str) -> dict:
        # Your implementation
        pass
```

## Troubleshooting

### Common Issues

1. **Worker not processing tasks**: Check Redis connection and queue names
2. **0711 API errors**: Verify API key and endpoint URL
3. **Tavily rate limits**: Adjust rate limiting in vertical config
4. **Memory issues**: Reduce worker concurrency or chunk sizes

### Debug Mode

Enable debug logging:
```bash
export CELERY_LOG_LEVEL=DEBUG
docker compose up
```

### Health Checks

All services include health checks accessible via:
- Orchestrator: `GET /health`
- Workers: Monitor via Flower dashboard
- External APIs: Automatic retry with exponential backoff

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure security best practices

## License

[Your License Here]