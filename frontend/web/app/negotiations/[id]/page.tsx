"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Negotiation,
  NegotiationRound,
  approveNegotiation,
  delayNegotiation,
  getNegotiation,
  getNegotiationRounds,
  modifyNegotiation,
  overrideNegotiation,
} from "../../../lib/api";

export default function NegotiationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [negotiation, setNegotiation] = useState<Negotiation | null>(null);
  const [rounds, setRounds] = useState<NegotiationRound[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    const [neg, rds] = await Promise.all([getNegotiation(id), getNegotiationRounds(id)]);
    setNegotiation(neg);
    setRounds(rds.rounds || []);
    setLoading(false);
  };

  useEffect(() => {
    load().catch((reason) => {
      setError(reason instanceof Error ? reason.message : "Failed to load negotiation");
      setLoading(false);
    });
  }, [id]);

  if (loading) {
    return (
      <div className="app-shell">
        <div className="glass card">Loading negotiation…</div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <button onClick={() => router.back()} className="btn" style={{ marginBottom: 16 }}>
        ← Back
      </button>

      <section className="glass card" style={{ marginBottom: 16 }}>
        <h1 className="title-xl">Negotiation Details</h1>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 8, flexWrap: "wrap" }}>
          <span className="pill mono">{id}</span>
          <span style={statusBadge(negotiation?.status || "pending")}>{String(negotiation?.status || "pending").toUpperCase()}</span>
          <span className="muted">fairness {Math.round((negotiation?.fairness_index || 0) * 100)}%</span>
        </div>
        {error && <p style={{ color: "var(--danger)", marginTop: 8 }}>{error}</p>}
      </section>

      <section className="glass card" style={{ marginBottom: 16 }}>
        <h2 className="heading">Resolution</h2>
        <pre className="mono" style={{ whiteSpace: "pre-wrap", color: "var(--text-muted)", fontSize: 12 }}>
          {JSON.stringify(negotiation?.resolution || {}, null, 2)}
        </pre>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <button
            className="btn btn-success"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await approveNegotiation(id);
                await load();
              } catch (reason) {
                setError(reason instanceof Error ? reason.message : "Approve failed");
              } finally {
                setBusy(false);
              }
            }}
          >
            Approve
          </button>
          <button
            className="btn"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await modifyNegotiation(id, { review_after_days: 21 });
                await load();
              } catch (reason) {
                setError(reason instanceof Error ? reason.message : "Modify failed");
              } finally {
                setBusy(false);
              }
            }}
          >
            Modify terms
          </button>
          <button
            className="btn btn-danger"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await overrideNegotiation(id, { manual_split: "50/50", note: "User override from demo UI" });
                await load();
              } catch (reason) {
                setError(reason instanceof Error ? reason.message : "Override failed");
              } finally {
                setBusy(false);
              }
            }}
          >
            Override
          </button>
          <button
            className="btn"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await delayNegotiation(id);
                await load();
              } catch (reason) {
                setError(reason instanceof Error ? reason.message : "Delay failed");
              } finally {
                setBusy(false);
              }
            }}
          >
            Delay 2h
          </button>
        </div>
      </section>

      <section>
        <h2 className="heading">Round Timeline ({rounds.length})</h2>
        {rounds.map((round) => (
          <div key={round.round_number} className="glass card" style={{ marginBottom: 12 }}>
            <p style={{ fontWeight: 600, marginBottom: 12, color: "var(--secondary)" }}>Round {round.round_number}</p>
            <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))" }}>
              {(round.agent_turns || []).map((turn) => (
                <div key={turn.agent_id} className="glass card" style={{ background: "rgba(10,16,33,0.45)", padding: 12 }}>
                  <p style={{ fontWeight: 700 }}>{turn.agent_id}</p>
                  <p className="muted" style={{ marginTop: 6 }}>stance: {turn.stance}</p>
                  <p className="muted">satisfaction: {Math.round(turn.satisfaction_score * 100)}%</p>
                  <p className="muted">concession: {turn.concession_pct}%</p>
                  <p className="muted" style={{ marginTop: 6 }}>{turn.rationale}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

function statusBadge(status: string): React.CSSProperties {
  const colors: Record<string, string> = {
    completed: "var(--success)",
    timed_out: "var(--danger)",
    in_progress: "var(--warning)",
    pending: "var(--text-dim)",
    overridden: "var(--primary)",
  };

  return {
    fontSize: 11,
    fontWeight: 700,
    padding: "4px 8px",
    borderRadius: 8,
    background: `${colors[status] || "var(--text-dim)"}22`,
    color: colors[status] || "var(--text-dim)",
    border: `1px solid ${colors[status] || "var(--text-dim)"}66`,
  };
}
