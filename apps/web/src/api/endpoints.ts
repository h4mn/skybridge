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

export const observabilityApi = {
  getLogFiles: () =>
    apiClient.get<{ ok: boolean; files: Array<{ name: string; size: number; modified: string }> }>('/logs/files'),
  streamLogs: (filename: string, tail: number = 50) =>
    apiClient.get<{ ok: boolean; total: number; page: number; per_page: number; entries: Array<{ timestamp: string; level: string; logger: string; message: string; message_html: string }> }>(
      `/logs/file/${filename}`,
      { params: { page: 1, per_page: tail } }
    ),
}

// =============================================================================
// AGENTS EXECUTIONS
// =============================================================================

export enum AgentState {
  CREATED = 'created',
  RUNNING = 'running',
  TIMED_OUT = 'timed_out',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface AgentResult {
  success: boolean
  changes_made: boolean
  files_created: string[]
  files_modified: string[]
  files_deleted: string[]
  commit_hash: string | null
  pr_url: string | null
  message: string
  issue_title: string
  output_message: string
  thinkings: unknown[]
}

export interface AgentExecution {
  agent_type: string
  job_id: string
  worktree_path: string
  skill: string
  state: AgentState
  result: AgentResult | null
  error_message: string | null
  duration_ms: number | null
  timeout_seconds: number
  timestamps: {
    created_at: string
    started_at: string | null
    completed_at: string | null
  }
}

export interface AgentMetrics {
  total: number
  created: number
  running: number
  completed: number
  failed: number
  timed_out: number
  success_rate: number | null
}

export interface AgentMessage {
  timestamp?: string
  type?: string
  content: string
}

export interface AgentExecutionWithMessages extends AgentExecution {
  messages?: string[]
  stdout?: string
}

export const agentsApi = {
  listExecutions: (limit: number = 100) =>
    apiClient.get<{
      ok: boolean
      executions: AgentExecution[]
      metrics: AgentMetrics
    }>('/agents/executions', { params: { limit } }),

  getExecution: (jobId: string) =>
    apiClient.get<{
      ok: boolean
      execution: AgentExecution
    }>(`/agents/executions/${jobId}`),

  getMessages: (jobId: string) =>
    apiClient.get<{
      ok: boolean
      job_id: string
      messages: string[]
      stdout: string
    }>(`/agents/executions/${jobId}/messages`),

  getMetrics: () =>
    apiClient.get<{
      ok: boolean
      metrics: AgentMetrics
    }>('/agents/metrics'),
}
