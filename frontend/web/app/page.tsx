import Link from "next/link";

export default function HomePage() {
  return (
    <main className="app-shell" style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
      <section className="glass card" style={{ maxWidth: 780, width: "100%", textAlign: "center", padding: 30 }}>
        <p className="pill mono" style={{ marginBottom: 12 }}>SYNAPSE • Demo Ready</p>
        <h1 className="title-xl" style={{ marginBottom: 12 }}>Ambient Relationship Intelligence</h1>
        <p className="muted" style={{ marginBottom: 20 }}>
          Full glassmorphic demo connected to live backend APIs for relationships, negotiations, contracts, and integrations.
        </p>
        <div style={{ display: "flex", justifyContent: "center", gap: 10, flexWrap: "wrap" }}>
          <Link href="/dashboard" className="btn btn-primary">Open Dashboard</Link>
          <a href="http://localhost:8010/docs" target="_blank" rel="noreferrer" className="btn">Backend API Docs</a>
        </div>
      </section>
    </main>
  );
}
