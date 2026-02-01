/**
 * Testes para LogStream component.
 *
 * TDD Estrito: Testes que documentam o comportamento esperado.
 *
 * DOC: LogStream mostra logs do sistema em tempo real.
 * DOC: LogStream faz polling a cada 2 segundos.
 * DOC: LogStream pode ser pausado via prop.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import LogStream from '../LogStream'
import * as endpoints from '../../api/endpoints'

// Mock do observabilityApi (endpoints)
vi.mock('../../api/endpoints', () => ({
  observabilityApi: {
    getLogFiles: vi.fn(),
    streamLogs: vi.fn(),
  },
}))

const mockGetLogFiles = endpoints.observabilityApi.getLogFiles as any
const mockStreamLogs = endpoints.observabilityApi.streamLogs as any

describe('LogStream', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('renderização inicial', () => {
    it('deve renderizar sem erro', () => {
      /**
       * DOC: Componente renderiza sem erro.
       */
      mockGetLogFiles.mockResolvedValue({
        data: { ok: true, files: [{ name: 'test.log' }] },
      })

      render(<LogStream />)

      expect(screen.getByText(/Logs ao Vivo/i)).toBeInTheDocument()
    })

    it('deve mostrar estado "Conectando..." inicialmente', () => {
      /**
       * DOC: Estado inicial mostra badge "Conectando...".
       */
      mockGetLogFiles.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<LogStream />)

      expect(screen.getByText(/Conectando\.\.\./i)).toBeInTheDocument()
    })

    it('deve mostrar erro quando falha ao buscar arquivos', async () => {
      /**
       * DOC: Erro ao carregar logs é tratado graciosamente.
       */
      mockGetLogFiles.mockRejectedValue(new Error('Network error'))

      render(<LogStream />)

      await waitFor(() => {
        expect(screen.getByText(/Erro ao carregar logs/i)).toBeInTheDocument()
      })
    })
  })

  describe('busca de arquivos de log', () => {
    it('deve buscar arquivos de log ao montar', async () => {
      /**
       * DOC: Componente busca lista de arquivos ao montar.
       */
      mockGetLogFiles.mockResolvedValue({
        data: { ok: true, files: [{ name: 'skybridge-2025-01-27.log' }] },
      })

      render(<LogStream />)

      await waitFor(() => {
        expect(mockGetLogFiles).toHaveBeenCalledWith()
      })
    })
  })

  describe('exibição de logs', () => {
    it('deve mostrar badge "Ao vivo" quando conectado', async () => {
      /**
       * DOC: Badge "Ao vivo" aparece quando logs estão sendo recebidos.
       */
      mockGetLogFiles.mockResolvedValue({
        data: { ok: true, files: [{ name: 'test.log' }] },
      })
      mockStreamLogs.mockResolvedValue({
        data: {
          ok: true,
          entries: [
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

      render(<LogStream />)

      await waitFor(() => {
        expect(screen.getByText(/Ao vivo/i)).toBeInTheDocument()
      })
    })

    it('deve mostrar mensagem de aguardando quando não há logs', async () => {
      /**
       * DOC: Estado vazio mostra "Aguardando logs...".
       */
      mockGetLogFiles.mockResolvedValue({
        data: { ok: true, files: [{ name: 'test.log' }] },
      })
      mockStreamLogs.mockResolvedValue({
        data: { ok: true, entries: [] },
      })

      render(<LogStream />)

      await waitFor(() => {
        expect(screen.getByText(/Aguardando logs\.\.\./i)).toBeInTheDocument()
      })
    })
  })

  describe('prop paused', () => {
    it('deve aceitar prop paused sem erro', () => {
      /**
       * DOC: Prop paused controla se o polling está ativo.
       */
      mockGetLogFiles.mockResolvedValue({
        data: { ok: true, files: [{ name: 'test.log' }] },
      })

      render(<LogStream paused={true} />)

      expect(screen.getByText(/Logs ao Vivo/i)).toBeInTheDocument()
    })
  })
})
