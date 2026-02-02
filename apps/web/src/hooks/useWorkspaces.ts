/**
 * useWorkspaces Hook - Gerencia workspaces e workspace ativo.
 *
 * DOC: ADR024 - Hook lista workspaces e gerencia workspace ativo.
 * DOC: PB013 - Workspace ativo define header X-Workspace global.
 */
import { useState, useEffect } from 'react'
import { workspacesApi, Workspace } from '@/api/endpoints'
import apiClient from '@/api/client'

export interface UseWorkspacesReturn {
  workspaces: Workspace[]
  activeWorkspace: string
  loading: boolean
  error: Error | null
  setActiveWorkspace: (id: string) => void
  isActive: (id: string) => boolean
}

const DEFAULT_WORKSPACE = 'core'
const WORKSPACE_STORAGE_KEY = 'skybridge_active_workspace'

/**
 * Hook para gerenciar workspaces.
 *
 * Carrega a lista de workspaces da API e gerencia o workspace ativo.
 * O workspace ativo é armazenado no localStorage e define o header
 * X-Workspace global para todas as requisições.
 */
export function useWorkspaces(): UseWorkspacesReturn {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [activeWorkspace, setActiveWorkspaceState] = useState<string>(DEFAULT_WORKSPACE)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // Carregar workspaces ao montar
  useEffect(() => {
    async function loadWorkspaces() {
      try {
        setLoading(true)
        setError(null)

        const response = await workspacesApi.list()
        setWorkspaces(response.data.workspaces)

        // Recuperar workspace ativo do localStorage
        const stored = localStorage.getItem(WORKSPACE_STORAGE_KEY)
        if (stored) {
          setActiveWorkspaceState(stored)
          // Definir header global
          apiClient.defaults.headers['X-Workspace'] = stored
        } else {
          // Usar core como padrão
          setActiveWorkspaceState(DEFAULT_WORKSPACE)
          apiClient.defaults.headers['X-Workspace'] = DEFAULT_WORKSPACE
        }
      } catch (err) {
        setError(err as Error)
        setWorkspaces([])
      } finally {
        setLoading(false)
      }
    }

    loadWorkspaces()
  }, [])

  /**
   * Define o workspace ativo.
   *
   * Atualiza o localStorage e define o header X-Workspace global.
   */
  const setActiveWorkspace = (id: string) => {
    setActiveWorkspaceState(id)
    localStorage.setItem(WORKSPACE_STORAGE_KEY, id)
    apiClient.defaults.headers['X-Workspace'] = id
  }

  /**
   * Verifica se um workspace está ativo.
   */
  const isActive = (id: string): boolean => {
    return activeWorkspace === id
  }

  return {
    workspaces,
    activeWorkspace,
    loading,
    error,
    setActiveWorkspace,
    isActive,
  }
}
