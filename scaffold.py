import os
import sys

base_dir = r"c:\Users\soura\OneDrive\Desktop\Synapse"

directories = [
    "backend/app/models",
    "backend/app/sensors",
    "backend/app/agents",
    "backend/app/graph",
    "backend/app/contracts",
    "backend/app/kafka",
    "backend/app/delivery",
    "backend/app/api/routers",
    "backend/app/database",
    "backend/tests",
    "backend/alembic",
    "frontend/web",
    "frontend/mobile",
    "contracts"
]

files = [
    "backend/app/main.py",
    "backend/app/config.py",
    "backend/app/models/canonical_event.py",
    "backend/app/models/negotiation.py",
    "backend/app/models/contract.py",
    "backend/app/models/relationship.py",
    "backend/app/sensors/base.py",
    "backend/app/sensors/google_calendar.py",
    "backend/app/sensors/gmail.py",
    "backend/app/sensors/slack.py",
    "backend/app/sensors/splitwise.py",
    "backend/app/agents/sensor_agent.py",
    "backend/app/agents/context_agent.py",
    "backend/app/agents/negotiation_engine.py",
    "backend/app/agents/emotion_agent.py",
    "backend/app/agents/schemas.py",
    "backend/app/graph/neo4j_client.py",
    "backend/app/graph/shapley.py",
    "backend/app/contracts/runtime.py",
    "backend/app/contracts/blockchain.py",
    "backend/app/kafka/producer.py",
    "backend/app/kafka/consumer.py",
    "backend/app/kafka/topics.py",
    "backend/app/delivery/push.py",
    "backend/app/delivery/voice.py",
    "backend/app/delivery/email_digest.py",
    "backend/app/api/routers/auth.py",
    "backend/app/api/routers/relationships.py",
    "backend/app/api/routers/negotiations.py",
    "backend/app/api/routers/contracts.py",
    "backend/app/api/routers/integrations.py",
    "backend/app/api/middleware.py",
    "backend/app/database/postgres.py",
    "backend/app/database/redis_client.py",
    "backend/Dockerfile",
    "backend/requirements.txt",
    "backend/pyproject.toml",
    "frontend/package.json",
    "contracts/AgreementRegistry.sol",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "README.md",
    ".env.example"
]

def scaffold():
    try:
        for d in directories:
            os.makedirs(os.path.join(base_dir, d), exist_ok=True)
            print(f"Created directory: {d}")
        
        for f in files:
            file_path = os.path.join(base_dir, f)
            if not os.path.exists(file_path):
                open(file_path, 'w').close()
                print(f"Created file: {f}")
    except Exception as e:
        print(f"Error scaffolding: {e}")

if __name__ == "__main__":
    scaffold()
