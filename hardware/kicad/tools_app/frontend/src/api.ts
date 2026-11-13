export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'timed_out';

export interface ModuleParameter {
  name: string;
  label: string;
  description: string;
  kind: 'positional' | 'option';
  type: 'string' | 'integer' | 'number' | 'boolean' | 'enum' | 'file' | 'directory' | 'string_list';
  required: boolean;
  default: unknown;
  minimum?: number;
  maximum?: number;
  extensions?: string[];
  choices?: Array<string | number>;
  may_create?: boolean;
}
export interface ModuleDefinition {
  id: string;
  name: string;
  description: string;
  category: string;
  execution_type: 'read_only' | 'kicad_modify' | 'file_generate' | 'system_control';
  requires_kicad: boolean;
  requires_pcb_editor: boolean;
  requires_kicad_api: boolean;
  timeout_seconds: number;
  parameters: ModuleParameter[];
  risk: { level: string; summary: string; confirmation_required: boolean };
}
export interface RunRecord {
  id: string;
  module_id: string;
  parameters: Record<string, unknown>;
  status: RunStatus;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  exit_code: number | null;
  error_summary: string | null;
  artifacts: string[];
}
export interface RunOutput {
  stdout: string;
  stderr: string;
}
export interface AppSettings {
  allowed_roots: string[];
  python_executable: string;
  kicad_executable: string;
  kicad_cli_executable: string;
  max_concurrent_runs: number;
  history_limit: number;
  frontend_origin: string;
}
interface ExecutableStatus {
  configured: string;
  available: boolean;
  resolved: string | null;
}
export interface HealthReport {
  status: string;
  python: ExecutableStatus;
  kicad: ExecutableStatus;
  kicad_cli: ExecutableStatus;
  kipy_importable: boolean;
  kicad_api_socket: string | null;
  pcb_editor_reachable: boolean;
}

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
};

export const api = {
  modules: (): Promise<ModuleDefinition[]> => request('/api/modules'),
  health: (): Promise<HealthReport> => request('/api/health'),
  runs: (): Promise<RunRecord[]> => request('/api/runs'),
  run: (id: string): Promise<RunRecord> => request(`/api/runs/${id}`),
  output: (id: string): Promise<RunOutput> => request(`/api/runs/${id}/output`),
  start: (
    moduleId: string,
    parameters: Record<string, unknown>,
    confirmed: boolean
  ): Promise<RunRecord> =>
    request('/api/runs', {
      method: 'POST',
      body: JSON.stringify({ module_id: moduleId, parameters, confirmed })
    }),
  cancel: (id: string): Promise<RunRecord> => request(`/api/runs/${id}/cancel`, { method: 'POST' }),
  settings: (): Promise<AppSettings> => request('/api/settings'),
  saveSettings: (settings: AppSettings): Promise<AppSettings> =>
    request('/api/settings', { method: 'PUT', body: JSON.stringify(settings) })
};
