/**
 * Testes para API endpoints.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { healthApi, discoverApi, webhooksApi, observabilityApi, agentsApi } from '../endpoints'
import apiClient from '../client'

// Mock do apiClient
vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('API Endpoints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('healthApi', () => {
    it('deve fazer GET para /health', async () => {
      vi.mocked(apiClient).get.mockResolvedValue({
        data: { status: 'healthy', version: '0.11.0' },
      })

      await healthApi.get()

      expect(apiClient.get).toHaveBeenCalledWith('/health')
    })

    it('deve retornar dados tipados', async () => {
      const mockHealth = {
        status: 'healthy',
        version: '0.11.0.dev',
        timestamp: '2025-01-27T20:00:00Z',
      }

      vi.mocked(apiClient).get.mockResolvedValue({ data: mockHealth })

      const result = await healthApi.get()

      expect(result.data).toEqual(mockHealth)
    })
  })

  describe('discoverApi', () => {
    it('deve listar todos os handlers', async () => {
      vi.mocked(apiClient).get.mockResolvedValue({
        data: {
          handlers: [
            { method: 'read_file', kind: 'query', description: 'Lê arquivo' },
          ],
        },
      })

      await discoverApi.list()

      expect(apiClient.get).toHaveBeenCalledWith('/discover')
    })

    it('deve obter handler específico', async () => {
      vi.mocked(apiClient).get.mockResolvedValue({
        data: {
          method: 'read_file',
          kind: 'query',
          description: 'Lê arquivo',
          module: 'kernel.queries.read_file',
        },
      })

      await discoverApi.getMethod('read_file')

      expect(apiClient.get).toHaveBeenCalledWith('/discover/read_file')
    })
  })

  describe('webhooksApi', () => {
    it('deve listar jobs', async () => {
      vi.mocked(apiClient).get.mockResolvedValue({
        data: {
          jobs: [
            { id: 'job-1', status: 'pending', created_at: '2025-01-27T20:00:00Z' },
          ],
        },
      })

      await webhooksApi.listJobs()

      expect(apiClient.get).toHaveBeenCalledWith('/webhooks/jobs')
    })

    it('deve obter métricas de jobs', async () => {
      vi.mocked(apiClient).get.mockResolvedValue({
        data: {
          ok: true,
          metrics: {
            queue_size: 20,
            processing: 10,
            completed: 60,
            failed: 10,
            total_enqueued: 100,
            total_completed: 60,
            total_failed: 10,
            success_rate: 85.5,
          },
        },
      })

      await agentsApi.getJobMetrics()

      expect(apiClient.get).toHaveBeenCalledWith('/webhooks/metrics')
    })
  })

  describe('observabilityApi', () => {
    it('deve listar arquivos de log', async () => {
      vi.mocked(apiClient).get.mockResolvedValue({
        data: {
          ok: true,
          files: [
            { name: 'skybridge-2025-01-27.log', size: 12345 },
          ],
        },
      })

      await observabilityApi.getLogFiles()

      expect(apiClient.get).toHaveBeenCalledWith('/logs/files')
    })

    it('deve fazer streaming de logs', async () => {
      vi.mocked(apiClient).get.mockResolvedValue({
        data: {
          logs: [
            {
              timestamp: '2025-01-27 20:00:00',
              level: 'INFO',
              logger: 'skybridge',
              message: 'Test message',
            },
          ],
        },
      })

      await observabilityApi.streamLogs('skybridge-2025-01-27.log')

      expect(apiClient.get).toHaveBeenCalledWith('/logs/file/skybridge-2025-01-27.log', {
        params: { page: 1, per_page: 50 },
      })
    })
  })
})
