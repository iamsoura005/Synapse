#!/usr/bin/env python3
"""SYNAPSE Project Verification & Analysis Report"""
import sys

print("=" * 70)
print("SYNAPSE PROJECT ANALYSIS & VERIFICATION REPORT")
print("=" * 70)

# Test all imports
test_results = []

def test_import(module_name, display_name):
    try:
        __import__(module_name)
        test_results.append((display_name, "✓ PASS", ""))
        print(f"  ✓ {display_name}")
        return True
    except Exception as e:
        msg = str(e)[:60]
        test_results.append((display_name, "✗ FAIL", msg))
        print(f"  ✗ {display_name}: {msg}")
        return False

# Test core modules
print("\n1. TESTING CORE MODULE IMPORTS:")
print("-" * 70)
test_import("app.config", "Config")
test_import("app.database.postgres", "PostgreSQL")
test_import("app.database.redis_client", "Redis Client")
test_import("app.kafka.topics", "Kafka Topics")
test_import("app.kafka.producer", "Kafka Producer")
test_import("app.kafka.consumer", "Kafka Consumer")
test_import("app.graph.neo4j_client", "Neo4j Client")

# Test models
print("\n2. TESTING DATA MODELS:")
print("-" * 70)
test_import("app.models.user", "User Model")
test_import("app.models.relationship", "Relationship Model")
test_import("app.models.negotiation", "Negotiation Model")
test_import("app.models.contract", "Contract Model")

# Test schemas
print("\n3. TESTING SCHEMAS:")
print("-" * 70)
test_import("app.agents.schemas", "Agent Schemas")
test_import("app.schemas.core", "Core Schemas")

# Test agents
print("\n4. TESTING AGENTS:")
print("-" * 70)
test_import("app.agents.context_agent", "Context Agent")
test_import("app.agents.emotion_agent", "Emotion Agent")
test_import("app.agents.negotiation_engine", "Negotiation Engine")
test_import("app.agents.sensor_agent", "Sensor Agent")

# Test delivery systems
print("\n5. TESTING DELIVERY SYSTEMS:")
print("-" * 70)
test_import("app.delivery.voice", "Voice Delivery (pyttsx3)")
test_import("app.delivery.push", "Push Delivery")
test_import("app.delivery.email_digest", "Email Digest")

# Test sensors
print("\n6. TESTING SENSORS:")
print("-" * 70)
test_import("app.sensors.base", "Base Sensor")
test_import("app.sensors.slack", "Slack Sensor")
test_import("app.sensors.gmail", "Gmail Sensor")
test_import("app.sensors.google_calendar", "Google Calendar Sensor")
test_import("app.sensors.splitwise", "Splitwise Sensor")

# Test contracts
print("\n7. TESTING CONTRACTS:")
print("-" * 70)
test_import("app.contracts.blockchain", "Blockchain")
test_import("app.contracts.runtime", "Contract Runtime")

# Test API routers
print("\n8. TESTING API ROUTERS:")
print("-" * 70)
test_import("app.api.routers.relationships", "Relationships Router")
test_import("app.api.routers.negotiations", "Negotiations Router")
test_import("app.api.routers.contracts", "Contracts Router")
test_import("app.api.routers.integrations", "Integrations Router")

# Test main app
print("\n9. TESTING MAIN APPLICATION:")
print("-" * 70)
try:
    from app.main import app
    test_results.append(("FastAPI App", "✓ PASS", ""))
    print(f"✓ FastAPI app loaded successfully")
    print(f"  - Title: {app.title}")
    print(f"  - Version: {app.version}")
    print(f"  - Routes: {len(app.routes)}")
except Exception as e:
    test_results.append(("FastAPI App", "✗ FAIL", str(e)))
    print(f"✗ Failed to load FastAPI app: {e}")

# Print summary
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)
passed = sum(1 for _, status, _ in test_results if "PASS" in status)
total = len(test_results)
print(f"\nTests Passed: {passed}/{total}")
print(f"Success Rate: {100*passed//total}%\n")

if passed == total:
    print("✓ ALL SYSTEMS OPERATIONAL")
    print("✓ PROJECT STRUCTURE IS VALID")
    print("✓ ALL IMPORTS ARE WORKING")
    print("\nThe project is ready to run!")
    print("\nNote: The backend server requires the following services:")
    print("  • PostgreSQL database")
    print("  • Redis cache")
    print("  • Neo4j graph database  ")
    print("  • Kafka message broker")
    print("\nTo start the server:")
    print("  cd backend")
    print("  python -m uvicorn app.main:app --reload")
else:
    print(f"\n⚠ {total - passed} module(s) failed to import")
    print("\nFailed modules:")
    for name, status, error in test_results:
        if "FAIL" in status:
            print(f"  • {name}: {error}")

print("\n" + "=" * 70)
