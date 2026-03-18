/**
 * MSW (Mock Service Worker) Handlers.
 *
 * Mocka as requisições da API Skybridge para testes.
 */

import { http, HttpResponse } from 'msw'

const API_BASE = 'http://localhost:8000'

export const handlers = [
  // Health Check
  http.get(`${API_BASE}/api/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '0.11.0.dev',
      timestamp: new Date().toISOString(),
    })
  }),

  // Discover
  http.get(`${API_BASE}/api/discover`, () => {
    return HttpResponse.json({
      handlers: [
        {
          method: 'read_file',
          kind: 'query',
          description: 'Lê conteúdo de um arquivo',
          module: 'kernel.queries.read_file',
        },
        {
          method: 'write_file',
          kind: 'command',
          description: 'Escreve conteúdo em um arquivo',
          module: 'kernel.commands.write_file',
        },
      ],
    })
  }),

  // Webhooks - List Jobs
  http.get(`${API_BASE}/api/webhooks/jobs`, () => {
    return HttpResponse.json({
      jobs: [
        {
          id: 'test-job-1',
          event_type: 'issues',
          status: 'pending',
          created_at: new Date().toISOString(),
        },
        {
          id: 'test-job-2',
          event_type: 'issues',
          status: 'processing',
          created_at: new Date().toISOString(),
        },
      ],
    })
  }),

  // Webhooks - Job Metrics
  http.get(`${API_BASE}/api/observability/jobs/metrics`, () => {
    return HttpResponse.json({
      total: 150,
      by_status: {
        pending: 50,
        processing: 25,
        completed: 60,
        failed: 15,
      },
    })
  }),

  // Logs - Files
  http.get(`${API_BASE}/api/logs/files`, () => {
    return HttpResponse.json({
      ok: true,
      files: [
        { name: 'skybridge-2025-01-27.log', size: 12345 },
        { name: 'skybridge-2025-01-26.log', size: 11200 },
      ],
    })
  }),

  // Logs - Stream
  http.get(`${API_BASE}/api/logs/stream`, () => {
    return HttpResponse.json({
      logs: [
        {
          timestamp: '2025-01-27 20:00:00',
          level: 'INFO',
          logger: 'skybridge',
          message: 'Test log message',
          message_html: '<span>Test log message</span>',
        },
      ],
    })
  }),

  // Worktrees - List
  http.get(`${API_BASE}/api/fileops/worktrees`, () => {
    return HttpResponse.json({
      worktrees: [
        {
          name: 'test-worktree-1',
          branch: 'feature/test-1',
          commit: 'abc123',
          created_at: '2025-01-27T10:00:00Z',
        },
      ],
    })
  }),

  // Worktrees - Git Diff
  http.post(`${API_BASE}/api/fileops/git-diff`, async ({ request }) => {
    const body = await request.json() as { worktree: string }

    // Retornar diff diferente baseado na worktree
    if (body.worktree === 'test-worktree-with-changes') {
      return HttpResponse.json({
        summary: {
          added: 3,
          modified: 5,
          deleted: 1,
        },
        files: [
          { path: 'src/test.tsx', status: 'M' },
          { path: 'src/new.tsx', status: 'A' },
          { path: 'src/old.tsx', status: 'D' },
        ],
        diffs: {
          'src/test.tsx': '@@ -1,3 +1,4 @@\n-test\n+test2',
        },
      })
    }

    return HttpResponse.json({
      summary: { added: 0, modified: 0, deleted: 0 },
      files: [],
      diffs: {},
    })
  }),

  // Worktrees - Create
  http.post(`${API_BASE}/api/fileops/worktrees`, async () => {
    return HttpResponse.json({
      name: 'new-worktree',
      branch: 'feature/new-branch',
      created_at: new Date().toISOString(),
    })
  }),

  // Worktrees - Delete
  http.delete(`${API_BASE}/api/fileops/worktrees/:name`, () => {
    return HttpResponse.json({ success: true })
  }),
]

export default handlers
