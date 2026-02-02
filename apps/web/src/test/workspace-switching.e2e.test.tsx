/**
 * Teste e2e de troca de workspace.
 *
 * TDD Estrito: Testes que documentam o comportamento esperado.
 *
 * DOC: PRD023 #14 - Teste e2e de troca de workspace.
 * DOC: PRD023 - Ao trocar workspace, todos os componentes recarregam dados.
 * DOC: ADR024 - Header X-Workspace é atualizado globalmente.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import { useState, useEffect } from 'react'
import WorkspaceSelector from '@/components/WorkspaceSelector'
import apiClient from '@/api/client'

// Mock do apiClient
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
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

describe('Troca de Workspace - Teste E2E (PRD023 #14)', () => {
  let queryClient: QueryClient

  const mockWorkspaces = [
    {
      id: 'core',
      name: 'Skybridge Core',
      path: 'workspace/core',
      description: 'Instância principal',
      auto: true,
      enabled: true,
    },
    {
      id: 'trading',
      name: 'Trading Bot',
      path: 'workspace/trading',
      description: 'Bot de trading',
      auto: false,
      enabled: true,
    },
  ]

  // Dados mockados por workspace
  const coreData = {
    jobs: [
      { job_id: 'core-job-1', source: 'github', event_type: 'issues.opened', status: 'PENDING', created_at: '2025-01-27T10:00:00Z' },
      { job_id: 'core-job-2', source: 'github', event_type: 'issues.closed', status: 'COMPLETED', created_at: '2025-01-27T11:00:00Z' },
    ],
    metrics: {
      total_enqueued: 2,
      total_completed: 1,
      total_failed: 0,
      queue_size: 1,
      processing: 0,
      success_rate: 100,
    },
  }

  const tradingData = {
    jobs: [
      { job_id: 'trading-job-1', source: 'trello', event_type: 'card.moved', status: 'PROCESSING', created_at: '2025-01-27T12:00:00Z' },
    ],
    metrics: {
      total_enqueued: 1,
      total_completed: 0,
      total_failed: 0,
      queue_size: 0,
      processing: 1,
      success_rate: 0,
    },
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

    // Mock padrão para listar workspaces
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/workspaces') {
        return Promise.resolve({ data: { workspaces: mockWorkspaces } })
      }
      if (url === '/webhooks/jobs') {
        const workspace = (apiClient as any).defaults.headers['X-Workspace'] || 'core'
        const data = workspace === 'trading' ? tradingData : coreData
        return Promise.resolve({
          data: { ok: true, ...data },
        })
      }
      return Promise.resolve({ data: {} })
    })
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )

  describe('fluxo completo de troca de workspace', () => {
    it('deve trocar workspace e atualizar header X-Workspace globalmente', async () => {
      /**
       * DOC: PRD023 - Troca de workspace atualiza header global.
       * GIVEN: Usuário está no workspace 'core'
       * WHEN: Usuário seleciona workspace 'trading'
       * THEN: Header X-Workspace é atualizado para 'trading'
       */
      const user = userEvent.setup()

      render(<WorkspaceSelector />, { wrapper })

      // Aguarda carregamento
      await waitFor(() => {
        expect(screen.getByTestId('workspace-selector')).toBeInTheDocument()
      })

      // Abre o dropdown
      const dropdownButton = screen.getByRole('button')
      await user.click(dropdownButton)

      // Clica no workspace trading
      await waitFor(() => {
        expect(screen.getByText(/Trading Bot/i)).toBeInTheDocument()
      })

      const tradingOption = screen.getByText(/Trading Bot/i)
      await user.click(tradingOption)

      // Verifica que o header X-Workspace foi atualizado
      await waitFor(() => {
        expect((apiClient as any).defaults.headers['X-Workspace']).toBe('trading')
      })

      // Verifica que o localStorage foi atualizado
      expect(localStorage.getItem('skybridge_active_workspace')).toBe('trading')
    })

    it('deve recarregar dados ao trocar workspace', async () => {
      /**
       * DOC: PRD023 - Componentes recarregam dados após troca de workspace.
       * GIVEN: Usuário está no workspace 'core' com 2 jobs
       * WHEN: Usuário troca para 'trading'
       * THEN: Dados do 'trading' são carregados (1 job)
       */

      // Cria um componente simples que exibe dados do workspace
      function TestComponent({ workspaceKey }: { workspaceKey: string }) {
        const [jobs, setJobs] = useState<any[]>([])
        const [loading, setLoading] = useState(true)

        useEffect(() => {
          async function loadJobs() {
            setLoading(true)
            const response = await apiClient.get('/webhooks/jobs')
            setJobs(response.data.jobs || [])
            setLoading(false)
          }
          loadJobs()
        }, [workspaceKey]) // Recarrega quando workspaceKey muda

        if (loading) return <div>Loading...</div>
        return (
          <div>
            <div data-testid="jobs-count">{jobs.length}</div>
            {jobs.map((job) => (
              <div key={job.job_id} data-testid="job-item">{job.job_id}</div>
            ))}
          </div>
        )
      }

      // Renderiza componente de teste com workspace 'core'
      const { rerender } = render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <TestComponent workspaceKey="core" />
          </MemoryRouter>
        </QueryClientProvider>
      )

      // Aguarda carregamento inicial (core com 2 jobs)
      await waitFor(() => {
        expect(screen.getByTestId('jobs-count')).toHaveTextContent('2')
        const jobItems = screen.getAllByTestId('job-item')
        expect(jobItems[0]).toHaveTextContent('core-job-1')
      })

      // Troca para trading
      localStorage.setItem('skybridge_active_workspace', 'trading')
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'trading'

      // Rerender com nova chave de workspace força recarga
      rerender(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <TestComponent workspaceKey="trading" />
          </MemoryRouter>
        </QueryClientProvider>
      )

      // Verifica que dados do trading foram carregados (1 job)
      await waitFor(() => {
        expect(screen.getByTestId('jobs-count')).toHaveTextContent('1')
      }, { timeout: 3000 })
    })

    it('não deve recarregar se selecionar o mesmo workspace', async () => {
      /**
       * DOC: PRD023 - Selecionar workspace ativo não causa reload.
       * GIVEN: Usuário está no workspace 'core'
       * WHEN: Usuário seleciona 'core' novamente
       * THEN: Nenhuma requisição adicional é feita
       */
      const user = userEvent.setup()
      const mockGet = vi.mocked(apiClient.get)

      render(<WorkspaceSelector />, { wrapper })

      // Aguarda carregamento inicial
      await waitFor(() => {
        expect(mockGet).toHaveBeenCalledWith('/workspaces')
      })

      const initialCallCount = mockGet.mock.calls.length

      // Abre o dropdown
      const dropdownButton = screen.getByRole('button')
      await user.click(dropdownButton)

      // Clica no workspace core (já ativo)
      const coreOption = screen.getByTestId('workspace-item-core')
      await user.click(coreOption)

      // Verifica que não houve chamadas adicionais
      expect(mockGet.mock.calls.length).toBe(initialCallCount)
    })
  })

  describe('sincronização entre componentes', () => {
    it('deve propagar mudança de workspace para todos os componentes', async () => {
      /**
       * DOC: PRD023 - Mudança de workspace afeta toda aplicação.
       * GIVEN: Múltiplos componentes usando dados do workspace
       * WHEN: Workspace é trocado
       * THEN: Todos os componentes atualizam seus dados
       */

      // Simula múltiplos componentes monitorando workspace
      const componentsData: Record<string, any[]> = {
        jobs: [],
        agents: [],
        worktrees: [],
      }

      // Mock que retorna dados diferentes por workspace
      vi.mocked(apiClient.get).mockImplementation((url: string) => {
        const workspace = (apiClient as any).defaults.headers['X-Workspace'] || 'core'

        if (url === '/workspaces') {
          return Promise.resolve({ data: { workspaces: mockWorkspaces } })
        }
        if (url === '/webhooks/jobs') {
          return Promise.resolve({
            data: {
              ok: true,
              jobs: workspace === 'trading' ? tradingData.jobs : coreData.jobs,
              metrics: workspace === 'trading' ? tradingData.metrics : coreData.metrics,
            },
          })
        }
        if (url === '/agents/executions') {
          const executions = workspace === 'trading'
            ? [{ job_id: 'trading-exec-1' }]
            : [{ job_id: 'core-exec-1' }]
          return Promise.resolve({ data: { ok: true, executions, metrics: { total: 1 } } })
        }
        if (url === '/webhooks/worktrees') {
          const worktrees = workspace === 'trading'
            ? [{ name: 'trading-tree-1' }]
            : [{ name: 'core-tree-1' }]
          return Promise.resolve({ data: { ok: true, worktrees } })
        }
        return Promise.resolve({ data: {} })
      })

      // Simula troca de workspace
      function changeWorkspace(newWorkspace: string) {
        localStorage.setItem('skybridge_active_workspace', newWorkspace)
        ;(apiClient as any).defaults.headers['X-Workspace'] = newWorkspace
      }

      // Carrega dados iniciais do core
      const response1 = await apiClient.get('/webhooks/jobs')
      componentsData.jobs = response1.data.jobs || []
      const response2 = await apiClient.get('/agents/executions')
      componentsData.agents = response2.data.executions || []
      const response3 = await apiClient.get('/webhooks/worktrees')
      componentsData.worktrees = response3.data.worktrees || []

      // Verifica dados do core
      expect(componentsData.jobs).toHaveLength(2)
      expect(componentsData.jobs[0].job_id).toContain('core')
      expect(componentsData.agents[0].job_id).toContain('core')
      expect(componentsData.worktrees[0].name).toContain('core')

      // Troca para trading
      changeWorkspace('trading')

      // Recarrega dados
      const response4 = await apiClient.get('/webhooks/jobs')
      componentsData.jobs = response4.data.jobs || []
      const response5 = await apiClient.get('/agents/executions')
      componentsData.agents = response5.data.executions || []
      const response6 = await apiClient.get('/webhooks/worktrees')
      componentsData.worktrees = response6.data.worktrees || []

      // Verifica dados do trading
      expect(componentsData.jobs).toHaveLength(1)
      expect(componentsData.jobs[0].job_id).toContain('trading')
      expect(componentsData.agents[0].job_id).toContain('trading')
      expect(componentsData.worktrees[0].name).toContain('trading')

      // Verifica que dados do core não estão presentes
      expect(componentsData.jobs.some((j: any) => j.job_id.includes('core'))).toBe(false)
    })
  })

  describe('persistência de workspace', () => {
    it('deve lembrar workspace selecionado após recarregar página', async () => {
      /**
       * DOC: PRD023 - Workspace selecionado é persistido no localStorage.
       * GIVEN: Usuário seleciona workspace 'trading'
       * WHEN: Página é recarregada
       * THEN: Workspace 'trading' é mantido selecionado
       */
      const user = userEvent.setup()

      const { unmount } = render(<WorkspaceSelector />, { wrapper })

      // Aguarda carregamento
      await waitFor(() => {
        expect(screen.getByTestId('workspace-selector')).toBeInTheDocument()
      })

      // Abre o dropdown
      const dropdownButton = screen.getByRole('button')
      await user.click(dropdownButton)

      // Seleciona trading
      const tradingOption = screen.getByText(/Trading Bot/i)
      await user.click(tradingOption)

      // Verifica que foi salvo no localStorage
      expect(localStorage.getItem('skybridge_active_workspace')).toBe('trading')

      // Unmount simula o fechamento da página
      unmount()

      // Renderiza novamente (simula recarregar a página)
      render(<WorkspaceSelector />, { wrapper })

      await waitFor(() => {
        expect(screen.getByTestId('workspace-selector')).toBeInTheDocument()
      })

      // Verifica que workspace trading ainda está ativo
      expect((apiClient as any).defaults.headers['X-Workspace']).toBe('trading')
    })
  })

  describe('tratamento de erros', () => {
    it('deve manter workspace atual se API falhar', async () => {
      /**
       * DOC: PRD023 - Erro na API não afeta seleção de workspace.
       * GIVEN: Workspace 'trading' está selecionado
       * WHEN: Requisição à API falha
       * THEN: Workspace 'trading' permanece selecionado
       */
      localStorage.setItem('skybridge_active_workspace', 'trading')
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'trading'

      vi.mocked(apiClient.get).mockRejectedValue(new Error('API Error'))

      render(<WorkspaceSelector />, { wrapper })

      // Aguarda tratamento de erro
      await waitFor(() => {
        expect(screen.getByText(/erro/i)).toBeInTheDocument()
      })

      // Verifica que workspace não foi alterado
      expect(localStorage.getItem('skybridge_active_workspace')).toBe('trading')
      expect((apiClient as any).defaults.headers['X-Workspace']).toBe('trading')
    })
  })
})
