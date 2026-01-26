import { useState, useEffect, useRef } from 'react'
import { Card, Badge, Spinner } from 'react-bootstrap'
import apiClient from '../api/client'

interface LogEntry {
  timestamp: string
  level: string
  logger: string
  message: string
  message_html: string
}

export default function LogStream() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [logFile, setLogFile] = useState<string>('')
  const logContainerRef = useRef<HTMLDivElement>(null)
  const lastLogCountRef = useRef<number>(0)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    console.log('[LogStream] Iniciando polling de logs...')

    // Primeiro, busca o arquivo de log mais recente
    const initLogFile = async () => {
      try {
        const filesResponse = await apiClient.get<{ ok: boolean; files: { name: string }[] }>('/logs/files')
        if (filesResponse.data.ok && filesResponse.data.files.length > 0) {
          const latestFile = filesResponse.data.files[0].name
          setLogFile(latestFile)
          console.log('[LogStream] Arquivo de log:', latestFile)
          return latestFile
        }
      } catch (err) {
        console.error('[LogStream] Erro ao buscar arquivo de log:', err)
        setError('Erro ao carregar logs')
        return null
      }
    }

    // Função para buscar logs mais recentes
    const fetchLatestLogs = async (filename: string) => {
      try {
        const response = await apiClient.get<{
          ok: boolean
          entries: any[]
          total: number
        }>(`/logs/file/${filename}`, {
          params: { page: 1, per_page: 20 }
        })

        if (response.data.ok && response.data.entries.length > 0) {
          const newLogs = response.data.entries
          const currentCount = lastLogCountRef.current

          // Se há novos logs, adiciona apenas os novos
          if (newLogs.length !== currentCount) {
            const logsToAdd = newLogs.slice(0, newLogs.length - currentCount)
            lastLogCountRef.current = newLogs.length

            setLogs(prev => {
              const updated = [...logsToAdd.map((e: any) => ({
                timestamp: e.timestamp,
                level: e.level,
                logger: e.logger,
                message: e.message,
                message_html: e.message_html
              })), ...prev]
              return updated.slice(0, 20)
            })

            setIsConnected(true)
            setError(null)
          }
        }
      } catch (err) {
        console.error('[LogStream] Erro ao buscar logs:', err)
        setError('Erro ao buscar logs')
        setIsConnected(false)
      }
    }

    // Inicia o polling
    const startPolling = async () => {
      const filename = await initLogFile()
      if (!filename) return

      // Busca imediatamente
      await fetchLatestLogs(filename)

      // Configura polling a cada 2 segundos
      pollIntervalRef.current = setInterval(() => fetchLatestLogs(filename), 2000)
    }

    startPolling()

    // Cleanup ao desmontar
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  // Auto-scroll para o topo quando novos logs chegam
  useEffect(() => {
    if (logContainerRef.current && logs.length > 0) {
      logContainerRef.current.scrollTop = 0
    }
  }, [logs])

  const getLevelVariant = (level: string) => {
    const l = level.toUpperCase()
    if (l === 'DEBUG') return 'secondary'
    if (l === 'INFO') return 'primary'
    if (l === 'WARNING') return 'warning'
    if (l === 'ERROR') return 'danger'
    if (l === 'CRITICAL') return 'danger'
    return 'secondary'
  }

  return (
    <Card className="mb-4" style={{ maxHeight: '300px', overflow: 'hidden' }}>
      <Card.Header className="d-flex justify-content-between align-items-center py-2 px-3">
        <span className="small fw-bold">
          📡 Logs ao Vivo
        </span>
        <div className="d-flex align-items-center gap-2">
          {error && <Badge bg="danger">Desconectado</Badge>}
          {!error && isConnected && (
            <Badge bg="success" className="d-flex align-items-center">
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'currentColor', marginRight: '4px', animation: 'pulse 1s infinite' }}></span>
              Ao vivo
            </Badge>
          )}
          {!error && !isConnected && (
            <Badge bg="secondary" className="d-flex align-items-center">
              <Spinner animation="grow" size="sm" className="me-1" style={{ width: '10px', height: '10px' }} />
              Conectando...
            </Badge>
          )}
        </div>
      </Card.Header>
      <Card.Body
        ref={logContainerRef}
        className="p-2"
        style={{
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
          fontFamily: 'monospace',
          fontSize: '11px',
          overflowY: 'auto',
          maxHeight: '250px'
        }}
      >
        {logs.length === 0 ? (
          <div className="text-muted text-center py-3 small">
            {error ? error : 'Aguardando logs...'}
          </div>
        ) : (
          <div>
            {logs.map((log, idx) => (
              <div
                key={`${log.timestamp}-${idx}`}
                className="mb-1"
                style={{
                  borderBottom: '1px solid #333',
                  paddingBottom: '2px',
                  marginBottom: '2px'
                }}
              >
                <span style={{ color: '#888' }}>{log.timestamp}</span>
                {' '}
                <Badge bg={getLevelVariant(log.level)} className="fs-6" style={{ fontSize: '9px' }}>
                  {log.level}
                </Badge>
                {' '}
                <span style={{ color: '#6ecaff' }}>{log.logger}</span>
                {' '}
                <span
                  style={{ color: '#d4d4d4' }}
                  dangerouslySetInnerHTML={{ __html: log.message_html }}
                />
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
