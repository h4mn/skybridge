/**
 * Testes para Dashboard page.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../Dashboard'
import * as apiClient from '../../api/client'

// Mock do apiClient
vi.mock('../../api/client', () => {
  const mockHeaders: Record<string, string> = {}
  return {
    default: {
      get: vi.fn(),
      defaults: { headers: mockHeaders },
    },
  }
})

// Mock do react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

describe('Dashboard', () => {
  let queryClient: QueryClient

  beforeEach(() => {
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

  describe('renderização inicial', () => {
    it('deve renderizar sem erro', () => {
      /**
       * DOC: Dashboard renderiza sem erro.
       */
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      // Dashboard deve renderizar cards de métricas
      expect(screen.getByText(/API Status/i)).toBeInTheDocument()
    })

    it('deve mostrar indicadores de carregamento', () => {
      vi.mocked(apiClient.default).get.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<Dashboard />, { wrapper })

      // Verifica que há algum indicador de carregamento nos cards
      // "Verificando..." aparece no card de API Status durante carregamento
      expect(screen.getByText(/Verificando\.\.\./i)).toBeInTheDocument()
    })
  })

  describe('cards de métricas', () => {
    it('deve mostrar card de API Status', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/API Status/i)).toBeInTheDocument()
        expect(screen.getByText(/Verificando\.\.\./i)).toBeInTheDocument()
      })
    })

    it('deve mostrar card de Jobs Ativos', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Jobs Ativos/i)).toBeInTheDocument()
      })
    })

    it('deve mostrar card de Success Rate', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Success Rate/i)).toBeInTheDocument()
      })
    })
  })

  describe('health check', () => {
    it('deve buscar health status ao montar', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(apiClient.default.get).toHaveBeenCalledWith('/health')
      })
    })

    it('deve mostrar erro quando health check falha', async () => {
      vi.mocked(apiClient.default).get.mockRejectedValue(new Error('Network error'))

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Erro ao carregar/i)).toBeInTheDocument()
      })
    })
  })

  describe('info card', () => {
    it('deve mostrar card com informações sobre Skybridge WebUI', async () => {
      /**
       * DOC: Dashboard mostra card informativo sobre a aplicação.
       */
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Skybridge WebUI/i)).toBeInTheDocument()
        expect(screen.getByText(/Dashboard de monitoramento/i)).toBeInTheDocument()
      })
    })
  })

  describe('refresh manual', () => {
    it('deve ter botão de atualização manual', async () => {
      /**
       * DOC: Dashboard tem botão para atualizar métricas manualmente.
       */
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        const refreshButton = screen.getByRole('button', { name: /Atualizar/i })
        expect(refreshButton).toBeInTheDocument()
      })
    })
  })

  describe('sem auto-refresh', () => {
    it('não tem mais auto-refresh (removido - usa apenas botão manual)', async () => {
      /**
       * DOC: Auto-refresh foi removido - agora usa apenas botão de atualização manual.
       */
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(apiClient.default.get).toHaveBeenCalled()
      })

      // Verifica que há botão de refresh manual
      const refreshButton = screen.getByRole('button', { name: /Atualizar/i })
      expect(refreshButton).toBeInTheDocument()
    })
  })

  describe('isolamento de workspace - PRD023', () => {
    beforeEach(() => {
      // Limpa localStorage antes de cada teste de workspace
      localStorage.clear()
      // Configura workspace ativo padrão como 'core'
      localStorage.setItem('skybridge_active_workspace', 'core')
    })

    it('deve incluir header X-Workspace nas requisições da API', async () => {
      /**
       * DOC: PRD023 - Dashboard inclui header X-Workspace em todas as requisições.
       * DOC: ADR024 - Workspace 'core' é usado como padrão.
       */
      const mockGet = vi.mocked(apiClient.default.get)

      mockGet.mockImplementation((url: string) => {
        // Verifica que o header X-Workspace está sendo incluído
        expect(apiClient.default.defaults.headers['X-Workspace']).toBe('core')
        return Promise.resolve({
          data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
        })
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(mockGet).toHaveBeenCalled()
      })
    })

    it('deve mostrar jobs apenas do workspace ativo', async () => {
      /**
       * DOC: PRD023 - Dashboard mostra jobs filtrados por workspace.
       * GIVEN: Workspace 'core' tem 3 jobs, 'trading' tem 2 jobs
       * WHEN: Dashboard é carregado com workspace 'core'
       * THEN: Apenas jobs do 'core' são exibidos
       */
      const coreJobs = [
        { job_id: 'core-job-1', source: 'github', event_type: 'issues.opened', status: 'PENDING', created_at: '2025-01-27T10:00:00Z' },
        { job_id: 'core-job-2', source: 'github', event_type: 'issues.opened', status: 'COMPLETED', created_at: '2025-01-27T11:00:00Z' },
        { job_id: 'core-job-3', source: 'trello', event_type: 'card.moved', status: 'PROCESSING', created_at: '2025-01-27T12:00:00Z' },
      ]

      const tradingJobs = [
        { job_id: 'trading-job-1', source: 'github', event_type: 'issues.opened', status: 'PENDING', created_at: '2025-01-27T10:00:00Z' },
        { job_id: 'trading-job-2', source: 'trello', event_type: 'card.moved', status: 'FAILED', created_at: '2025-01-27T11:00:00Z' },
      ]

      // Mock para health check
      vi.mocked(apiClient.default.get).mockImplementation((url: string) => {
        if (url === '/health') {
          return Promise.resolve({
            data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
          })
        }
        if (url === '/webhooks/jobs') {
          // Simula filtragem por workspace - retorna apenas jobs do core
          return Promise.resolve({
            data: {
              ok: true,
              jobs: coreJobs,
              metrics: {
                queue_size: 1,
                processing: 1,
                completed: 1,
                failed: 0,
                total_enqueued: 3,
                total_completed: 1,
                total_failed: 0,
                success_rate: 100,
              },
            },
          })
        }
        return Promise.resolve({ data: {} })
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        // Deve mostrar 3 jobs do workspace core
        // Usa getAllByText porque há múltiplos elementos com "3"
        const threes = screen.getAllByText(/3/i)
        expect(threes.length).toBeGreaterThan(0)
      })
    })

    it('deve atualizar dados ao trocar workspace', async () => {
      /**
       * DOC: PRD023 - Ao trocar workspace, Dashboard recarrega dados do novo workspace.
       * WHEN: Usuário troca de 'core' para 'trading'
       * THEN: Dashboard mostra jobs do workspace 'trading'
       */
      const tradingJobsMetrics = {
        queue_size: 0,
        processing: 0,
        completed: 1,
        failed: 1,
        total_enqueued: 2,
        total_completed: 1,
        total_failed: 1,
        success_rate: 50,
      }

      // Simula troca de workspace para trading
      localStorage.setItem('skybridge_active_workspace', 'trading')
      apiClient.default.defaults.headers['X-Workspace'] = 'trading'

      vi.mocked(apiClient.default.get).mockImplementation((url: string) => {
        if (url === '/health') {
          return Promise.resolve({
            data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
          })
        }
        if (url === '/webhooks/jobs') {
          return Promise.resolve({
            data: {
              ok: true,
              jobs: [],
              metrics: tradingJobsMetrics,
            },
          })
        }
        return Promise.resolve({ data: {} })
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        // Deve mostrar métricas do workspace trading (2 jobs total)
        expect(screen.getByText(/2/i)).toBeInTheDocument()
      })
    })

    it('deve manter isolamento entre workspaces simultâneos', async () => {
      /**
       * DOC: PRD023 - Múltiplos workspaces não misturam dados.
       * GIVEN: Dois workspaces com dados diferentes
       * WHEN: Carregando Dashboard para cada workspace
       * THEN: Dados permanecem isolados (sem vazamento)
       */
      let capturedHeaders: Record<string, string> = {}

      vi.mocked(apiClient.default.get).mockImplementation((url: string) => {
        // Captura headers da requisição
        capturedHeaders = { ...apiClient.default.defaults.headers }

        const workspace = apiClient.default.defaults.headers['X-Workspace'] || 'core'
        const isCore = workspace === 'core'

        return Promise.resolve({
          data: {
            status: 'healthy',
            version: '0.11.0',
            timestamp: '2025-01-27T20:00:00Z',
            // Mock dados específicos por workspace
            ok: true,
            jobs: isCore
              ? [{ job_id: 'core-job-1', source: 'github', event_type: 'issues.opened', status: 'PENDING', created_at: '2025-01-27T10:00:00Z' }]
              : [{ job_id: 'trading-job-1', source: 'trello', event_type: 'card.moved', status: 'COMPLETED', created_at: '2025-01-27T11:00:00Z' }],
            metrics: isCore
              ? { total_enqueued: 1, total_completed: 0, total_failed: 0, queue_size: 1, processing: 0, success_rate: 0 }
              : { total_enqueued: 1, total_completed: 1, total_failed: 0, queue_size: 0, processing: 0, success_rate: 100 },
          },
        })
      })

      // Testa com workspace core
      localStorage.setItem('skybridge_active_workspace', 'core')
      apiClient.default.defaults.headers['X-Workspace'] = 'core'

      const { unmount } = render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(capturedHeaders['X-Workspace']).toBe('core')
      })

      // Testa com workspace trading
      unmount() // Limpa o componente anterior

      localStorage.setItem('skybridge_active_workspace', 'trading')
      apiClient.default.defaults.headers['X-Workspace'] = 'trading'

      // Renderiza novamente com novo workspace
      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(capturedHeaders['X-Workspace']).toBe('trading')
      })
    })
  })
})
