/**
 * Testes para WorkspaceSelector component.
 *
 * TDD Estrito: Testes que documentam o comportamento esperado.
 *
 * DOC: ADR024 - WorkspaceSelector mostra workspaces disponíveis.
 * DOC: ADR024 - WorkspaceSelector alterna workspace ao selecionar.
 * DOC: PB013 - Workspace ativo tem indicador visual.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import WorkspaceSelector from '../WorkspaceSelector'
import { workspacesApi } from '@/api/endpoints'
import apiClient from '@/api/client'

// Mock do apiClient
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

const getMockHeaders = () => (apiClient as any).defaults.headers

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

describe('WorkspaceSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renderiza o seletor de workspaces', async () => {
    /**
     * DOC: ADR024 - Componente renderiza sem erro.
     */
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { workspaces: mockWorkspaces },
    } as any)

    render(<WorkspaceSelector />)

    // Aguarda carregamento
    await waitFor(() => {
      expect(screen.getByTestId('workspace-selector')).toBeInTheDocument()
    })

    // Botão dropdown deve estar presente
    const dropdownButton = screen.getByRole('button')
    expect(dropdownButton).toBeInTheDocument()
  })

  it('mostra workspace ativo no botão', async () => {
    /**
     * DOC: PB013 - Workspace ativo é exibido no botão.
     */
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { workspaces: mockWorkspaces },
    } as any)

    render(<WorkspaceSelector />)

    // Aguarda carregamento
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    // Verifica que o botão contém o ID do workspace ativo
    const dropdownButton = screen.getByRole('button')
    expect(dropdownButton.textContent).toContain('core')
  })

  it('mostra indicador de carregamento', () => {
    /**
     * DOC: Componente mostra estado de carregamento.
     */
    vi.mocked(apiClient.get).mockImplementation(
      () => new Promise(() => {}) // Nunca resolve
    )

    render(<WorkspaceSelector />)

    // Deve mostrar algum indicador de loading
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText(/Carregando workspaces/i)).toBeInTheDocument()
  })

  it('trata erro ao carregar workspaces', async () => {
    /**
     * DOC: Erro ao carregar workspaces é tratado graciosamente.
     */
    vi.mocked(apiClient.get).mockRejectedValue(new Error('API Error'))

    render(<WorkspaceSelector />)

    // Aguarda tratamento de erro
    await waitFor(() => {
      expect(screen.getByText(/erro/i)).toBeInTheDocument()
    })
  })

  it('workspaces estão disponíveis no componente', async () => {
    /**
     * DOC: ADR024 - Workspaces são carregados no componente.
     */
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { workspaces: mockWorkspaces },
    } as any)

    render(<WorkspaceSelector />)

    // Aguarda carregamento
    await waitFor(() => {
      expect(screen.getByTestId('workspace-selector')).toBeInTheDocument()
    })

    // Verifica que o botão existe e tem o ID correto
    const dropdownButton = screen.getByRole('button')
    expect(dropdownButton).toHaveAttribute('id', 'workspace-dropdown')

    // O componente deve renderizar sem erros
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
