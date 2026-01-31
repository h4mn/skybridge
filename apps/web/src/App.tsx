import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import Sidebar, { SidebarSection } from './components/Sidebar'
import Header from './components/Header'
import ContextualNavbar from './components/ContextualNavbar'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import Worktrees from './pages/Worktrees'
import Logs from './pages/Logs'
import Events from './pages/Events'
import Agents from './pages/Agents'
import Kanban from './pages/Kanban'
import Wiki from './pages/Wiki'
import axios from 'axios'

// Criar cliente Query para React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

// Configuração da Sidebar
const sidebarSections: SidebarSection[] = [
  {
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
      { id: 'kanban', label: 'Kanban', icon: '📋', path: '/kanban' },
      { id: 'wiki', label: 'Wiki', icon: '📖', path: '/wiki' },
    ]
  },
  {
    title: 'Operações',
    items: [
      { id: 'jobs', label: 'Jobs', icon: '⚡', path: '/jobs' },
      { id: 'agents', label: 'Agents', icon: '🤖', path: '/agents' },
      { id: 'worktrees', label: 'Worktrees', icon: '🌲', path: '/worktrees' },
      { id: 'events', label: 'Eventos', icon: '🎭', path: '/events' },
      { id: 'logs', label: 'Logs', icon: '📋', path: '/logs' },
    ]
  }
]

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/web">
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

function AppContent() {
  const location = useLocation()

  // Atualizar título da página com versão da API
  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await axios.get('/api/health')
        const serverVersion = response.data?.version || '0.0.0'
        document.title = `Skybridge v${serverVersion}`
      } catch (error) {
        console.error('Erro ao buscar versão:', error)
        document.title = 'Skybridge'
      }
    }

    fetchVersion()
  }, [])

  return (
    <div>
      <Header />
      <div className="app-layout d-flex">
        <Sidebar sections={sidebarSections} />

        <main className="app-main flex-grow-1">
          <div className="container-fluid py-4">
            {/* Navbar Contextual */}
            <ContextualNavbar currentPath={location.pathname} />

            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/kanban" element={<Kanban />} />
              <Route path="/wiki" element={<Wiki />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/worktrees" element={<Worktrees />} />
              <Route path="/events" element={<Events />} />
              <Route path="/logs" element={<Logs />} />
              {/* Rotas futuras - redirect para Dashboard */}
              <Route path="/settings" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
