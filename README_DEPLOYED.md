# Synapse - AI-Powered Fair Negotiation Platform

> A full-stack platform for intelligent, fair negotiations powered by LLM agents and game-theoretic algorithms.

## 🎯 Overview

Synapse uses AI agents and Shapley value theory to facilitate fair negotiations between parties. It maintains relationship health scores, tracks negotiation history, and executes smart contracts on blockchain.

**Live Demo:** Backend on port 8010, Frontend on port 3000

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  Glasmorphic UI │ Real-time Updates │ Responsive Design        │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTPS REST API
┌────────────────▼────────────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ Relationships │ │ Negotiations │ │ Contracts    │             │
│ │ Intelligence │ │ Engine       │ │ Management   │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
│         ↓               ↓                  ↓                    │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ Neo4j Graph  │ │ Shapley      │ │ Polygon      │             │
│ │ Database     │ │ Algorithms   │ │ Blockchain   │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL 15+ (optional, demo mode works without it)
- Redis (optional)
- Neo4j (optional)

### Development Setup

```bash
# Clone repository
git clone https://github.com/iamsoura005/Synapse.git
cd Synapse

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend/web
npm install

# Start backend (port 8010)
cd ../../backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

# Start frontend (port 3000, in another terminal)
cd ../frontend/web
npm run dev -- --port 3000
```

Access at: http://localhost:3000

## 📦 Deployment

### Vercel Deployment (Frontend)

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Import project in Vercel**
   - Go to https://vercel.com/new
   - Select GitHub repository: `iamsoura005/Synapse`
   - Set project root: `frontend/web`

3. **Configure Environment Variables in Vercel**
   ```
   NEXT_PUBLIC_API_URL=<your-backend-api-url>
   ```

4. **Deploy**
   - Vercel will auto-deploy on push to main

### Backend Deployment (Railway/Render/Fly)

**Example with Railway:**

1. Push code to GitHub (already done)

2. Connect to Railway
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub"
   - Select `iamsoura005/Synapse`
   - Set root directory: `backend`

3. **Add Environment Variables**
   ```
   DEMO_MODE=false
   DATABASE_URL=postgresql://...  # Your PostgreSQL URL
   REDIS_URL=redis://...          # Your Redis URL
   NEO4J_URI=bolt://...           # Your Neo4j URL
   JWT_SECRET_KEY=<secure-random-key>
   FRONTEND_ORIGINS=https://<your-vercel-domain>.vercel.app
   # Add other API keys as needed
   ```

4. **Add PostgreSQL Service (Railway)**
   - Click "Add Service" → "PostgreSQL"
   - Railway will auto-populate `DATABASE_URL`

5. **Configure Domain**
   - Set custom domain in Railway
   - Update Vercel env var `NEXT_PUBLIC_API_URL` with backend URL

6. **Deploy**
   - Railway auto-deploys on push

## 🔌 API Endpoints

### Demo Mode (No DB Required)
All endpoints work without external services when `DEMO_MODE=true`

### Relationships
- `GET /api/v1/relationships?user_id={id}` - List relationships
- `GET /api/v1/relationships/{id}` - Get single relationship
- `GET /api/v1/relationships/{id}/graph` - Graph data
- `GET /api/v1/relationships/{id}/insights` - AI insights
- `POST /api/v1/relationships` - Create relationship
- `DELETE /api/v1/relationships/{id}` - Delete relationship

### Negotiations
- `GET /api/v1/negotiations?user_id={id}` - List negotiations
- `GET /api/v1/negotiations/{id}` - Get negotiation
- `GET /api/v1/negotiations/{id}/rounds` - Negotiation rounds
- `POST /api/v1/negotiations/{id}/approve` - Approve terms
- `POST /api/v1/negotiations/{id}/modify` - Modify terms
- `POST /api/v1/negotiations/{id}/override` - Override with fair split
- `POST /api/v1/negotiations/{id}/delay` - Delay negotiation
- `POST /api/v1/negotiations/manual` - Start new negotiation

### Contracts
- `GET /api/v1/contracts?user_id={id}` - List contracts
- `GET /api/v1/contracts/{id}` - Get contract
- `POST /api/v1/contracts` - Create contract

### Integrations
- `GET /api/v1/integrations/status?user_id={id}` - Get integ status
- `POST /api/v1/integrations/connect/{name}` - Connect integration
- `DELETE /api/v1/integrations/{name}` - Disconnect integration

### Health
- `GET /health` - Backend health check

## 🔐 Environment Variables

### Backend (.env or Railway/Render env vars)
```env
# Mode
DEMO_MODE=true                    # Set to false for production

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/synapse
REDIS_URL=redis://host:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Message Queue
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# AI Models
GEMINI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

# Auth
JWT_SECRET_KEY=<secure-random-32-char-key>
SUPABASE_URL=
SUPABASE_ANON_KEY=

# OAuth Integrations
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
SPLITWISE_API_KEY=

# Blockchain
POLYGON_RPC_URL=https://polygon-rpc.com
POLYGON_PRIVATE_KEY=

# CORS
FRONTEND_ORIGINS=http://localhost:3000,https://yourdomain.vercel.app
```

### Frontend (.env.local or Vercel env vars)
```env
NEXT_PUBLIC_API_URL=http://localhost:8010      # Dev
NEXT_PUBLIC_API_URL=https://api.yourdomain.com # Prod
```

## 📊 Dashboard Features

- **Relationships Management** - View health scores, trust indices, negotiation history
- **Active Negotiations** - Monitor ongoing negotiations with live status updates
- **Contract Management** - View and manage living contracts with blockchain proofs
- **Integration Status** - Connect/disconnect external services (Google Calendar, Gmail, Slack, Splitwise)
- **Manual Negotiations** - Start new negotiations with multiple parties
- **Fairness Analytics** - View Shapley-based fairness scores
- **WebSocket Feed** - Real-time updates on negotiation progress

## 🧠 ML Features

### Shapley Value Computation
- Fair allocation using exact algorithm (N ≤ 6) or Monte Carlo (N > 6)
- GameTheoretic fairness guarantees
- Integrated with negotiation recommendations

### LLM Agents
- Negotiation engine with multiple strategies (collaborative, competitive, accommodating)
- Relationship intelligence analysis
- Emotion-aware negotiation adjustments
- Context preservation across rounds

## 📱 Tech Stack

- **Frontend**: Next.js 14.2 + React 18 + TypeScript + Glassmorphic CSS
- **Backend**: FastAPI + Python 3.13 + async/await
- **Databases**: PostgreSQL (relationships) + Redis (cache) + Neo4j (graph)
- **Message Queue**: Kafka (event streaming)
- **ML**: Google Generative AI + Shapley algorithms
- **Blockchain**: Polygon (contract notarization)
- **Deployment**: Vercel (frontend) + Railway/Render/Fly (backend)

## 🔄 CI/CD

GitHub Actions automatically:
- Lint Python code
- Type-check TypeScript
- Run test suites
- Deploy to Vercel (frontend)
- Deploy to Railway (backend)

## 📝 API Documentation

- **Interactive Docs**: http://localhost:8010/docs (Swagger UI)
- **ReDoc**: http://localhost:8010/redoc
- **OpenAPI Schema**: http://localhost:8010/openapi.json

## 🐛 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests (Next.js)
cd frontend/web
npm test

# Type checking
cd frontend/web
npm run type-check
```

## 🔍 Monitoring (Demo Mode)

When `DEMO_MODE=true`:
- ✅ All endpoints return mocked data
- ✅ No external service dependencies
- ✅ Perfect for development and testing
- ✅ Frontend fully functional with real API calls

When `DEMO_MODE=false` (Production):
- ✓ PostgreSQL required for relationships
- ✓ Redis required for caching
- ✓ Neo4j required for graph queries
- ✓ Kafka required for event streaming
- ✓ API keys required for AI/integrations

## 📄 License

MIT License - see LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📧 Support

For issues, questions, or contributions: [GitHub Issues](https://github.com/iamsoura005/Synapse/issues)

---

**Built with ❤️ for fair negotiations**
