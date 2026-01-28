/**
 * Testes para LogStream component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LogStream from '../LogStream'
import * as apiClient from '../../api/client'

// Mock do apiClient
vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
  },
}))

describe('LogStream', () => {
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

  afterEach(() => {
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('renderização inicial', () => {
    it('deve mostrar spinner durante carregamento', () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { ok: true, files: [{ name: 'test.log' }] },
      })

      render(<LogStream />, { wrapper })

      expect(screen.getByText(/Sistema/i)).toBeInTheDocument()
      expect(screen.getByRole('status')).toHaveClass('text-muted')
    })

    it('deve mostrar estado desconectado inicialmente', () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { ok: true, files: [{ name: 'test.log' }] },
      })

      render(<LogStream />, { wrapper })

      expect(screen.getByText(/Conectando/i)).toBeInTheDocument()
    })
  })

  describe('busca de arquivos de log', () => {
    it('deve buscar arquivos de log ao montar', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { ok: true, files: [{ name: 'skybridge-2025-01-27.log' }] },
      })

      render(<LogStream />, { wrapper })

      await waitFor(() => {
        expect(apiClient.default.get).toHaveBeenCalledWith('/logs/files')
      })
    })

    it('deve mostrar erro quando falha ao buscar arquivos', async () => {
      vi.mocked(apiClient.default).get.mockRejectedValue(new Error('Network error'))

      render(<LogStream />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Erro ao carregar logs/i)).toBeInTheDocument()
      })
    })
  })

  describe('exibição de logs', () => {
    it('deve exibir logs quando conectado', async () => {
      vi.mocked(apiClient.default).get
        .mockResolvedValueOnce({
          data: { ok: true, files: [{ name: 'test.log' }] },
        })
        .mockResolvedValue({
          data: {
            logs: [
              {
                timestamp: '2025-01-27 20:00:00',
                level: 'INFO',
                logger: 'skybridge',
                message: 'Test message',
                message_html: '<span>Test message</span>',
              },
            ],
          },
        })

      render(<LogStream />, { wrapper })

      await waitFor(() => {
        expect(screen.getByText(/Conectado/i)).toBeInTheDocument()
      })
    })

    it('deve mostrar badge de nível de log correto', async () => {
      vi.mocked(apiClient.default).get
        .mockResolvedValueOnce({
          data: { ok: true, files: [{ name: 'test.log' }] },
        })
        .mockResolvedValue({
          data: {
            logs: [
              {
                timestamp: '2025-01-27 20:00:00',
                level: 'ERROR',
                logger: 'skybridge',
                message: 'Error message',
                message_html: '<span>Error message</span>',
              },
            ],
          },
        })

      render(<LogStream />, { wrapper })

      await waitFor(() => {
        const errorBadge = screen.getByText(/ERR/i)
        expect(errorBadge).toHaveClass('badge')
      })
    })
  })

  describe('polling', () => {
    it('deve iniciar polling após conectar', async () => {
      vi.useFakeTimers()

      vi.mocked(apiClient.default).get
        .mockResolvedValueOnce({
          data: { ok: true, files: [{ name: 'test.log' }] },
        })
        .mockResolvedValue({
          data: { logs: [] },
        })

      render(<LogStream />, { wrapper })

      await waitFor(() => {
        expect(apiClient.default.get).toHaveBeenCalled()
      })

      vi.advanceTimersByTime(2000)

      await waitFor(() => {
        expect(apiClient.default.get).toHaveBeenCalledTimes(2) // files + first poll
      })

      vi.useRealTimers()
    })
  })

  describe('toggle de stream', () => {
    it('deve permitir pausar/retomar o stream', async () => {
      vi.mocked(apiClient.default).get.mockResolvedValue({
        data: { ok: true, files: [{ name: 'test.log' }] },
      })

      render(<LogStream />, { wrapper })

      await waitFor(() => {
        const toggleButton = screen.getByRole('button', { name: /Pausar/i })
        expect(toggleButton).toBeInTheDocument()
      })
    })
  })
})
