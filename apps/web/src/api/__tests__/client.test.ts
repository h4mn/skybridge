/**
 * Testes para API client.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import apiClient, { setAuthToken, clearAuthToken } from '../client'

// Mock do axios
vi.mock('axios')

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    clearAuthToken()
  })

  describe('configuração básica', () => {
    it('deve ter baseURL configurada para /api', () => {
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: '/api',
        })
      )
    })

    it('deve ter timeout configurado', () => {
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          timeout: expect.any(Number),
        })
      )
    })
  })

  describe('auth token', () => {
    it('deve definir auth token', () => {
      const mockAxiosInstance = {
        interceptors: {
          request: {
            use: vi.fn(),
          },
        },
      }

      vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any)

      setAuthToken('test-token')

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled()
    })

    it('deve limpar auth token', () => {
      const mockAxiosInstance = {
        interceptors: {
          request: {
            use: vi.fn(),
          },
        },
      }

      vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any)

      setAuthToken('test-token')
      clearAuthToken()

      // Verifica se o interceptor foi chamado duas vezes (set + clear)
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledTimes(2)
    })
  })

  describe('métodos HTTP', () => {
    let mockInstance: any

    beforeEach(() => {
      mockInstance = {
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        patch: vi.fn(),
        interceptors: {
          request: {
            use: vi.fn(),
          },
        },
      }
      vi.mocked(axios.create).mockReturnValue(mockInstance)
    })

    it('deve fazer requisição GET', async () => {
      mockInstance.get.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.get('/test')

      expect(mockInstance.get).toHaveBeenCalledWith('/test')
      expect(result.data).toEqual({ success: true })
    })

    it('deve fazer requisição POST', async () => {
      mockInstance.post.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.post('/test', { data: 'test' })

      expect(mockInstance.post).toHaveBeenCalledWith('/test', { data: 'test' })
      expect(result.data).toEqual({ success: true })
    })

    it('deve fazer requisição PUT', async () => {
      mockInstance.put.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.put('/test', { data: 'test' })

      expect(mockInstance.put).toHaveBeenCalledWith('/test', { data: 'test' })
      expect(result.data).toEqual({ success: true })
    })

    it('deve fazer requisição DELETE', async () => {
      mockInstance.delete.mockResolvedValue({ data: { success: true } })

      const result = await apiClient.delete('/test')

      expect(mockInstance.delete).toHaveBeenCalledWith('/test')
      expect(result.data).toEqual({ success: true })
    })
  })

  describe('tratamento de erros', () => {
    let mockInstance: any

    beforeEach(() => {
      mockInstance = {
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: {
            use: vi.fn(),
          },
        },
      }
      vi.mocked(axios.create).mockReturnValue(mockInstance)
    })

    it('deve propagar erros da API', async () => {
      const error = new Error('Network error')
      mockInstance.get.mockRejectedValue(error)

      await expect(apiClient.get('/test')).rejects.toThrow('Network error')
    })

    it('deve incluir dados do erro em requisições falhas', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found' },
        },
      }
      mockInstance.get.mockRejectedValue(error)

      try {
        await apiClient.get('/test')
      } catch (e: any) {
        expect(e.response.status).toBe(404)
        expect(e.response.data).toEqual({ detail: 'Not found' })
      }
    })
  })
})
