"""Neo4j client for SYNAPSE relationship graph operations."""
import logging
from datetime import datetime
from typing import Optional
from neo4j import AsyncGraphDatabase
from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    async def verify_connectivity(self):
        await self.driver.verify_connectivity()
        logger.info("Neo4j connected.")

    async def close(self):
        await self.driver.close()

    # ── Relationship operations ───────────────────────────────────────────────

    async def create_relationship(self, user_a_id: str, user_b_id: str, rel_type: str) -> str:
        query = """
        MERGE (a:User {id: $user_a_id})
        MERGE (b:User {id: $user_b_id})
        MERGE (a)-[r:KNOWS {type: $rel_type}]->(b)
        ON CREATE SET r.id = randomUUID(), r.health_score = 75.0,
                      r.trust_index = 0.5, r.created_at = datetime()
        RETURN r.id AS relationship_id
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_a_id=user_a_id, user_b_id=user_b_id, rel_type=rel_type)
            record = await result.single()
            return record["relationship_id"]

    async def get_relationship_context(self, relationship_id: str) -> dict:
        query = """
        MATCH (a:User)-[r:KNOWS {id: $relationship_id}]->(b:User)
        OPTIONAL MATCH (a)-[:HAD_NEGOTIATION]->(n:Negotiation)
        WITH a, r, b, collect(n)[..10] AS negotiations
        RETURN a {.*} AS party_a, b {.*} AS party_b,
               r {.*} AS relationship, negotiations
        """
        async with self.driver.session() as session:
            result = await session.run(query, relationship_id=relationship_id)
            record = await result.single()
            if not record:
                return {}
            return {
                "party_a": dict(record["party_a"]),
                "party_b": dict(record["party_b"]),
                "relationship": dict(record["relationship"]),
                "negotiations": [dict(n) for n in record["negotiations"]],
            }

    async def get_relationship_health_all(self, user_id: str) -> list[dict]:
        query = """
        MATCH (u:User {id: $user_id})-[r:KNOWS]-(other:User)
        RETURN other.id AS party_id, other.name AS name,
               r.health_score AS health_score, r.trust_index AS trust_index,
               r.type AS relationship_type, r.id AS relationship_id
        ORDER BY r.health_score DESC
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            return [dict(record) async for record in result]

    async def get_negotiation_style_profile(self, user_id: str) -> dict:
        query = """
        MATCH (u:User {id: $user_id})-[:HAD_NEGOTIATION]->(n:Negotiation)
        RETURN
            avg(n.rounds_completed) AS avg_rounds,
            avg(n.satisfaction_score) AS avg_satisfaction,
            collect(n.final_stance) AS stance_sequence
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            record = await result.single()
            if not record:
                return {"avg_rounds": 3, "avg_satisfaction": 0.75, "stance_sequence": []}
            return dict(record)

    async def update_relationship_health(self, relationship_id: str, health_score: float):
        query = """
        MATCH ()-[r:KNOWS {id: $relationship_id}]->()
        SET r.health_score = $health_score, r.updated_at = datetime()
        """
        async with self.driver.session() as session:
            await session.run(query, relationship_id=relationship_id, health_score=health_score)

    async def record_negotiation_outcome(
        self,
        relationship_id: str,
        satisfaction_scores: dict,
        fairness_index: float,
    ):
        avg_satisfaction = sum(satisfaction_scores.values()) / max(len(satisfaction_scores), 1)
        query = """
        MATCH ()-[r:KNOWS {id: $relationship_id}]->()
        SET r.last_satisfaction = $avg_satisfaction,
            r.last_fairness = $fairness_index,
            r.last_negotiated_at = datetime()
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                relationship_id=relationship_id,
                avg_satisfaction=avg_satisfaction,
                fairness_index=fairness_index,
            )

    async def compute_health_score(self, relationship_id: str) -> float:
        """
        Health score = trust_index×40 + avg_satisfaction×30 + resolution_rate×20 + recency×10
        """
        query = """
        MATCH ()-[r:KNOWS {id: $relationship_id}]->()
        RETURN r.trust_index AS trust_index,
               r.last_satisfaction AS satisfaction,
               r.resolution_rate AS resolution_rate,
               r.last_negotiated_at AS last_negotiated_at
        """
        async with self.driver.session() as session:
            result = await session.run(query, relationship_id=relationship_id)
            record = await result.single()
            if not record:
                return 70.0

            trust = (record.get("trust_index") or 0.5) * 40
            satisfaction = (record.get("satisfaction") or 0.75) * 30
            resolution = (record.get("resolution_rate") or 0.75) * 20
            recency = 10  # simplified — full impl would decay based on days since last_negotiated_at
            return min(100.0, trust + satisfaction + resolution + recency)


# Singleton
neo4j_client = Neo4jClient()
