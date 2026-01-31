import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Spinner, Alert, Badge, Table, ProgressBar, Collapse, Button } from 'react-bootstrap'
import { healthApi, webhooksApi, observabilityApi, type JobMetrics } from '../api/endpoints'
import LogStream from '../components/LogStream'

/**
 * Página Dashboard com métricas principais.
 * Objetivo: RF001 - Dashboard Principal com Métricas
 */
export default function Dashboard() {
  const [expandedCard, setExpandedCard] = useState<string | null>(null)
  const [logStreamPaused, setLogStreamPaused] = useState(false)

  // Query para health check
  const { data: health, isLoading: healthLoading, error: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await healthApi.get()
      return res.data
    },
    refetchInterval: 5000,
  })

  // Query para jobs
  const { data: jobsData, isLoading: jobsLoading, error: jobsError } = useQuery({
    queryKey: ['webhook-jobs'],
    queryFn: async () => {
      const res = await webhooksApi.listJobs()
      return res.data
    },
    refetchInterval: 5000,
  })

  // Query para logs files
  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ['logs-files'],
    queryFn: async () => {
      const res = await observabilityApi.getLogFiles()
      return res.data
    },
    refetchInterval: 10000,
  })

  // Métricas
  const metrics: JobMetrics = (jobsData as any)?.metrics ?? {}
  const activeJobs = metrics.queue_size ?? metrics.processing ?? 0
  const completedJobs = metrics.total_completed ?? 0
  const failedJobs = metrics.total_failed ?? 0
  const totalJobs = metrics.total_enqueued ?? 0
  const successRate = totalJobs > 0
    ? ((completedJobs / totalJobs) * 100).toFixed(1)
    : '0.0'

  // Status helper
  const getHealthStatus = () => {
    if (healthLoading) return { variant: 'secondary' as const, text: 'Verificando...', icon: '🔄' }
    if (health?.status === 'healthy') return { variant: 'success' as const, text: 'ONLINE', icon: '✓' }
    return { variant: 'danger' as const, text: 'OFFLINE', icon: '✗' }
  }

  const getJobStatusVariant = () => {
    if (activeJobs > 0) return 'primary' as const
    if (totalJobs > 0) return 'success' as const
    return 'secondary' as const
  }

  const getSuccessRateVariant = () => {
    const rate = parseFloat(successRate)
    if (rate >= 90) return 'success' as const
    if (rate >= 70) return 'warning' as const
    if (rate > 0) return 'danger' as const
    return 'secondary' as const
  }

  const healthStatus = getHealthStatus()
  const lastUpdate = new Date().toLocaleTimeString('pt-BR')

  // Card click handler
  const handleCardClick = (cardId: string) => {
    if (expandedCard === cardId) {
      setExpandedCard(null)
    } else {
      setExpandedCard(cardId)
    }
  }

  // Log files count
  const logFilesCount = logsData?.files?.length ?? 0
  const currentLogFile = logsData?.files?.[0]?.name ?? null

  return (
    <div>
      <small className="text-muted d-block mb-3">
        Última atualização: {lastUpdate}
      </small>

      {(healthError || jobsError) && (
        <Alert variant="warning">
          Erro ao carregar métricas. Verifique se a API está rodando.
        </Alert>
      )}

      {/* 4 Cards de Métricas */}
      <Row className="g-4 mb-4">
        {/* API Status Card */}
        <Col md={3}>
          <Card
            className={`h-100 border-${healthStatus.variant} cursor-pointer ${expandedCard === 'health' ? 'shadow-sm' : ''}`}
            onClick={() => handleCardClick('health')}
          >
            <Card.Body className="d-flex align-items-center">
              <div className={`display-6 me-3 text-${healthStatus.variant}`}>
                {healthLoading ? <Spinner size="sm" /> : healthStatus.icon}
              </div>
              <div className="flex-grow-1">
                <Card.Subtitle className="text-muted mb-1">API Status</Card.Subtitle>
                <h3 className={`mb-0 text-${healthStatus.variant}`}>{healthStatus.text}</h3>
                <small className="text-muted">
                  {health?.version || 'v0.0.0'}
                </small>
                <div className="mt-1">
                  <small className="text-muted">👆 Clique para detalhes</small>
                </div>
              </div>
            </Card.Body>

            {/* Expanded Content */}
            <Collapse in={expandedCard === 'health'}>
              <div className="border-top pt-3 mt-3">
                <h6>Detalhes da API</h6>
                <Table size="sm" bordered>
                  <tbody>
                    <tr>
                      <td><strong>Status</strong></td>
                      <td>{health?.status || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td><strong>Versão</strong></td>
                      <td>{health?.version || 'N/A'}</td>
                    </tr>
                    <tr>
                      <td><strong>Timestamp</strong></td>
                      <td><small>{health?.timestamp || 'N/A'}</small></td>
                    </tr>
                  </tbody>
                </Table>
              </div>
            </Collapse>
          </Card>
        </Col>

        {/* Jobs Ativos Card */}
        <Col md={3}>
          <Card
            className="h-100 cursor-pointer hover-shadow-sm transition"
            onClick={() => handleCardClick('jobs')}
          >
            <Card.Body className="d-flex align-items-center">
              <div className={`display-6 me-3 text-${getJobStatusVariant()}`}>
                {jobsLoading ? <Spinner size="sm" /> : '⚡'}
              </div>
              <div className="flex-grow-1">
                <Card.Subtitle className="text-muted mb-1">Jobs Ativos</Card.Subtitle>
                <h3 className={`mb-0 text-${getJobStatusVariant()}`}>
                  {jobsLoading ? '...' : activeJobs}
                </h3>
                <small className="text-muted">
                  fila: {metrics.queue_size ?? 0}
                </small>
                <div className="mt-1">
                  <small className="text-muted">👆 Clique para detalhes</small>
                </div>
              </div>
            </Card.Body>

            {/* Expanded Content */}
            <Collapse in={expandedCard === 'jobs'}>
              <div className="border-top pt-3 mt-3">
                <h6>Distribuição de Jobs</h6>
                <Table size="sm" bordered>
                  <tbody>
                    <tr>
                      <td>📥 Na fila</td>
                      <td className="text-end"><strong>{metrics.queue_size ?? 0}</strong></td>
                    </tr>
                    <tr>
                      <td>⚙️ Processando</td>
                      <td className="text-end"><strong>{metrics.processing ?? 0}</strong></td>
                    </tr>
                    <tr>
                      <td>✅ Concluídos</td>
                      <td className="text-end text-success"><strong>{completedJobs}</strong></td>
                    </tr>
                    <tr>
                      <td>❌ Falharam</td>
                      <td className="text-end text-danger"><strong>{failedJobs}</strong></td>
                    </tr>
                    <tr>
                      <td>📊 Total</td>
                      <td className="text-end"><strong>{totalJobs}</strong></td>
                    </tr>
                  </tbody>
                </Table>
              </div>
            </Collapse>
          </Card>
        </Col>

        {/* Success Rate Card */}
        <Col md={3}>
          <Card
            className="h-100 cursor-pointer hover-shadow-sm transition"
            onClick={() => handleCardClick('success')}
          >
            <Card.Body className="d-flex align-items-center">
              <div className={`display-6 me-3 text-${getSuccessRateVariant()}`}>
                {jobsLoading ? <Spinner size="sm" /> : '📊'}
              </div>
              <div className="flex-grow-1">
                <Card.Subtitle className="text-muted mb-1">Success Rate</Card.Subtitle>
                <h3 className={`mb-0 text-${getSuccessRateVariant()}`}>
                  {jobsLoading ? '...' : successRate}%
                </h3>
                <small className="text-muted">
                  {completedJobs}/{totalJobs}
                </small>
                <div className="mt-1">
                  <small className="text-muted">👆 Clique para breakdown</small>
                </div>
              </div>
            </Card.Body>

            {/* Expanded Content */}
            <Collapse in={expandedCard === 'success'}>
              <div className="border-top pt-3 mt-3">
                <h6>Taxa de Sucesso</h6>
                <Table size="sm" bordered>
                  <tbody>
                    <tr>
                      <td>🎉 Excelente</td>
                      <td className="text-success">&gt;= 90%</td>
                    </tr>
                    <tr>
                      <td>👍 Bom</td>
                      <td className="text-warning">70-89%</td>
                    </tr>
                    <tr>
                      <td>⚠️ Atenção</td>
                      <td className="text-danger">&lt; 70%</td>
                    </tr>
                    <tr>
                      <td>📊 Atual</td>
                      <td className={getSuccessRateVariant() === 'success' ? 'text-success' :
                               getSuccessRateVariant() === 'warning' ? 'text-warning' :
                               getSuccessRateVariant() === 'danger' ? 'text-danger' : 'text-muted'}>
                        {successRate}%
                      </td>
                    </tr>
                  </tbody>
                </Table>
              </div>
            </Collapse>
          </Card>
        </Col>

        {/* Logs Card - Inline (sem link) */}
        <Col md={3}>
          <Card className="h-100">
            <Card.Body className="d-flex align-items-center">
              <div className="display-6 me-3 text-warning">
                📋
              </div>
              <div className="flex-grow-1">
                <Card.Subtitle className="text-muted mb-1">Logs</Card.Subtitle>
                <h3 className="mb-0 text-warning">
                  {logsLoading ? '...' : logFilesCount}
                </h3>
                <small className="text-muted">arquivos</small>
                {currentLogFile && (
                  <div className="mt-1">
                    <small className="text-muted text-truncate d-block" style={{ maxWidth: '150px' }}>
                      {currentLogFile}
                    </small>
                  </div>
                )}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Logs ao Vivo */}
      <Card className="mb-4">
        <Card.Header className="d-flex justify-content-between align-items-center py-2">
          <Card.Title className="mb-0 fs-6">📡 Logs ao Vivo</Card.Title>
          {!logsLoading && currentLogFile && (
            <Badge bg={logStreamPaused ? 'warning' : 'success'} className="me-2">
              {logStreamPaused ? 'Pausado' : 'Ao vivo'}
            </Badge>
          )}
          <Button
            variant={logStreamPaused ? 'success' : 'warning'}
            size="sm"
            onClick={() => setLogStreamPaused(!logStreamPaused)}
          >
            {logStreamPaused ? '▶ Retomar' : '⏸ Pausar'}
          </Button>
        </Card.Header>
        <Card.Body className="p-0">
          <LogStream paused={logStreamPaused} />
        </Card.Body>
      </Card>

      {/* Progress Summary */}
      {totalJobs > 0 && (
        <Row className="g-4 mb-4">
          <Col md={12}>
            <Card>
              <Card.Body>
                <Card.Subtitle className="mb-3">Progresso dos Jobs</Card.Subtitle>
                <ProgressBar>
                  <ProgressBar
                    variant="success"
                    now={totalJobs > 0 ? (completedJobs / totalJobs) * 100 : 0}
                    label={`${completedJobs} concluídos`}
                    title={`${completedJobs} concluídos`}
                  />
                  <ProgressBar
                    variant="danger"
                    now={totalJobs > 0 ? (failedJobs / totalJobs) * 100 : 0}
                    label={`${failedJobs} falhos`}
                    title={`${failedJobs} falhos`}
                  />
                  <ProgressBar
                    variant="info"
                    now={totalJobs > 0 ? (activeJobs / totalJobs) * 100 : 0}
                    label={`${activeJobs} ativos`}
                    title={`${activeJobs} ativos`}
                  />
                </ProgressBar>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Info Card */}
      <Card className="mt-4 bg-light">
        <Card.Body>
          <Card.Title className="h6">ℹ️ Sobre o Skybridge WebUI</Card.Title>
          <Card.Text className="text-muted mb-0">
            Dashboard de monitoramento em tempo real do sistema de webhook agents.
            Métricas atualizadas automaticamente a cada 5-10 segundos.
          </Card.Text>
        </Card.Body>
      </Card>
    </div>
  )
}
