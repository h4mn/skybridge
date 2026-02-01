/**
 * WorkspaceSelector Component - Seletor de Workspace.
 *
 * DOC: ADR024 - Componente mostra workspaces disponíveis e permite alternar.
 * DOC: PB013 - Workspace ativo tem indicador visual.
 *
 * Este componente usa o hook useWorkspaces para gerenciar a lista de
 * workspaces e o workspace ativo, definindo o header X-Workspace global.
 */
import { useState } from 'react'
import { Dropdown, DropdownButton } from 'react-bootstrap'
import { useWorkspaces } from '@/hooks/useWorkspaces'

export default function WorkspaceSelector() {
  const { workspaces, activeWorkspace, loading, error, setActiveWorkspace, isActive } =
    useWorkspaces()
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const handleSelect = (workspaceId: string) => {
    setActiveWorkspace(workspaceId)
    setDropdownOpen(false)
  }

  return (
    <div className="workspace-selector ms-3" data-testid="workspace-selector">
      {loading ? (
        // Indicador de carregamento
        <span role="status" className="text-muted">
          Carregando workspaces...
        </span>
      ) : error ? (
        // Estado de erro
        <span className="text-danger">Erro ao carregar workspaces</span>
      ) : (
        // Dropdown de workspaces
        <Dropdown show={dropdownOpen} onToggle={(isOpen) => setDropdownOpen(isOpen)}>
          <DropdownButton
            variant={isActive(activeWorkspace) ? 'primary' : 'outline-primary'}
            size="sm"
            id="workspace-dropdown"
            title={`Workspace atual: ${activeWorkspace}`}
          >
            <span data-testid="active-workspace-id">{activeWorkspace}</span>
          </DropdownButton>

          <Dropdown.Menu>
            {workspaces.map((workspace) => (
              <Dropdown.Item
                key={workspace.id}
                active={isActive(workspace.id)}
                onClick={() => handleSelect(workspace.id)}
                data-testid={`workspace-item-${workspace.id}`}
              >
                {workspace.id} - {workspace.name}
              </Dropdown.Item>
            ))}
          </Dropdown.Menu>
        </Dropdown>
      )}
    </div>
  )
}
