import apiClient from './client'

/**
 * Endpoints da API Skybridge.
 * Funções tipadas para comunicação com o backend.
 */

// =============================================================================
// HEALTH & DISCOVERY
// =============================================================================

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
}

export interface DiscoverResponse {
  handlers: Array<{
    method: string
    kind: 'query' | 'command'
    description: string
    input_schema: Record<string, unknown>
    output_schema: Record<string, unknown>
  }>
}

export const healthApi = {
  get: () => apiClient.get<HealthResponse>('/health'),
}

export const discoverApi = {
  list: () => apiClient.get<DiscoverResponse>('/discover'),
  getMethod: (method: string) => apiClient.get(`/discover/${method}`),
}

// =============================================================================
// WEBHOOKS & JOBS
// =============================================================================

export enum JobStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  TIMED_OUT = 'TIMED_OUT',
}

export interface WebhookJob {
  job_id: string
  source: string
  event_type: string
  status: JobStatus
  created_at: string
  worktree_path?: string
}

export interface Worktree {
  name: string
  path: string
  status?: string
  snapshot?: Record<string, unknown>
}

export interface JobMetrics {
  queue_size: number
  processing: number
  completed: number
  failed: number
  total_enqueued: number
  total_completed: number
  total_failed: number
  success_rate: number
}

export const webhooksApi = {
  listJobs: () => apiClient.get<{
    ok: boolean
    jobs: WebhookJob[]
    metrics: JobMetrics
  }>('/webhooks/jobs'),
  listWorktrees: () => apiClient.get<{ worktrees: Worktree[] }>('/webhooks/worktrees'),
  getWorktree: (name: string) =>
    apiClient.get<{
      name: string
      path: string
      agent_log?: string
      snapshot?: Record<string, unknown>
    }>(`/webhooks/worktrees/${name}`),
  deleteWorktree: (name: string, password: string) =>
    apiClient.delete<{ ok: boolean; message: string }>(`/webhooks/worktrees/${name}`, { params: { password } }),
}

// =============================================================================
// OBSERVABILITY & LOGS
// =============================================================================

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  SUCCESS = 'SUCCESS',
}

export const logsApi = {
  get: (params: { tail?: number; level?: LogLevel }) =>
    apiClient.get<{ lines: string[] }>('/observability/logs', { params }),
}
