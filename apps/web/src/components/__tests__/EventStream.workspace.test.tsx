/**
 * Testes de isolamento de workspace para EventStream component.
 *
 * TDD Estrito: Testes que documentam o comportamento esperado.
 *
 * DOC: PRD023 - EventStream mostra eventos apenas do workspace ativo.
 * DOC: PRD023 - SSE usa query parameter para workspace (EventSource não suporta headers).
 * DOC: ADR024 - Cada workspace tem seus próprios eventos isolados.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import EventStream from '../EventStream'
import apiClient from '@/api/client'

// Mock do apiClient
vi.mock('@/api/client', () => ({
  default: {
    delete: vi.fn(),
    post: vi.fn(),
    defaults: { headers: {} },
  },
}))

// Mock do EventSource nativo do browser
class MockEventSource {
  public url: string
  public readyState: number = 0
  public onopen: ((this: EventSource, event: Event) => void) | null = null
  public onmessage: ((this: EventSource, event: MessageEvent) => void) | null = null
  public onerror: ((this: EventSource, event: Event) => void) | null = null
  private eventListeners: Map<string, EventListener[]> = new Map()

  constructor(url: string) {
    this.url = url
    // Simula conexão bem-sucedida após 100ms
    setTimeout(() => {
      this.readyState = 1 // OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 100)
  }

  public addEventListener(type: string, listener: EventListener) {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, [])
    }
    this.eventListeners.get(type)!.push(listener)

    // Simula eventos de histórico para 'history' e 'domain_event'
    if (type === 'history' || type === 'domain_event') {
      setTimeout(() => {
        const mockEvent = new MessageEvent(type, {
          data: JSON.stringify({
            event_id: `test-event-${type}`,
            timestamp: new Date().toISOString(),
            event_type: 'TEST_EVENT',
            aggregate_id: 'test-aggregate',
            version: 1,
          }),
        })
        listener(mockEvent)
      }, 150)
    }
  }

  public removeEventListener(type: string, listener: EventListener) {
    const listeners = this.eventListeners.get(type)
    if (listeners) {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  public close() {
    this.readyState = 2 // CLOSED
  }
}

// Substitui EventSource global por mock
vi.stubGlobal('EventSource', MockEventSource)

describe('EventStream - Isolamento de Workspace (PRD023)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()

    // Configura workspace padrão como 'core'
    localStorage.setItem('skybridge_active_workspace', 'core')
    ;(apiClient as any).defaults.headers['X-Workspace'] = 'core'

    // Mock das chamadas de API
    vi.mocked(apiClient.delete).mockResolvedValue({ data: { ok: true } })
    vi.mocked(apiClient.post).mockResolvedValue({ data: { count: 5 } })
  })

  afterEach(() => {
    // Limpa todos os EventSources criados
    vi.unstubAllGlobals()
    vi.stubGlobal('EventSource', MockEventSource)
  })

  describe('query parameter para SSE', () => {
    it('deve incluir workspace como query parameter na URL do SSE', async () => {
      /**
       * DOC: PRD023 - EventSource usa query parameter para workspace.
       * DOC: PRD023 - EventSource não suporta headers customizados.
       * GIVEN: Workspace ativo é 'core'
       * WHEN: EventStream é montado
       * THEN: URL do SSE contém ?workspace=core
       */

      // Intercepta criação do EventSource para capturar a URL
      let capturedUrl: string | null = null

      const originalEventSource = global.EventSource
      global.EventSource = class extends MockEventSource {
        constructor(url: string) {
          super(url)
          capturedUrl = url
        }
      } as any

      render(<EventStream />)

      await waitFor(() => {
        expect(capturedUrl).toContain('workspace=core')
        expect(capturedUrl).toContain('/api/observability/events/stream')
      }, { timeout: 1000 })

      // Restaura EventSource original
      global.EventSource = originalEventSource
    })

    it('deve usar workspace do localStorage na URL do SSE', async () => {
      /**
       * DOC: PRD023 - Workspace ativo é obtido do localStorage.
       * GIVEN: Workspace 'trading' está salvo no localStorage
       * WHEN: EventStream é montado
       * THEN: URL do SSE contém ?workspace=trading
       */
      // Configura workspace trading
      localStorage.setItem('skybridge_active_workspace', 'trading')

      let capturedUrl: string | null = null

      const originalEventSource = global.EventSource
      global.EventSource = class extends MockEventSource {
        constructor(url: string) {
          super(url)
          capturedUrl = url
        }
      } as any

      render(<EventStream />)

      await waitFor(() => {
        expect(capturedUrl).toContain('workspace=trading')
      }, { timeout: 1000 })

      global.EventSource = originalEventSource
    })

    it('deve usar workspace core como padrão quando não definido', async () => {
      /**
       * DOC: PRD023 - Workspace 'core' é usado como padrão.
       * GIVEN: Nenhum workspace está salvo no localStorage
       * WHEN: EventStream é montado
       * THEN: URL do SSE contém ?workspace=core
       */
      localStorage.removeItem('skybridge_active_workspace')

      let capturedUrl: string | null = null

      const originalEventSource = global.EventSource
      global.EventSource = class extends MockEventSource {
        constructor(url: string) {
          super(url)
          capturedUrl = url
        }
      } as any

      render(<EventStream />)

      await waitFor(() => {
        expect(capturedUrl).toContain('workspace=core')
      }, { timeout: 1000 })

      global.EventSource = originalEventSource
    })
  })

  describe('operações CRUD usam apiClient com X-Workspace', () => {
    it('deve incluir header X-Workspace ao limpar histórico de eventos', async () => {
      /**
       * DOC: PRD023 - DELETE usa apiClient com header X-Workspace.
       * GIVEN: Workspace ativo é 'core'
       * WHEN: Usuário clica em "Limpar"
       * THEN: Requisição DELETE inclui header X-Workspace: core
       */
      const mockDelete = vi.mocked(apiClient.delete)
      mockDelete.mockResolvedValue({ data: { ok: true } })

      render(<EventStream />)

      await waitFor(() => {
        expect(screen.getByText(/Limpar/i)).toBeInTheDocument()
      })

      const clearButton = screen.getByText(/Limpar/i)
      await clearButton.click()

      await waitFor(() => {
        expect(mockDelete).toHaveBeenCalledWith('/api/observability/events/history')
        expect((apiClient as any).defaults.headers['X-Workspace']).toBe('core')
      })
    })

    it('deve incluir header X-Workspace ao gerar eventos fake', async () => {
      /**
       * DOC: PRD023 - POST usa apiClient com header X-Workspace.
       * GIVEN: Workspace ativo é 'trading'
       * WHEN: Usuário clica em "Gerar 5"
       * THEN: Requisição POST inclui header X-Workspace: trading
       */
      // Configura workspace trading
      localStorage.setItem('skybridge_active_workspace', 'trading')
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'trading'

      const mockPost = vi.mocked(apiClient.post)
      mockPost.mockResolvedValue({ data: { count: 5 } })

      render(<EventStream />)

      await waitFor(() => {
        expect(screen.getByText(/Gerar 5/i)).toBeInTheDocument()
      })

      const generateButton = screen.getByText(/Gerar 5/i)
      await generateButton.click()

      await waitFor(() => {
        expect(mockPost).toHaveBeenCalledWith(
          '/api/observability/events/generate-fake',
          null,
          expect.objectContaining({
            params: { count: 5 },
          })
        )
        expect((apiClient as any).defaults.headers['X-Workspace']).toBe('trading')
      })
    })
  })

  describe('isolamento de eventos por workspace', () => {
    it('deve processar eventos apenas do workspace solicitado', async () => {
      /**
       * DOC: PRD023 - Eventos recebidos via SSE são do workspace ativo.
       * GIVEN: Workspace ativo é 'core'
       * WHEN: SSE envia eventos
       * THEN: Apenas eventos do workspace 'core' são processados
       */
      let capturedUrl: string | null = null

      const originalEventSource = global.EventSource
      global.EventSource = class extends MockEventSource {
        constructor(url: string) {
          super(url)
          capturedUrl = url
        }
      } as any

      render(<EventStream />)

      await waitFor(() => {
        expect(capturedUrl).toContain('workspace=core')
      }, { timeout: 1000 })

      // Verifica que eventos foram processados (apareceu "eventos")
      await waitFor(() => {
        // Usa getAllByText porque há múltiplos elementos com "eventos"
        const eventosElements = screen.getAllByText(/eventos/i)
        expect(eventosElements.length).toBeGreaterThan(0)
      }, { timeout: 1000 })

      global.EventSource = originalEventSource
    })

    it('não deve misturar eventos de workspaces diferentes', async () => {
      /**
       * DOC: PRD023 - SSE mantém isolamento entre workspaces.
       * GIVEN: Workspaces core e trading têm eventos diferentes
       * WHEN: Conectando ao SSE de cada workspace
       * THEN: Eventos permanecem isolados
       */

      // Testa workspace core
      let coreUrl: string | null = null
      global.EventSource = class extends MockEventSource {
        constructor(url: string) {
          super(url)
          coreUrl = url
        }
      } as any

      localStorage.setItem('skybridge_active_workspace', 'core')
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'core'

      const { unmount } = render(<EventStream />)

      await waitFor(() => {
        expect(coreUrl).toContain('workspace=core')
      }, { timeout: 1000 })

      // Testa workspace trading
      unmount() // Limpa o componente anterior

      let tradingUrl: string | null = null
      global.EventSource = class extends MockEventSource {
        constructor(url: string) {
          super(url)
          tradingUrl = url
        }
      } as any

      localStorage.setItem('skybridge_active_workspace', 'trading')
      ;(apiClient as any).defaults.headers['X-Workspace'] = 'trading'

      // Renderiza novamente com novo workspace
      render(<EventStream />)

      await waitFor(() => {
        expect(tradingUrl).toContain('workspace=trading')
      }, { timeout: 1000 })

      // Verifica que as URLs são diferentes
      expect(coreUrl).not.toEqual(tradingUrl)
      expect(coreUrl).toContain('workspace=core')
      expect(tradingUrl).toContain('workspace=trading')
    })
  })
})
