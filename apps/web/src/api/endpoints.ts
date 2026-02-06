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

  getJobMetrics: () =>
    apiClient.get<{
      ok: boolean
      metrics: JobMetrics
    }>('/webhooks/metrics'),
}

// =============================================================================
// WORKSPACES
// =============================================================================

export interface Workspace {
  id: string
  name: string
  path: string
  description: string
  auto: boolean
  enabled: boolean
}

export interface WorkspacesListResponse {
  workspaces: Workspace[]
}

export const workspacesApi = {
  list: () =>
    apiClient.get<WorkspacesListResponse>('/workspaces'),

  get: (id: string) =>
    apiClient.get<Workspace>(`/workspaces/${id}`),

  create: (data: {
    id: string
    name: string
    path: string
    description?: string
  }) =>
    apiClient.post<Workspace>('/workspaces', data),

  delete: (id: string) =>
    apiClient.delete<{ message: string }>(`/workspaces/${id}`),
}

// =============================================================================
// KANBAN (Fase 1: Leitura - LEGADO)
// =============================================================================

export enum CardStatus {
  BACKLOG = 'backlog',
  TODO = 'todo',
  IN_PROGRESS = 'in_progress',
  REVIEW = 'review',
  DONE = 'done',
  BLOCKED = 'blocked',
  CHALLENGE = 'challenge',
}

export interface KanbanCard {
  id: string
  title: string
  description: string | null
  status: CardStatus
  labels: string[]
  due_date: string | null
  url: string
  list_name: string
  created_at: string | null
}

export interface KanbanBoard {
  id: string
  name: string
  url: string
}

export interface KanbanList {
  id: string
  name: string
  position: number
}

export interface KanbanBoardResponse {
  ok: boolean
  board: KanbanBoard | null
  cards: KanbanCard[]
  lists: KanbanList[]
}

export const kanbanApi = {
  getBoard: () =>
    apiClient.get<KanbanBoardResponse>('/kanban/board'),
}

// =============================================================================
// KANBAN FASE 2: kanban.db (Fonte Única da Verdade)
// =============================================================================

// Interfaces para nova API kanban.db
export interface KanbanDbBoard {
  id: string
  name: string
  trello_board_id: string | null
  trello_sync_enabled: boolean
  created_at: string
  updated_at: string
}

export interface KanbanDbList {
  id: string
  board_id: string
  name: string
  position: number
  trello_list_id: string | null
}

export interface KanbanDbCard {
  id: string
  list_id: string
  title: string
  description: string | null
  position: number
  labels: string[]
  due_date: string | null
  being_processed: boolean
  processing_started_at: string | null
  processing_job_id: string | null
  processing_step: number
  processing_total_steps: number
  processing_progress_percent: number
  issue_number: number | null
  issue_url: string | null
  pr_url: string | null
  trello_card_id: string | null
  created_at: string
  updated_at: string
}

export interface CreateCardRequest {
  list_id: string
  title: string
  description?: string
  position?: number
  labels?: string[]
  due_date?: string
  issue_number?: number
  issue_url?: string
}

export interface UpdateCardRequest {
  title?: string
  description?: string
  list_id?: string  // Mover entre listas
  position?: number
  labels?: string[]
  due_date?: string
  being_processed?: boolean
  processing_job_id?: string
  processing_step?: number
  processing_total_steps?: number
}

// Card History
export interface CardHistory {
  id: number | null
  card_id: string
  event: string  // 'created' | 'moved' | 'updated' | 'processing_started' | 'processing_completed' | 'deleted'
  from_list_id: string | null
  to_list_id: string | null
  metadata: string | null  // JSON string
  created_at: string
}

export const kanbanDbApi = {
  // Boards
  getBoards: () =>
    apiClient.get<KanbanDbBoard[]>('/kanban/boards'),
  getBoard: (id: string) =>
    apiClient.get<KanbanDbBoard>(`/kanban/boards/${id}`),
  createBoard: (data: { id: string; name: string }) =>
    apiClient.post<KanbanDbBoard>('/kanban/boards', data),

  // Lists
  getLists: (boardId?: string) =>
    apiClient.get<KanbanDbList[]>(`/kanban/lists${boardId ? `?board_id=${boardId}` : ''}`),
  createList: (data: { id: string; board_id: string; name: string; position?: number }) =>
    apiClient.post<KanbanDbList>('/kanban/lists', data),

  // Cards
  getCards: (filters?: { list_id?: string; being_processed?: boolean }) =>
    apiClient.get<KanbanDbCard[]>(
      '/kanban/cards' +
      (filters?.list_id ? `?list_id=${filters.list_id}` : '') +
      (filters?.being_processed !== undefined ? `${filters?.list_id ? '&' : '?'}being_processed=${filters.being_processed}` : '')
    ),
  getCard: (id: string) =>
    apiClient.get<KanbanDbCard>(`/kanban/cards/${id}`),
  createCard: (data: CreateCardRequest) =>
    apiClient.post<KanbanDbCard>('/kanban/cards', data),
  updateCard: (id: string, data: UpdateCardRequest) =>
    apiClient.patch<KanbanDbCard>(`/kanban/cards/${id}`, data),
  deleteCard: (id: string) =>
    apiClient.delete(`/kanban/cards/${id}`),

  // Card History
  getCardHistory: (id: string) =>
    apiClient.get<CardHistory[]>(`/kanban/cards/${id}/history`),

  // Initialize
  initialize: () =>
    apiClient.post<{ ok: boolean; message: string; workspace: string }>('/kanban/initialize'),
}
