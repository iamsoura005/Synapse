"use client";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Contract, getContract } from "../../../lib/api";

const CLAUSE_COLORS: Record<string, string> = {
  static: "#94a3b8",
  adaptive: "var(--secondary)",
  expiry: "var(--warning)",
  escalation: "var(--danger)",
  milestone: "var(--primary)",
};

function ClauseCard({ clause }: { clause: Record<string, unknown> }) {
  const type = (clause.type as string) || "static";
  const color = CLAUSE_COLORS[type] || CLAUSE_COLORS.static;
  const triggerCondition = clause.trigger_condition as Record<string, unknown> | undefined;

  return (
    <div className="glass card" style={{ borderLeft: `3px solid ${color}`, marginBottom: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <span style={{ fontWeight: 600 }}>{String(clause.title || "Clause")}</span>
        <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 10, border: `1px solid ${color}`, color, background: `${color}22` }}>
          {type}
        </span>
        {type !== "static" && (
          <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-dim)" }}>
            {String(clause.trigger_status || "watching")}
          </span>
        )}
      </div>
      <p style={{ fontSize: 13, color: "var(--text-muted)" }}>{String(clause.description || "")}</p>
      {triggerCondition && (
        <pre style={{ marginTop: 8, fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-dim)", background: "rgba(10,16,33,0.5)", padding: 8, borderRadius: 6, overflow: "auto" }}>
          {JSON.stringify(triggerCondition, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function ContractDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [contract, setContract] = useState<Contract | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getContract(id).then(setContract).catch((reason) => {
      setError(reason instanceof Error ? reason.message : "Failed to load contract");
    });
  }, [id]);

  if (!contract) return <div className="app-shell"><div className="glass card">{error || "Loading…"}</div></div>;

  const clauses = contract.clauses || [];

  return (
    <div className="app-shell">
      <div className="glass card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
          <h1 className="title-xl">Living Contract</h1>
          <span className="pill mono">v{String(contract.version || 1)}</span>
        </div>
        <p className="muted" style={{ marginTop: 8 }}>Contract ID: <span className="mono">{contract.id}</span></p>
      </div>

      <div className="glass card" style={{ marginBottom: 16 }}>
        <p style={{ fontWeight: 600, marginBottom: 10 }}>Parties</p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {(contract.party_ids || []).map((partyId) => (
            <span key={partyId} className="pill mono">{partyId}</span>
          ))}
        </div>
      </div>

      <h2 className="heading">Clauses ({clauses.length})</h2>
      {clauses.map((clause, index) => <ClauseCard key={index} clause={clause} />)}

      <div className="glass card" style={{ marginTop: 16 }}>
        <p style={{ fontWeight: 600, marginBottom: 8 }}>Blockchain Verification</p>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-muted)", display: "grid", gap: 6 }}>
          <div>hash: {contract.polygon_hash || "n/a"}</div>
          <div>tx: {contract.polygon_tx_hash || "n/a"}</div>
        </div>
        {contract.polygon_scan_url && (
          <a href={contract.polygon_scan_url} target="_blank" rel="noreferrer" style={{ color: "var(--secondary)", marginTop: 8, display: "inline-block" }}>
            Open PolygonScan ↗
          </a>
        )}
      </div>

      <div style={{ marginTop: 16 }}>
        <Link href="/dashboard" className="btn">Back to dashboard</Link>
      </div>
    </div>
  );
}
