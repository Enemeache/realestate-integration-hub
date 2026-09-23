"use client";

import { useCallback, useEffect, useState } from "react";
import { API_URL, fetchLeads, submitLead, type Lead } from "@/lib/api";

const STATUS_OPTIONS = ["", "hot", "warm", "cold"];

export default function DashboardPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [name, setName] = useState("Juana Pérez");
  const [email, setEmail] = useState("juana@example.com");
  const [source, setSource] = useState("web_form");
  const [budget, setBudget] = useState("300000");
  const [message, setMessage] = useState(
    "Busco una casa con pileta para mi familia, tengo que mudarme urgente esta semana"
  );
  const [submitting, setSubmitting] = useState(false);
  const [submitNote, setSubmitNote] = useState<string | null>(null);

  const loadLeads = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await fetchLeads(statusFilter || undefined);
      setLeads(data);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setSubmitNote(null);
    try {
      const result = await submitLead({
        source,
        full_name: name,
        email,
        message,
        budget_usd: budget ? Number(budget) : undefined,
      });
      setSubmitNote(
        `Lead ${result.id} encolado (202 Accepted). El worker lo procesa de forma asíncrona — actualizá en unos segundos.`
      );
      setTimeout(loadLeads, 2500);
    } catch (err) {
      setSubmitNote(
        `Error: ${err instanceof Error ? err.message : "no se pudo enviar el lead"}`
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="wrap">
      <header>
        <h1>PropLeads Dashboard</h1>
        <p className="sub">
          Panel Next.js que consume la API real de{" "}
          <a href="https://github.com/Enemeache/realestate-integration-hub" target="_blank" rel="noopener">
            PropLeads Integration Hub
          </a>{" "}
          — POST /webhook/lead (REST) y POST /graphql para listar leads. Apunta a{" "}
          <code>{API_URL}</code>.
        </p>
      </header>

      <section className="panel">
        <h2>Cargar un lead</h2>
        <form onSubmit={handleSubmit}>
          <div className="grid2">
            <div>
              <label className="f" htmlFor="name">Nombre</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
              <label className="f" htmlFor="email">Email</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              <label className="f" htmlFor="source">Fuente</label>
              <select id="source" value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="web_form">Formulario web</option>
                <option value="zonaprop">ZonaProp</option>
                <option value="whatsapp">WhatsApp</option>
              </select>
            </div>
            <div>
              <label className="f" htmlFor="budget">Presupuesto (USD)</label>
              <input id="budget" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} />
              <label className="f" htmlFor="message">Mensaje</label>
              <textarea id="message" value={message} onChange={(e) => setMessage(e.target.value)} required />
            </div>
          </div>
          <div className="row">
            <button type="submit" disabled={submitting}>
              {submitting ? "Enviando…" : "Enviar lead →"}
            </button>
            <button type="button" className="ghost" onClick={loadLeads} disabled={loading}>
              {loading ? "Actualizando…" : "Actualizar lista"}
            </button>
          </div>
        </form>
        {submitNote && <p className="sub" style={{ marginTop: ".7rem" }}>{submitNote}</p>}
      </section>

      <section className="panel">
        <h2>Leads (GET vía GraphQL)</h2>
        <div className="row" style={{ marginTop: 0, marginBottom: ".8rem" }}>
          <label className="f" style={{ margin: 0 }} htmlFor="statusFilter">Filtrar por status</label>
          <select
            id="statusFilter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ width: "auto" }}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{s || "todos"}</option>
            ))}
          </select>
        </div>

        {loadError && (
          <div className="err">
            No se pudo conectar con la API en <code>{API_URL}</code>: {loadError}.
            <br />
            Corré <code>docker compose up --build</code> en la raíz del repo y volvé a intentar.
          </div>
        )}

        {!loadError && leads.length === 0 && !loading && (
          <div className="empty">Todavía no hay leads guardados.</div>
        )}

        {!loadError && leads.length > 0 && (
          <div className="scroll">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nombre</th>
                  <th>Fuente</th>
                  <th>Status</th>
                  <th>Resumen</th>
                  <th>Matches</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr key={lead.id}>
                    <td style={{ fontFamily: "var(--mono)" }}>{lead.id.slice(0, 8)}</td>
                    <td>{lead.fullName}</td>
                    <td>{lead.source}</td>
                    <td><span className={`statuspill ${lead.status}`}>{lead.status}</span></td>
                    <td>{lead.summary}</td>
                    <td>
                      <ul className="matchlist">
                        {lead.matches.slice(0, 2).map((m) => (
                          <li key={m.propertyId}>{m.title} ({m.score.toFixed(3)})</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <footer>
        Este panel consume el backend real (FastAPI + RabbitMQ/Kafka + MongoDB) — a
        diferencia de la demo del portfolio, que reimplementa la lógica en JS puro
        para poder mostrarse sin infraestructura. Correr con <code>npm install &amp;&amp; npm run dev</code>{" "}
        junto con <code>docker compose up</code> en la raíz del repo.
      </footer>
    </div>
  );
}
