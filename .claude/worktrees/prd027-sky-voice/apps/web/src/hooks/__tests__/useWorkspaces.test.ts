/**
 * Testes para useWorkspaces hook.
 *
 * TDD Estrito: Testes que documentam o comportamento esperado.
 *
 * DOC: ADR024 - useWorkspaces lista workspaces disponíveis.
 * DOC: ADR024 - useWorkspaces gerencia workspace ativo com X-Workspace.
 */
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useWorkspaces } from '../useWorkspaces'
import { workspacesApi } from '@/api/endpoints'
import apiClient from '@/api/client'

// Mock do apiClient - mock inline para evitar problemas de hoisting
vi.mock('@/api/client', () => {
  const mockHeaders: Record<string, string> = {}
  return {
    default: {
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
      defaults: { headers: mockHeaders },
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    },
  }
})

// Acessar os headers mockados após o mock ser aplicado
const getMockHeaders = () => (apiClient as any).defaults.headers

describe('useWorkspaces', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Limpar localStorage
    localStorage.clear()
  })

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

  it('lista workspaces disponíveis', async () => {
    /**
     * DOC: ADR024 - Hook carrega lista de workspaces da API.
     */
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { workspaces: mockWorkspaces },
    } as any)

    const { result } = renderHook(() => useWorkspaces())

    // Estado inicial: carregando
    expect(result.current.loading).toBe(true)
    expect(result.current.workspaces).toEqual([])

    // Após carregar
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
      expect(result.current.workspaces).toEqual(mockWorkspaces)
    })
  })

  it('usa workspace core como padrão', async () => {
    /**
     * DOC: ADR024 - Sem workspace ativo, usa 'core' como padrão.
     */
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { workspaces: mockWorkspaces },
    } as any)

    const { result } = renderHook(() => useWorkspaces())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.activeWorkspace).toBe('core')
  })

  it('define workspace ativo ao selecionar', async () => {
    /**
     * DOC: ADR024 - setActiveWorkspace define header X-Workspace.
     */
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { workspaces: mockWorkspaces },
    } as any)

    const { result } = renderHook(() => useWorkspaces())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Selecionar trading
    await act(async () => {
      result.current.setActiveWorkspace('trading')
    })

    expect(result.current.activeWorkspace).toBe('trading')
    expect(getMockHeaders()['X-Workspace']).toBe('trading')
  })

  it('mostra workspace ativo com destaque', async () => {
    /**
     * DOC: PB013 - Workspace ativo tem indicador visual.
     */
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { workspaces: mockWorkspaces },
    } as any)

    const { result } = renderHook(() => useWorkspaces())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Core está ativo por padrão
    expect(result.current.isActive('core')).toBe(true)
    expect(result.current.isActive('trading')).toBe(false)

    // Após mudar para trading
    await act(async () => {
      result.current.setActiveWorkspace('trading')
    })

    expect(result.current.isActive('core')).toBe(false)
    expect(result.current.isActive('trading')).toBe(true)
  })

  it('trata erro ao carregar workspaces', async () => {
    /**
     * DOC: Erro ao carregar workspaces é tratado graciosamente.
     */
    vi.mocked(apiClient.get).mockRejectedValue(new Error('API Error'))

    const { result } = renderHook(() => useWorkspaces())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBeTruthy()
    expect(result.current.workspaces).toEqual([])
  })
})
