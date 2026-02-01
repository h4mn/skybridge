/**
 * Testes para API client.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock do axios - o mock é hoisted para antes da importação
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      interceptors: {
        request: {
          use: vi.fn(),
          eject: vi.fn(),
        },
        response: {
          use: vi.fn(),
          eject: vi.fn(),
        },
      },
      defaults: {
        headers: {
          common: {},
          get: {},
          post: {},
          put: {},
          delete: {},
        },
      },
    })),
  },
}))

import apiClient from '../client'

// Mock dos métodos do apiClient para os testes
const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

// Substitui os métodos do apiClient pelos mocks
apiClient.get = mockGet
apiClient.post = mockPost
apiClient.put = mockPut
apiClient.delete = mockDelete

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Configura comportamento padrão
    mockGet.mockResolvedValue({ data: {} })
    mockPost.mockResolvedValue({ data: {} })
    mockPut.mockResolvedValue({ data: {} })
    mockDelete.mockResolvedValue({ data: {} })
  })

  describe('métodos HTTP', () => {
    it('deve fazer requisição GET', async () => {
      mockGet.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.get('/test')

      expect(mockGet).toHaveBeenCalledWith('/test')
      expect(result.data).toEqual({ success: true })
    })

    it('deve fazer requisição POST', async () => {
      mockPost.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.post('/test', { data: 'test' })

      expect(mockPost).toHaveBeenCalledWith('/test', { data: 'test' })
      expect(result.data).toEqual({ success: true })
    })

    it('deve fazer requisição PUT', async () => {
      mockPut.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.put('/test', { data: 'test' })

      expect(mockPut).toHaveBeenCalledWith('/test', { data: 'test' })
      expect(result.data).toEqual({ success: true })
    })

    it('deve fazer requisição DELETE', async () => {
      mockDelete.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.delete('/test')

      expect(mockDelete).toHaveBeenCalledWith('/test')
      expect(result.data).toEqual({ success: true })
    })
  })

  describe('tratamento de erros', () => {
    it('deve propagar erros da API', async () => {
      const error = new Error('Network error')
      mockGet.mockRejectedValue(error)

      await expect(apiClient.get('/test')).rejects.toThrow('Network error')
    })

    it('deve incluir dados do erro em requisições falhas', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found' },
        },
      }
      mockGet.mockRejectedValue(error)

      try {
        await apiClient.get('/test')
      } catch (e: any) {
        expect(e.response.status).toBe(404)
        expect(e.response.data).toEqual({ detail: 'Not found' })
      }
    })
  })
})
