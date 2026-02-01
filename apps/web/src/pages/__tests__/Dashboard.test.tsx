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
vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
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
})
