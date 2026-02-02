import { useState, useEffect, useRef, useCallback } from 'react'
import { Card, Badge, Spinner } from 'react-bootstrap'
import { observabilityApi } from '../api/endpoints'

interface LogEntry {
  timestamp: string
  level: string
  logger: string
  message: string
  message_html: string
}

interface LogStreamProps {
  paused?: boolean
}

export default function LogStream({ paused = false }: LogStreamProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const logContainerRef = useRef<HTMLDivElement>(null)
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const filenameRef = useRef<string | null>(null)

  // Função para buscar logs mais recentes (usando useCallback para manter referência estável)
  const fetchLatestLogs = useCallback(async (filename: string) => {
    try {
      const response = await observabilityApi.streamLogs(filename, 50)

      if (response.data.ok && response.data.entries.length > 0) {
        const newLogs = response.data.entries

        setLogs(prev => {
          // Adiciona logs novos no início (mais recentes primeiro)
          const updated = [...newLogs.reverse(), ...prev]
          return updated.slice(0, 50) // Manter apenas os 50 mais recentes
        })

        setIsConnected(true)
        setError(null)
      } else {
        setIsConnected(false)
      }
    } catch (err) {
      console.error('[LogStream] Erro ao buscar logs:', err)
      setError('Erro ao buscar logs')
      setIsConnected(false)
    }
  }, [])

  useEffect(() => {
    console.log('[LogStream] Iniciando polling de logs...')

    // Inicia o polling
    const startPolling = async () => {
      // Busca arquivos de log primeiro
      try {
        const filesResponse = await observabilityApi.getLogFiles()
        if (filesResponse.data.ok && filesResponse.data.files.length > 0) {
          const latestFile = filesResponse.data.files[0].name
          filenameRef.current = latestFile
          console.log('[LogStream] Arquivo de log:', latestFile)

          // Busca logs imediatamente
          await fetchLatestLogs(latestFile)

          // Configura polling a cada 2 segundos
          pollIntervalRef.current = setInterval(() => fetchLatestLogs(latestFile), 2000)
          console.log('[LogStream] Polling configurado: intervalo 2s')
        }
      } catch (err) {
        console.error('[LogStream] Erro ao buscar arquivos de log:', err)
        setError('Erro ao carregar logs')
      }
    }

    startPolling()

    // Cleanup ao desmontar - CRÍTICO: deve parar o polling
    return () => {
      console.log('[LogStream] LIMPANDO: parando polling...')
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
        console.log('[LogStream] Polling PARADO')
      }
    }
  }, [fetchLatestLogs])

  // Pausa/retoma o polling quando a prop paused muda
  useEffect(() => {
    if (paused && pollIntervalRef.current) {
      console.log('[LogStream] PAUSANDO polling (usuário clicou em pausar)')
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    } else if (!paused && filenameRef.current && !pollIntervalRef.current) {
      // Retoma o polling
      console.log('[LogStream] RETOMANDO polling')
      pollIntervalRef.current = setInterval(() => {
        fetchLatestLogs(filenameRef.current!)
      }, 2000)
    }
  }, [paused, fetchLatestLogs])

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
