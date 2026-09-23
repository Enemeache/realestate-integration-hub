export type PropertyMatch = {
  propertyId: string;
  title: string;
  score: number;
};

export type Lead = {
  id: string;
  source: string;
  fullName: string;
  email: string;
  status: string;
  summary: string | null;
  matches: PropertyMatch[];
};

export type NewLead = {
  source: string;
  full_name: string;
  email: string;
  message: string;
  budget_usd?: number;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const LEADS_QUERY = `
  query Leads($status: String) {
    leads(status: $status) {
      id
      source
      fullName
      email
      status
      summary
      matches { propertyId title score }
    }
  }
`;

export async function fetchLeads(status?: string): Promise<Lead[]> {
  const res = await fetch(`${API_URL}/graphql`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: LEADS_QUERY, variables: { status: status ?? null } }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`GraphQL respondió ${res.status} — ¿está corriendo la API?`);
  }
  const json = await res.json();
  if (json.errors?.length) {
    throw new Error(json.errors[0].message);
  }
  return json.data.leads as Lead[];
}

export async function submitLead(lead: NewLead): Promise<{ id: string; queued: boolean }> {
  const res = await fetch(`${API_URL}/webhook/lead`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(lead),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `El webhook respondió ${res.status}`);
  }
  return res.json();
}

export { API_URL };
