import { Nav } from 'react-bootstrap'
import { Link } from 'react-router-dom'

interface NavItem {
  label: string
  path: string
}

interface ContextNavConfig {
  [key: string]: NavItem[]
}

// Configuração das navbars por contexto
const contextNavs: ContextNavConfig = {
  '/dashboard': [
    { label: 'Resumo', path: '/dashboard' },
    { label: 'Métricas', path: '/dashboard/metrics' },
    { label: 'Jobs', path: '/dashboard/jobs' },
  ],
  '/kanban': [
    { label: 'Quadro', path: '/kanban' },
    { label: 'Backlog', path: '/kanban/backlog' },
    { label: 'Em Progresso', path: '/kanban/in-progress' },
    { label: 'Concluídos', path: '/kanban/done' },
  ],
  '/wiki': [
    { label: 'Início', path: '/wiki' },
    { label: 'Tarefas', path: '/wiki/tarefas' },
    { label: 'Agentes', path: '/wiki/agentes' },
    { label: 'Procedimentos', path: '/wiki/procedimentos' },
  ],
  '/jobs': [
    { label: 'Todos', path: '/jobs' },
    { label: 'Pendentes', path: '/jobs?status=pending' },
    { label: 'Processando', path: '/jobs?status=processing' },
    { label: 'Concluídos', path: '/jobs?status=completed' },
    { label: 'Falhados', path: '/jobs?status=failed' },
  ],
  '/worktrees': [
    { label: 'Todas', path: '/worktrees' },
    { label: 'Ativas', path: '/worktrees?status=active' },
    { label: 'Snapshots', path: '/worktrees/snapshots' },
  ],
  '/logs': [
    { label: 'Ao Vivo', path: '/logs' },
    { label: 'Arquivos', path: '/logs/files' },
    { label: 'Filtros', path: '/logs/filters' },
  ],
}

interface ContextualNavbarProps {
  currentPath: string
}

export default function ContextualNavbar({ currentPath }: ContextualNavbarProps) {
  // Encontrar o contexto base (ex: /dashboard/summary -> /dashboard)
  const getContextBase = (path: string): string => {
    const segments = path.split('/').filter(Boolean)
    if (segments.length === 0) return '/dashboard'

    // Tentar encontrar correspondência exata
    if (contextNavs[`/${segments[0]}`]) {
      return `/${segments[0]}`
    }

    // Default para dashboard
    return '/dashboard'
  }

  const contextBase = getContextBase(currentPath)
  const navItems = contextNavs[contextBase] || []

  // Se não há itens de navegação, não renderizar nada
  if (navItems.length === 0) {
    return null
  }

  return (
    <Nav className="mb-4" variant="pills">
      {navItems.map((item) => {
        const isActive = currentPath === item.path || currentPath.startsWith(item.path + '?')

        return (
          <Nav.Link
            key={item.path}
            as={Link}
            to={item.path}
            active={isActive}
          >
            {item.label}
          </Nav.Link>
        )
      })}
    </Nav>
  )
}
