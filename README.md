# Sales Call Insight API

A production-ready FastAPI application for analyzing sales call transcripts and generating comprehensive deal intelligence.

## Features

- **Transcript Analysis**: Upload and analyze sales call transcripts
- **Deal Scoring**: AI-powered deal health scoring (0-100)
- **Intent Classification**: Buyer intent detection (researching/comparing/ready_to_buy/stalled)
- **Objection Detection**: Identify objections with recommended responses
- **Talk Ratio Analysis**: Measure rep vs prospect engagement
- **Sentiment Timeline**: Track engagement throughout the call
- **Entity Extraction**: Identify decision makers, budget, competitors
- **Coachable Moments**: AI-generated coaching insights
- **Team Dashboards**: Performance analytics for reps and managers
- **Async Processing**: Celery-powered background processing
- **Usage Tracking**: Tier-based usage limits and monitoring

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Database**: PostgreSQL + SQLAlchemy
- **Cache**: Redis
- **Queue**: Celery + Redis
- **AI**: OpenAI GPT-4o-mini + spaCy + NLTK
- **Authentication**: JWT with role-based access
- **Monitoring**: Prometheus metrics + Flower (Celery)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd sales-call-insight-api
```

2. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other settings
```

3. Start the services
```bash
docker-compose up -d
```

4. Initialize the database
```bash
docker-compose exec api python -c "
from app.db.postgres import engine
from app.db.models import Base
Base.metadata.create_all(bind=engine)
print('Database initialized')
"
```

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Flower (Celery Monitor)**: http://localhost:5555

## API Endpoints

### Authentication
- `POST /auth/login` - Login and get access token
- `POST /auth/register` - Register new rep/team
- `GET /auth/me` - Get current user info

### Calls
- `POST /calls/upload` - Upload call transcript
- `POST /calls/analyze` - Analyze call (by ID or inline)
- `GET /calls/{call_id}/insights` - Get analysis results
- `GET /calls/` - List user's calls

### Dashboards
- `GET /dashboard/rep/{rep_id}` - Rep performance dashboard
- `GET /dashboard/team` - Team performance dashboard
- `GET /dashboard/rep/{rep_id}/trends` - Performance trends

### Health & Monitoring
- `GET /health` - Comprehensive health check
- `GET /metrics` - Prometheus metrics
- `GET /status` - Simple status endpoint

## Usage Examples

### Upload and Analyze a Call

```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "john@company.com", "password": "password123"}'

# Upload transcript
curl -X POST "http://localhost:8000/calls/upload" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Rep: Hi, thanks for taking the time today...\nProspect: Thanks for reaching out...",
    "metadata": {
      "prospect_company": "Acme Corp",
      "call_type": "discovery",
      "deal_value": 50000
    }
  }'

# Get analysis results
curl -X GET "http://localhost:8000/calls/1/insights" \
  -H "Authorization: Bearer <token>"
```

### Sample Response

```json
{
  "call_id": 1,
  "deal_score": 78.5,
  "intent_classification": "ready_to_buy",
  "detected_objections": [
    {
      "text": "This seems expensive",
      "timestamp": 0.65,
      "category": "price",
      "recommended_response": "Focus on ROI and value proposition..."
    }
  ],
  "talk_ratio": {
    "rep_percentage": 45.2,
    "prospect_percentage": 54.8,
    "total_words": 1250
  },
  "sentiment_timeline": [...],
  "key_topics": ["pricing", "implementation", "timeline"],
  "decision_makers_identified": ["John Doe", "Jane Smith"],
  "budget_mentions": ["$50,000", "approved"],
  "timeline_urgency": ["next quarter", "ASAP"],
  "competitor_mentions": ["Salesforce"],
  "next_best_actions": [
    {
      "action": "Send ROI calculation",
      "priority": 1,
      "due_date": "2024-01-15"
    }
  ],
  "confidence_score": 0.85,
  "processing_time_ms": 2340
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing key | Required |
| `MAX_TRANSCRIPT_LENGTH` | Max transcript characters | `50000` |
| `PROCESSING_TIMEOUT_SECONDS` | Analysis timeout | `120` |
| `DEFAULT_LLM_MODEL` | OpenAI model | `gpt-4o-mini` |

### Pricing Tiers

- **Professional** ($79/month): 100 calls, 5 team members
- **Business** ($199/month): 500 calls, unlimited team, API access

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/sales_insights"
export OPENAI_API_KEY="your-key"

# Run API server
uvicorn app.main:app --reload

# Run Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## Architecture

```
├── app/
│   ├── api/
│   │   ├── routes/          # API endpoints
│   │   ├── dependencies.py  # Auth & dependencies
│   │   └── schemas.py       # Pydantic models
│   ├── core/
│   │   ├── config.py        # Settings
│   │   └── llm_client.py    # OpenAI integration
│   ├── services/
│   │   ├── transcript_processor.py
│   │   ├── objection_detector.py
│   │   ├── intent_classifier.py
│   │   ├── deal_scorer.py
│   │   └── insight_generator.py
│   ├── db/
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── postgres.py      # Database connection
│   │   └── redis_cache.py   # Redis client
│   ├── tasks/
│   │   ├── celery_app.py    # Celery configuration
│   │   └── celery_tasks.py  # Background tasks
│   └── main.py              # FastAPI application
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Monitoring & Scaling

### Horizontal Scaling

- Scale API servers behind a load balancer
- Add more Celery workers for increased processing capacity
- Use Redis Cluster for high availability

### Monitoring

- Prometheus metrics at `/metrics`
- Health checks at `/health`
- Flower UI for Celery monitoring at port 5555

### Performance Optimization

- Redis caching for frequent analyses
- Async processing for long transcripts
- Database indexing for fast queries
- Connection pooling for database

## Security

- JWT-based authentication
- Role-based access control (rep/manager/admin)
- Rate limiting per user
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- CORS configuration

## License

MIT License - see LICENSE file for details.
