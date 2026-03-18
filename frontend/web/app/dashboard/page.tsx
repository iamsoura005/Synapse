"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Contract,
  HealthResponse,
  Negotiation,
  Relationship,
  approveNegotiation,
  connectIntegration,
  createContract,
  createRelationship,
  delayNegotiation,
  disconnectIntegration,
  getContracts,
  getHealth,
  getIntegrationStatus,
  getNegotiations,
  getRelationshipInsights,
  getRelationships,
  startManualNegotiation,
  useNegotiationFeed,
} from "../../lib/api";

type FeedEvent = {
  id: string;
  type: string;
  message: string;
  timestamp: string;
};

const DEMO_USER = "demo-user";

function scoreColor(score: number) {
  if (score >= 80) return "var(--success)";
  if (score >= 60) return "var(--warning)";
  return "var(--danger)";
}

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [integrations, setIntegrations] = useState<Record<string, boolean>>({});
  const [feed, setFeed] = useState<FeedEvent[]>([]);
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string>("");
  const [selectedNegotiationId, setSelectedNegotiationId] = useState<string>("");
  const [insights, setInsights] = useState<string[]>([]);
  const [newCounterparty, setNewCounterparty] = useState("taylor-lee");
  const [newRelationshipType, setNewRelationshipType] = useState("friend");
  const [manualContext, setManualContext] = useState("Need to rebalance recurring shared expenses and reduce friction.");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>("");

  const avgHealth = useMemo(() => {
    if (!relationships.length) return 0;
    return Math.round(relationships.reduce((sum, item) => sum + Number(item.health_score || 0), 0) / relationships.length);
  }, [relationships]);

  const refreshAll = async () => {
    const [healthRes, relRes, negRes, contractRes, integrationRes] = await Promise.all([
      getHealth(),
      getRelationships(DEMO_USER),
      getNegotiations(DEMO_USER),
      getContracts(DEMO_USER),
      getIntegrationStatus(DEMO_USER),
    ]);

    setHealth(healthRes);
    setRelationships(relRes.relationships);
    setNegotiations(negRes.negotiations);
    setContracts(contractRes.contracts);
    setIntegrations(integrationRes.integrations);

    if (!selectedRelationshipId && relRes.relationships.length) {
      setSelectedRelationshipId(relRes.relationships[0].id);
    }
    if (!selectedNegotiationId && negRes.negotiations.length) {
      setSelectedNegotiationId(negRes.negotiations[0].id);
    }
  };

  useEffect(() => {
    refreshAll().catch((reason) => setError(reason instanceof Error ? reason.message : "Failed to load dashboard"));
  }, []);

  useEffect(() => {
    if (!selectedRelationshipId) return;
    getRelationshipInsights(selectedRelationshipId)
      .then((response) => {
        setInsights(response.insights.map((insight) => insight.actionable_suggestion));
      })
      .catch(() => setInsights([]));
  }, [selectedRelationshipId]);

  useEffect(() => {
    const cleanup = useNegotiationFeed(DEMO_USER, (event) => {
      const item: FeedEvent = {
        id: String(Date.now()),
        type: String(event.type || "event"),
        message: String(event.message || "Live feed update"),
        timestamp: new Date().toLocaleTimeString(),
      };
      setFeed((prev) => [item, ...prev].slice(0, 10));
    });
    return cleanup;
  }, []);

  const handleCreateRelationship = async () => {
    try {
      setBusy(true);
      setError("");
      await createRelationship({
        user_id: DEMO_USER,
        counterparty_id: newCounterparty,
        relationship_type: newRelationshipType,
      });
      await refreshAll();
      setFeed((prev) => [
        { id: String(Date.now()), type: "relationship", message: `Added relationship with ${newCounterparty}`, timestamp: new Date().toLocaleTimeString() },
        ...prev,
      ]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed creating relationship");
    } finally {
      setBusy(false);
    }
  };

  const handleStartNegotiation = async () => {
    try {
      setBusy(true);
      setError("");
      const selected = relationships.find((item) => item.id === selectedRelationshipId);
      const counterpartyId = selected?.counterparty_id || "counterparty";
      const response = await startManualNegotiation({
        negotiation_type: "expense",
        party_ids: [DEMO_USER, counterpartyId],
        context: manualContext,
        urgency: "medium",
        relationship_id: selectedRelationshipId || undefined,
      });
      await refreshAll();
      setSelectedNegotiationId(response.negotiation_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed starting negotiation");
    } finally {
      setBusy(false);
    }
  };

  const handleCreateContract = async () => {
    if (!selectedNegotiationId) return;
    try {
      setBusy(true);
      setError("");
      const negotiation = negotiations.find((item) => item.id === selectedNegotiationId);
      await createContract({
        negotiation_id: selectedNegotiationId,
        party_ids: negotiation?.party_ids || [DEMO_USER, "counterparty"],
        clauses: [
          {
            clause_id: "sync-1",
            title: "Bi-weekly Retrospective",
            type: "milestone",
            description: "Review outcomes every two weeks and adjust if needed.",
            trigger_status: "watching",
          },
          {
            clause_id: "budget-guard",
            title: "Budget Drift Control",
            type: "adaptive",
            description: "If spend variance exceeds 15%, trigger renegotiation.",
            trigger_status: "watching",
            trigger_condition: { metric: "spend_variance", threshold: 0.15 },
          },
        ],
      });
      await refreshAll();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed creating contract");
    } finally {
      setBusy(false);
    }
  };

  const toggleIntegration = async (name: string, isEnabled: boolean) => {
    try {
      setBusy(true);
      setError("");
      if (isEnabled) {
        await disconnectIntegration(name, DEMO_USER);
      } else {
        await connectIntegration(name, DEMO_USER);
      }
      await refreshAll();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Failed updating integration");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="app-shell">
      <section className="glass card" style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 14 }}>
        <div>
          <h1 className="title-xl">SYNAPSE Demo Command Center</h1>
          <p className="muted" style={{ marginTop: 8 }}>Glassmorphic frontend connected to live backend APIs and mutable demo state.</p>
        </div>
        <div className="pill mono">mode: {health?.mode || "live"}</div>
      </section>

      {error && (
        <section className="glass card" style={{ borderColor: "rgba(239,68,68,0.6)", marginBottom: 16 }}>
          <strong>Request error:</strong> {error}
        </section>
      )}

      <section className="grid-3" style={{ marginBottom: 16 }}>
        <article className="glass card">
          <p className="heading">Relationship Health</p>
          <p style={{ fontSize: 34, fontWeight: 700, color: scoreColor(avgHealth) }}>{avgHealth}</p>
          <p className="muted">Average across {relationships.length} relationships</p>
        </article>
        <article className="glass card">
          <p className="heading">Active Negotiations</p>
          <p style={{ fontSize: 34, fontWeight: 700 }}>{negotiations.filter((item) => item.status !== "completed").length}</p>
          <p className="muted">Total negotiations tracked: {negotiations.length}</p>
        </article>
        <article className="glass card">
          <p className="heading">Live Contracts</p>
          <p style={{ fontSize: 34, fontWeight: 700 }}>{contracts.length}</p>
          <p className="muted">Stored and verifiable from contract endpoints</p>
        </article>
      </section>

      <section className="grid-3" style={{ alignItems: "start", marginBottom: 16 }}>
        <article className="glass card">
          <p className="heading">Relationships</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 12 }}>
            {relationships.map((item) => (
              <button
                key={item.id}
                className="btn"
                style={{ textAlign: "left", borderColor: selectedRelationshipId === item.id ? "rgba(124,92,255,0.7)" : undefined }}
                onClick={() => setSelectedRelationshipId(item.id)}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{item.counterparty_name || item.counterparty_id}</span>
                  <span className="mono" style={{ color: scoreColor(item.health_score) }}>{Math.round(item.health_score)}</span>
                </div>
                <div className="muted" style={{ fontSize: 12 }}>{item.relationship_type}</div>
              </button>
            ))}
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            <input className="input" value={newCounterparty} onChange={(event) => setNewCounterparty(event.target.value)} placeholder="counterparty-id" />
            <select className="select" value={newRelationshipType} onChange={(event) => setNewRelationshipType(event.target.value)}>
              <option value="friend">friend</option>
              <option value="colleague">colleague</option>
              <option value="roommate">roommate</option>
              <option value="client">client</option>
              <option value="family">family</option>
            </select>
            <button className="btn btn-primary" disabled={busy} onClick={handleCreateRelationship}>Create relationship</button>
          </div>
        </article>

        <article className="glass card">
          <p className="heading">Negotiations</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 12 }}>
            {negotiations.map((item) => (
              <div key={item.id} className="glass card" style={{ background: "rgba(10,16,33,0.5)", padding: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong>{item.negotiation_type}</strong>
                  <span className="pill mono">{item.status}</span>
                </div>
                <p className="muted" style={{ marginTop: 6, marginBottom: 8 }}>fairness {Math.round((item.fairness_index || 0) * 100)}%</p>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <Link className="btn" href={`/negotiations/${item.id}`}>Open</Link>
                  <button className="btn btn-success" disabled={busy} onClick={async () => { await approveNegotiation(item.id); await refreshAll(); }}>Approve</button>
                  <button className="btn" disabled={busy} onClick={async () => { await delayNegotiation(item.id); await refreshAll(); }}>Delay</button>
                </div>
              </div>
            ))}
          </div>
          <textarea className="textarea" value={manualContext} onChange={(event) => setManualContext(event.target.value)} />
          <button className="btn btn-primary" style={{ marginTop: 8 }} disabled={busy} onClick={handleStartNegotiation}>Start manual negotiation</button>
        </article>

        <article className="glass card">
          <p className="heading">Contracts</p>
          <select className="select" style={{ marginBottom: 8 }} value={selectedNegotiationId} onChange={(event) => setSelectedNegotiationId(event.target.value)}>
            <option value="">select negotiation</option>
            {negotiations.map((item) => (
              <option key={item.id} value={item.id}>{item.negotiation_type} · {item.id.slice(0, 8)}</option>
            ))}
          </select>
          <button className="btn btn-primary" disabled={!selectedNegotiationId || busy} onClick={handleCreateContract}>Create contract from negotiation</button>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
            {contracts.map((item) => (
              <Link key={item.id} href={`/contracts/${item.id}`} className="glass card" style={{ background: "rgba(10,16,33,0.5)", padding: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>v{item.version}</strong>
                  <span className="pill mono">{item.status}</span>
                </div>
                <p className="muted" style={{ marginTop: 6 }}>{item.id.slice(0, 10)}…</p>
              </Link>
            ))}
          </div>
        </article>
      </section>

      <section className="grid-2" style={{ alignItems: "start" }}>
        <article className="glass card">
          <p className="heading">Integrations</p>
          <div style={{ display: "grid", gap: 10 }}>
            {Object.entries(integrations).map(([name, enabled]) => (
              <div key={name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>{name}</span>
                <button className={`btn ${enabled ? "btn-danger" : "btn-success"}`} disabled={busy} onClick={() => toggleIntegration(name, enabled)}>
                  {enabled ? "Disconnect" : "Connect"}
                </button>
              </div>
            ))}
          </div>
          <p className="muted" style={{ marginTop: 10, fontSize: 13 }}>Connected status comes from backend /integrations/status endpoint.</p>
        </article>

        <article className="glass card">
          <p className="heading">Insights & Live Feed</p>
          <div style={{ marginBottom: 12 }}>
            {insights.length ? insights.map((item, index) => (
              <p key={index} style={{ margin: "0 0 8px", color: "var(--text-muted)" }}>• {item}</p>
            )) : <p className="muted">Select a relationship to load insights.</p>}
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            {feed.map((item) => (
              <div key={item.id} className="glass card" style={{ background: "rgba(10,16,33,0.5)", padding: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>{item.type}</strong>
                  <span className="mono muted" style={{ fontSize: 12 }}>{item.timestamp}</span>
                </div>
                <p className="muted" style={{ marginTop: 4 }}>{item.message}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
