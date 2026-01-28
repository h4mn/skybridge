import { Navbar, Container } from 'react-bootstrap'
import { useLocation } from 'react-router-dom'

/**
 * Header/Navbar principal do Skybridge WebUI.
 * Mostra o título dinâmico baseado no contexto ativo.
 */
export default function Header() {
  const location = useLocation()

  // Mapear caminho para nome do contexto
  const getContextName = (path: string): string => {
    const contextMap: Record<string, string> = {
      '/dashboard': 'Dashboard',
      '/dashboard/': 'Dashboard',
      '/kanban': 'Kanban',
      '/wiki': 'Wiki',
      '/jobs': 'Jobs',
      '/worktrees': 'Worktrees',
      '/logs': 'Logs',
    }

    // Encontrar correspondência exata ou por prefixo
    const exactMatch = contextMap[path]
    if (exactMatch) return exactMatch

    // Tentar correspondência por prefixo
    for (const [key, value] of Object.entries(contextMap)) {
      if (path.startsWith(key) && key !== '/') {
        return value
      }
    }

    return 'WebUI'
  }

  const contextName = getContextName(location.pathname)

  return (
    <Navbar bg="dark" variant="dark">
      <Container fluid>
        <Navbar.Brand>
          <strong>Skybridge</strong> {contextName}
        </Navbar.Brand>
      </Container>
    </Navbar>
  )
}
