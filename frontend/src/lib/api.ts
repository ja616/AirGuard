const API_BASE = "http://localhost:8000/api/v1";

export interface MetricsResponse {
  total_investigations: number;
  failed_investigations: number;
  completed_investigations: number;
  average_duration_seconds: number;
  state_counts: Record<string, number>;
}

export interface HealthResponse {
  status: string;
  backend: string;
  database: string;
  airflow: string;
  aws: string;
  slack: string;
}

export interface InvestigationMetadata {
  started_by: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  airflow_environment: string;
  aws_account: string;
  engine_version: string;
  investigation_version: string;
}

export interface Investigation {
  id: string;
  state: string;
  progress: number;
  metadata: InvestigationMetadata;
  artifacts?: any[];
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const res = await fetch(`${API_BASE}/metrics/`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health/`);
  if (!res.ok) throw new Error("Failed to fetch health");
  return res.json();
}

export async function fetchInvestigations(): Promise<Investigation[]> {
  const res = await fetch(`${API_BASE}/investigations/`);
  if (!res.ok) throw new Error("Failed to fetch investigations");
  return res.json();
}

export async function fetchInvestigation(id: string): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/investigations/${id}`);
  if (!res.ok) throw new Error("Failed to fetch investigation");
  return res.json();
}

export async function fetchTimeline(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/${id}/timeline`);
  if (!res.ok) return null;
  return res.json();
}

export async function fetchGraph(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/${id}/graph`);
  if (!res.ok) return null;
  return res.json();
}

export async function fetchReport(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/${id}/report`);
  if (!res.ok) return null;
  return res.json();
}

export async function fetchEvidence(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/investigations/${id}/evidence`);
  if (!res.ok) return null;
  return res.json();
}

export async function triggerInvestigation(payload: {
  dag_id: string;
  failed_node_id?: string;
  severity?: string;
  execution_state?: string;
  investigation_goal?: string;
  environment?: string;
}): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/investigations/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to start investigation");
  return res.json();
}
