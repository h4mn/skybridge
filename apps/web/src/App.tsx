import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import Worktrees from './pages/Worktrees'
import Logs from './pages/Logs'

// Criar cliente Query para React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/web">
        <div className="App">
          <Header />
          <main className="container-fluid py-4">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/worktrees" element={<Worktrees />} />
              <Route path="/logs" element={<Logs />} />
              {/* Rotas futuras - redirect para Dashboard */}
              <Route path="/settings" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
