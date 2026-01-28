/**
 * Testes para Dashboard page.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
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
    it('deve mostrar heading "Dashboard"', () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      expect(screen.getByRole('heading', { name: /dashboard/i, level: 1 })).toBeInTheDocument()
    })

    it('deve mostrar spinner durante carregamento', () => {
      vi.mocked(apiClient.default).get.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<Dashboard />, { wrapper })

      expect(screen.getByRole('status')).toBeInTheDocument()
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

    it('deve mostrar card de Worktrees', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Worktrees/i)).toBeInTheDocument()
      })
    })

    it('deve mostrar card de Logs', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Logs/i)).toBeInTheDocument()
        expect(screen.getByText(/Sistema/i)).toBeInTheDocument()
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

  describe('navegação', () => {
    it('deve ter link para Skybridge WebUI no header', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /Skybridge WebUI/i })
        expect(link).toHaveAttribute('href', '/web')
      })
    })
  })

  describe('refetch automático', () => {
    it('deve recarregar dados a cada 5 segundos', async () => {
      vi.useFakeTimers()

      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0', timestamp: '2025-01-27T20:00:00Z' },
      })

      render(<Dashboard />, { wrapper })

      await waitFor(() => {
        expect(apiClient.default.get).toHaveBeenCalled()
      })

      const initialCallCount = vi.mocked(apiClient.default).get.mock.calls.length

      vi.advanceTimersByTime(5000)

      await waitFor(() => {
        expect(vi.mocked(apiClient.default).get.mock.calls.length).toBeGreaterThan(initialCallCount)
      })

      vi.useRealTimers()
    })
  })
})
