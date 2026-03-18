import { useState, useEffect, useRef } from 'react'
import { Card, Badge, Button } from 'react-bootstrap'
import apiClient from '@/api/client'

// Tipos para EventSource (API nativa do browser)
declare global {
  interface EventSourceEventMap {
    history: MessageEvent
    domain_event: MessageEvent
  }
}

interface DomainEvent {
  event_id: string
  timestamp: string
  event_type: string
  aggregate_id: string
  version: number
  [key: string]: any // Allow additional fields from specific event types
}

interface EventStreamProps {
  paused?: boolean
}

export default function EventStream({ paused = false }: EventStreamProps) {
  const [events, setEvents] = useState<DomainEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const eventContainerRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    console.log('[EventStream] Conectando ao SSE...')

    // Obtém workspace ativo do localStorage (mesma lógica do useWorkspaces)
    const WORKSPACE_STORAGE_KEY = 'skybridge_active_workspace'
    const activeWorkspace = localStorage.getItem(WORKSPACE_STORAGE_KEY) || 'core'

    // Cria EventSource para streaming de eventos
    // DOC: ADR024 - Passa workspace via query parameter (EventSource não suporta headers)
    const eventSource = new EventSource(`/api/observability/events/stream?workspace=${activeWorkspace}`)
    eventSourceRef.current = eventSource

    // Conectado
    eventSource.onopen = () => {
      console.log('[EventStream] Conectado')
      setIsConnected(true)
      setError(null)
    }

    // Erro
    eventSource.onerror = () => {
      console.error('[EventStream] Erro de conexão')
      setError('Desconectado')
      setIsConnected(false)
    }

    // Eventos de histórico
    eventSource.addEventListener('history', (e) => {
      try {
        const event = JSON.parse(e.data)
        console.log('[EventStream] Histórico recebido:', event.event_type, event)
        setEvents(prev => [...prev, event].slice(0, 100))
        setIsConnected(true)
        setError(null)
      } catch (err) {
        console.error('[EventStream] Erro ao parse histórico:', err, e.data)
      }
    })

    // Novos eventos de domínio
    eventSource.addEventListener('domain_event', (e) => {
      try {
        const event = JSON.parse(e.data)
        console.log('[EventStream] Novo evento recebido:', event.event_type, event)
        setEvents(prev => [event, ...prev].slice(0, 100))
        setIsConnected(true)
        setError(null)
      } catch (err) {
        console.error('[EventStream] Erro ao parse evento:', err, e.data)
      }
    })

    // Captura todas as mensagens SSE para debug
    eventSource.addEventListener('message', (e) => {
      console.log('[EventStream] Mensagem SSE bruta:', e.data)
    })

    // Log quando conexão fecha
    eventSource.addEventListener('close', () => {
      console.log('[EventStream] Conexão fechada pelo servidor')
    })

    // Cleanup ao desmontar
    return () => {
      console.log('[EventStream] Fechando conexão')
      eventSource.close()
    }
  }, [])

  // Auto-scroll para o topo quando novos eventos chegam
  useEffect(() => {
    if (eventContainerRef.current && events.length > 0 && !paused) {
      eventContainerRef.current.scrollTop = 0
    }
  }, [events, paused])

  const getEventColor = (eventType: string) => {
    const t = eventType.toUpperCase()

    // Job events
    if (t.includes('STARTED')) return '#4dabf7' // blue
    if (t.includes('COMPLETED')) return '#51cf66' // green
    if (t.includes('FAILED')) return '#ff6b6b' // red
    if (t.includes('CREATED')) return '#ffd43b' // yellow

    // Issue events
    if (t.includes('ISSUE')) return '#da77f2' // purple

    // Commit/PR events
    if (t.includes('COMMIT')) return '#69db7c' // light green
    if (t.includes('PUSH')) return '#38d9a9' // teal
    if (t.includes('PR') || t.includes('PULL')) return '#748ffc' // indigo

    return '#adb5bd' // gray
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const renderEventDetails = (event: DomainEvent) => {
    const details: string[] = []

    // Campos comuns
    if (event.aggregate_id) {
      details.push(`ID: ${event.aggregate_id.slice(0, 8)}...`)
    }

    // Campos específicos por tipo de evento
    if (event.job_id) {
      details.push(`Job: ${event.job_id.slice(0, 8)}...`)
    }
    if (event.issue_number) {
      details.push(`Issue: #${event.issue_number}`)
    }
    if (event.repository) {
      details.push(`Repo: ${event.repository}`)
    }
    if (event.commit_hash) {
      details.push(`Commit: ${event.commit_hash.slice(0, 7)}`)
    }
    if (event.pr_url) {
      details.push(`PR: criado`)
    }
    if (event.message) {
      details.push(`Msg: ${event.message}`)
    }

    return details.join(' | ')
  }

  // Limpar histórico de eventos
  const handleClearEvents = async () => {
    try {
      // DOC: ADR023 - Usa apiClient para incluir header X-Workspace
      await apiClient.delete('/api/observability/events/history')
      setEvents([])
      console.log('[EventStream] Histórico limpo')
    } catch (err) {
      console.error('[EventStream] Erro ao limpar histórico:', err)
    }
  }

  // Gerar eventos fake
  const handleGenerateFake = async (count: number = 5) => {
    try {
      // DOC: ADR023 - Usa apiClient para incluir header X-Workspace
      const response = await apiClient.post('/api/observability/events/generate-fake', null, {
        params: { count }
      })
      console.log(`[EventStream] Gerados ${response.data.count} eventos fake`)
    } catch (err) {
      console.error('[EventStream] Erro ao gerar eventos fake:', err)
    }
  }

  return (
    <Card className="mb-4" style={{ maxHeight: '400px', overflow: 'hidden' }}>
      <Card.Header className="d-flex justify-content-between align-items-center py-2 px-3">
        <div className="d-flex align-items-center gap-3">
          <span className="small fw-bold">
            🎭 Eventos de Domínio
          </span>
          <div className="d-flex gap-2">
            <Button
              variant="outline-secondary"
              size="sm"
              onClick={handleClearEvents}
              style={{ fontSize: '11px', padding: '2px 8px' }}
              title="Limpar todos os eventos"
            >
              🗑️ Limpar
            </Button>
            <Button
              variant="outline-primary"
              size="sm"
              onClick={() => handleGenerateFake(5)}
              style={{ fontSize: '11px', padding: '2px 8px' }}
              title="Gerar 5 eventos fake para teste"
            >
              ⚡ Gerar 5
            </Button>
            <Button
              variant="outline-primary"
              size="sm"
              onClick={() => handleGenerateFake(20)}
              style={{ fontSize: '11px', padding: '2px 8px' }}
              title="Gerar 20 eventos fake para teste"
            >
              ⚡ Gerar 20
            </Button>
          </div>
        </div>
        <div className="d-flex align-items-center gap-2">
          <Badge bg="secondary" className="fs-6" style={{ fontSize: '10px' }}>
            {events.length} eventos
          </Badge>
          {error && <Badge bg="danger">Desconectado</Badge>}
          {!error && isConnected && (
            <Badge bg="success" className="d-flex align-items-center">
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'currentColor', marginRight: '4px', animation: 'pulse 1s infinite' }}></span>
              Ao vivo
            </Badge>
          )}
          {!error && !isConnected && (
            <Badge bg="secondary" className="d-flex align-items-center">
              Conectando...
            </Badge>
          )}
        </div>
      </Card.Header>
      <Card.Body
        ref={eventContainerRef}
        className="p-2"
        style={{
          backgroundColor: '#0d1117',
          color: '#c9d1d9',
          fontFamily: 'monospace',
          fontSize: '11px',
          overflowY: 'auto',
          maxHeight: '350px'
        }}
      >
        {events.length === 0 ? (
          <div className="text-muted text-center py-3 small">
            {error ? error : 'Aguardando eventos...'}
          </div>
        ) : (
          <div>
            {events.map((event) => (
              <div
                key={event.event_id}
                className="mb-2 p-2 rounded"
                style={{
                  borderBottom: '1px solid #30363d',
                  paddingBottom: '8px',
                  marginBottom: '8px',
                  borderLeft: `3px solid ${getEventColor(event.event_type)}`
                }}
              >
                <div className="d-flex align-items-start gap-2">
                  <span style={{ color: '#8b949e', minWidth: '70px' }}>
                    {formatTimestamp(event.timestamp)}
                  </span>
                  <div className="flex-grow-1">
                    <div style={{ color: getEventColor(event.event_type), fontWeight: 'bold' }}>
                      {event.event_type}
                    </div>
                    {renderEventDetails(event) && (
                      <div style={{ color: '#8b949e', fontSize: '10px', marginTop: '2px' }}>
                        {renderEventDetails(event)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card.Body>
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}
      </style>
    </Card>
  )
}
