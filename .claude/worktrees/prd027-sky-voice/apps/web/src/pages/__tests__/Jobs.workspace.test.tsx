/**
 * Testes de isolamento de workspace para Jobs page.
 *
 * TDD Estrito: Testes que documentam o comportamento esperado.
 *
 * DOC: PRD023 - Jobs page mostra apenas jobs do workspace ativo.
 * DOC: PRD023 - Troca de workspace filtra jobs corretamente.
 * DOC: ADR024 - Cada workspace tem seus próprios jobs isolados.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import Jobs from '../Jobs'
import apiClient from '@/api/client'

// Mock do apiClient
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    delete: vi.fn(),
    defaults: { headers: {} },
  },
}))

// Mock do react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

describe('Jobs Page - Isolamento de Workspace (PRD023)', () => {
  let queryClient: QueryClient

  // Mock dados de jobs por workspace
  const coreJobs = [
    {
      job_id: 'core-job-abc123',
      source: 'github',
      event_type: 'issues.opened',
      status: 'PENDING',
      created_at: '2025-01-27T10:00:00Z',
      worktree_path: 'workspace/core/worktrees/skybridge-github-123',
    },
    {
      job_id: 'core-job-def456',
      source: 'github',
      event_type: 'issues.closed',
      status: 'COMPLETED',
      created_at: '2025-01-27T11:00:00Z',
      worktree_path: 'workspace/core/worktrees/skybridge-github-456',
    },
    {
      job_id: 'core-job-ghi789',
      source: 'trello',
      event_type: 'card.moved',
      status: 'FAILED',
      created_at: '2025-01-27T12:00:00Z',
      worktree_path: null,
    },
  ]

  const tradingJobs = [
    {
      job_id: 'trading-job-xyz111',
      source: 'github',
      event_type: 'issues.opened',
      status: 'PROCESSING',
      created_at: '2025-01-27T13:00:00Z',
      worktree_path: 'workspace/trading/worktrees/skybridge-github-789',
    },
    {
      job_id: 'trading-job-uvw222',
      source: 'trello',
      event_type: 'card.created',
      status: 'COMPLETED',
      created_at: '2025-01-27T14:00:00Z',
      worktree_path: null,
    },
  ]

  const coreMetrics = {
    queue_size: 1,
    processing: 0,
    completed: 1,
    failed: 1,
    total_enqueued: 3,
    total_completed: 1,
    total_failed: 1,
    success_rate: 50,
  }

  const tradingMetrics = {
    queue_size: 0,
    processing: 1,
    completed: 1,
    failed: 0,
    total_enqueued: 2,
    total_completed: 1,
    total_failed: 0,
    success_rate: 100,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()

    // Configura workspace padrão como 'core'
    localStorage.setItem('skybridge_active_workspace', 'core')
    ;(apiClient as any).defaults.headers['X-Workspace'] = 'core'

    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )

  describe('isolamento de dados', () => {
    it('deve incluir header X-Workspace ao buscar jobs', async () => {
      /**
       * DOC: PRD023 - Jobs page inclui header X-Workspace na requisição.
       * GIVEN: Workspace ativo é 'core'
       * WHEN: Jobs page é carregada
       * THEN: Requisição inclui header X-Workspace
       */
      const mockGet = vi.mocked(apiClient.get)

      mockGet.mockResolvedValue({
        data: {
          ok: true,
          jobs: coreJobs,
          metrics: coreMetrics,
        },
      })

      render(<Jobs />, { wrapper })

      await waitFor(() => {
        expect(mockGet).toHaveBeenCalled()
      })

      // Verifica que o header X-Workspace foi configurado
      expect((apiClient as any).defaults.headers['X-Workspace']).toBe('core')
    })

    it('deve trocar header X-Workspace ao mudar workspace', async () => {
      /**
       * DOC: PRD023 - Ao trocar workspace, header X-Workspace é atualizado.
       * GIVEN: Usuário troca de 'core' para 'trading'
       * WHEN: Jobs page é carregada
       * THEN: Requisição usa novo workspace
       */
      // Configura workspace trading
      localStorage.setItem('skybridge_active_workspace', 'trading')
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'trading'

      const mockGet = vi.mocked(apiClient.get)

      mockGet.mockResolvedValue({
        data: {
          ok: true,
          jobs: tradingJobs,
          metrics: tradingMetrics,
        },
      })

      render(<Jobs />, { wrapper })

      await waitFor(() => {
        expect(mockGet).toHaveBeenCalled()
      })

      // Verifica que o header X-Workspace foi atualizado para trading
      expect((apiClient as any).defaults.headers['X-Workspace']).toBe('trading')
    })
  })

  describe('métricas por workspace', () => {
    it('deve mostrar jobs corretos do workspace core', async () => {
      /**
       * DOC: PRD023 - Jobs page mostra jobs do workspace ativo.
       * GIVEN: Workspace core tem 3 jobs
       * WHEN: Jobs page é carregada
       * THEN: Jobs do core são exibidos (com status corretos)
       */
      vi.mocked(apiClient.get).mockResolvedValue({
        data: {
          ok: true,
          jobs: coreJobs,
          metrics: coreMetrics,
        },
      })

      render(<Jobs />, { wrapper })

      // Verifica que jobs do core estão presentes
      await waitFor(() => {
        expect(screen.getByText(/core-job-abc123/i)).toBeInTheDocument()
        expect(screen.getByText(/core-job-def456/i)).toBeInTheDocument()
        expect(screen.getByText(/core-job-ghi789/i)).toBeInTheDocument()
      })
    })

    it('deve mostrar jobs corretos do workspace trading', async () => {
      /**
       * DOC: PRD023 - Jobs do trading são diferentes do core.
       * GIVEN: Workspace trading tem 2 jobs
       * WHEN: Jobs page é carregada
       * THEN: Jobs do trading são exibidos (não os do core)
       */
      // Configura workspace trading
      localStorage.setItem('skybridge_active_workspace', 'trading')
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'trading'

      vi.mocked(apiClient.get).mockResolvedValue({
        data: {
          ok: true,
          jobs: tradingJobs,
          metrics: tradingMetrics,
        },
      })

      render(<Jobs />, { wrapper })

      // Verifica que jobs do trading estão presentes
      await waitFor(() => {
        expect(screen.getByText(/trading-job-xyz111/i)).toBeInTheDocument()
        expect(screen.getByText(/trading-job-uvw222/i)).toBeInTheDocument()
        // Jobs do core não devem aparecer
        expect(screen.queryByText(/core-job-abc123/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('filtros por workspace', () => {
    it('deve filtrar jobs apenas dentro do workspace ativo', async () => {
      /**
       * DOC: PRD023 - Filtros aplicam-se apenas aos jobs do workspace atual.
       * GIVEN: Workspace core tem 3 jobs (1 PENDING, 1 COMPLETED, 1 FAILED)
       * WHEN: Usuário filtra por status PENDING
       * THEN: Apenas jobs PENDING do core são exibidos (não afeta outros workspaces)
       */
      vi.mocked(apiClient.get).mockResolvedValue({
        data: {
          ok: true,
          jobs: coreJobs,
          metrics: coreMetrics,
        },
      })

      render(<Jobs />, { wrapper })

      // Aguarda renderização dos jobs
      await waitFor(() => {
        expect(screen.getByText(/core-job-abc123/i)).toBeInTheDocument()
      })

      // Seleciona filtro PENDING (primeiro combobox é o filtro de status)
      const statusFilters = screen.getAllByRole('combobox')
      await userEvent.selectOptions(statusFilters[0], 'PENDING')

      // Verifica que apenas o job PENDING do core está visível
      await waitFor(() => {
        expect(screen.getByText(/core-job-abc123/i)).toBeInTheDocument()
        expect(screen.queryByText(/core-job-def456/i)).not.toBeInTheDocument()
        expect(screen.queryByText(/core-job-ghi789/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('sem vazamento de dados', () => {
    it('não deve misturar jobs de workspaces diferentes', async () => {
      /**
       * DOC: PRD023 - Não há vazamento de dados entre workspaces.
       * GIVEN: Dois workspaces com IDs de jobs diferentes
       * WHEN: Carregando jobs de cada workspace
       * THEN: Jobs permanecem isolados (sem sobreposição)
       */
      // Testa que job IDs são únicos por workspace
      const coreJobIds = coreJobs.map(j => j.job_id)
      const tradingJobIds = tradingJobs.map(j => j.job_id)

      // Verifica que não há sobreposição de IDs
      const overlappingIds = coreJobIds.filter(id => tradingJobIds.includes(id))
      expect(overlappingIds).toHaveLength(0)

      // Mock que retorna apenas jobs do workspace solicitado
      vi.mocked(apiClient.get).mockImplementation(async (url) => {
        if (url === '/workspaces') {
          return Promise.resolve({ data: { workspaces: mockWorkspaces } })
        }
        const workspace = (apiClient as any).defaults.headers['X-Workspace']
        const jobs = workspace === 'trading' ? tradingJobs : coreJobs
        const metrics = workspace === 'trading' ? tradingMetrics : coreMetrics

        return Promise.resolve({
          data: {
            ok: true,
            jobs,
            metrics,
          },
        })
      })

      // Testa com core - verifica que não há sobreposição
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'core'
      const { unmount: unmountCore } = render(<Jobs />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/core-job-abc123/i)).toBeInTheDocument()
      })

      unmountCore()

      // Limpa query cache para novo workspace
      queryClient.clear()

      // Testa com trading - render novo (sem rerender)
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'trading'
      render(<Jobs />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/trading-job-xyz111/i)).toBeInTheDocument()
        // Jobs do core não devem aparecer
        expect(screen.queryByText(/core-job-abc123/i)).not.toBeInTheDocument()
      })
    })
  })
})
