# SYNAPSE: Ambient Relationship Intelligence OS

SYNAPSE is a backend + frontend system that monitors your digital integrations for interpersonal friction, proactively negotiates via AI agents, and creates living contracts that auto-adapt to reality.

## Quick Start

### 1. Environment Setup
Copy the `.env.example` file to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 2. Start Infrastructure
Run the core services (Database, Redis, Kafka, Neo4j):
```bash
docker compose up -d postgres redis zookeeper kafka neo4j
```

### 3. Backend Development
The backend is built with FastAPI, LangGraph, and PostgreSQL. Keep the infrastructure running above, and either run the backend via docker or locally:
```bash
docker compose up backend celery-worker celery-beat
```

### 4. Frontend Workspace
The frontend is a monorepo consisting of a Next.js web dashboard and an Expo React Native mobile app.

**Web Dashboard:**
```bash
cd frontend
npm install
npm run dev:web
```

**Mobile App:**
```bash
cd frontend
npm install
npm run dev:mobile
```

## Architecture Layers
- **Sensors:** Integrations to existing services (Gmail, Slack, Calendar, Splitwise).
- **Stream:** Kafka handles real-time events.
- **Agents:** Gemini 2.0 agents built on LangGraph for Context, Tension, and Negotiation.
- **Data:** PostgeSQL (relational models) and Neo4j (relationship graphs).
