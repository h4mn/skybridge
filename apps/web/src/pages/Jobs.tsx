import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Table,
  Button,
  Badge,
  Spinner,
  Alert,
  Modal,
  Form,
  FormControl,
  InputGroup,
  Pagination,
} from 'react-bootstrap'
import { webhooksApi, type WebhookJob, JobStatus } from '../api/endpoints'

/**
 * Página Jobs - Lista e gerencia jobs de webhooks.
 * Objetivo: RF003 - Tabela de Jobs Ativos (Fase 3)
 */
export default function Jobs() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Modal state
  const [selectedJob, setSelectedJob] = useState<WebhookJob | null>(null)

  // Query para jobs
  const {
    data: jobsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['webhook-jobs'],
    queryFn: async () => {
      const res = await webhooksApi.listJobs()
      return res.data
    },
    refetchInterval: 5000, // Atualiza a cada 5s
  })

  const jobs = jobsData?.jobs ?? []

  // Filtros
  const filteredJobs = jobs.filter((job) => {
    const matchesSearch =
      searchTerm === '' ||
      job.job_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.event_type.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus =
      statusFilter === 'all' || job.status === statusFilter

    const matchesSource =
      sourceFilter === 'all' || job.source === sourceFilter

    return matchesSearch && matchesStatus && matchesSource
  })

  // Paginação
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredJobs.slice(indexOfFirstItem, indexOfLastItem)
  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage)

  // Handlers
  const handleView = (job: WebhookJob) => {
    setSelectedJob(job)
  }

  // Status badge helper
  const getStatusBadge = (status: JobStatus) => {
    switch (status) {
      case JobStatus.COMPLETED:
        return 'success'
      case JobStatus.FAILED:
      case JobStatus.TIMED_OUT:
        return 'danger'
      case JobStatus.PROCESSING:
        return 'primary'
      case JobStatus.PENDING:
        return 'secondary'
      default:
        return 'secondary'
    }
  }

  // Status icon helper
  const getStatusIcon = (status: JobStatus) => {
    switch (status) {
      case JobStatus.COMPLETED:
        return '✅'
      case JobStatus.FAILED:
        return '❌'
      case JobStatus.TIMED_OUT:
        return '⏱️'
      case JobStatus.PROCESSING:
        return '⚙️'
      case JobStatus.PENDING:
        return '⏳'
      default:
        return '❓'
    }
  }

  // Formata data relativa
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'agora'
    if (diffMins < 60) return `${diffMins}m atrás`
    if (diffHours < 24) return `${diffHours}h atrás`
    return `${diffDays}d atrás`
  }

  // Formata data completa
  const formatFullDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="mb-0">Jobs</h1>
        <Button variant="outline-primary" size="sm" onClick={() => refetch()}>
          🔄 Atualizar
        </Button>
      </div>

      {error && (
        <Alert variant="warning">
          Erro ao carregar jobs. Verifique se a API está rodando.
        </Alert>
      )}

      {/* Métricas Summary */}
      {jobsData?.metrics && (
        <Card className="mb-4 bg-light">
          <Card.Body>
            <div className="row text-center">
              <div className="col-md-2">
                <div className="text-muted small">Na Fila</div>
                <div className="h4 mb-0">{jobsData.metrics.queue_size ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Processando</div>
                <div className="h4 mb-0 text-primary">{jobsData.metrics.processing ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Concluídos</div>
                <div className="h4 mb-0 text-success">{jobsData.metrics.total_completed ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Falharam</div>
                <div className="h4 mb-0 text-danger">{jobsData.metrics.total_failed ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Total</div>
                <div className="h4 mb-0">{jobsData.metrics.total_enqueued ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Taxa Sucesso</div>
                <div className="h4 mb-0">
                  {jobsData.metrics.total_enqueued > 0
                    ? ((jobsData.metrics.total_completed / jobsData.metrics.total_enqueued) * 100).toFixed(1)
                    : '0.0'}%
                </div>
              </div>
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Filtros */}
      <Card className="mb-4">
        <Card.Body>
          <div className="row g-3">
            <div className="col-md-4">
              <InputGroup>
                <FormControl
                  placeholder="Buscar por job_id ou evento..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value)
                    setCurrentPage(1)
                  }}
                />
                <InputGroup.Text>🔍</InputGroup.Text>
              </InputGroup>
            </div>
            <div className="col-md-3">
              <Form.Select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value)
                  setCurrentPage(1)
                }}
              >
                <option value="all">Todos os status</option>
                <option value={JobStatus.PENDING}>Pendentes</option>
                <option value={JobStatus.PROCESSING}>Em processamento</option>
                <option value={JobStatus.COMPLETED}>Concluídos</option>
                <option value={JobStatus.FAILED}>Falharam</option>
                <option value={JobStatus.TIMED_OUT}>Timeout</option>
              </Form.Select>
            </div>
            <div className="col-md-3">
              <Form.Select
                value={sourceFilter}
                onChange={(e) => {
                  setSourceFilter(e.target.value)
                  setCurrentPage(1)
                }}
              >
                <option value="all">Todas as fontes</option>
                <option value="github">GitHub</option>
                <option value="trello">Trello</option>
              </Form.Select>
            </div>
            <div className="col-md-2">
              <div className="text-muted pt-2">
                Mostrando {filteredJobs.length} de {jobs.length} jobs
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Tabela */}
      <Card>
        <Card.Body className="p-0">
          {isLoading ? (
            <div className="text-center py-5">
              <Spinner animation="border" />
              <p className="mt-3 text-muted">Carregando jobs...</p>
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="text-center py-5 text-muted">
              {searchTerm || statusFilter !== 'all' || sourceFilter !== 'all'
                ? 'Nenhum job encontrado com os filtros atuais.'
                : 'Nenhum job encontrado.'}
            </div>
          ) : (
            <>
              <Table hover responsive>
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Job ID</th>
                    <th>Fonte</th>
                    <th>Evento</th>
                    <th>Criado</th>
                    <th>Worktree</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {currentItems.map((job) => (
                    <tr key={job.job_id}>
                      <td>
                        <Badge bg={getStatusBadge(job.status)} className="fs-6">
                          {getStatusIcon(job.status)} {job.status}
                        </Badge>
                      </td>
                      <td>
                        <code className="text-primary" style={{ fontSize: '0.85em' }}>
                          {job.job_id.slice(0, 8)}...
                        </code>
                      </td>
                      <td>
                        <Badge bg="info" className="fs-6">
                          {job.source}
                        </Badge>
                      </td>
                      <td>
                        <small className="text-muted">{job.event_type}</small>
                      </td>
                      <td>
                        <small className="text-muted" title={formatFullDate(job.created_at)}>
                          {formatRelativeTime(job.created_at)}
                        </small>
                      </td>
                      <td>
                        {job.worktree_path ? (
                          <small className="text-truncate d-block" style={{ maxWidth: '120px' }} title={job.worktree_path}>
                            {job.worktree_path.split(/[/\\]/).pop()}
                          </small>
                        ) : (
                          <small className="text-muted">-</small>
                        )}
                      </td>
                      <td>
                        <Button
                          size="sm"
                          variant="outline-primary"
                          onClick={() => handleView(job)}
                          title="Ver detalhes"
                        >
                          👁️ Detalhes
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>

              {/* Paginação */}
              {totalPages > 1 && (
                <div className="d-flex justify-content-center mt-4">
                  <Pagination>
                    <Pagination.First
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                    />
                    <Pagination.Prev
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    />
                    <Pagination.Item>{currentPage}</Pagination.Item>
                    <Pagination.Item>{totalPages}</Pagination.Item>
                    <Pagination.Next
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    />
                    <Pagination.Last
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                    />
                  </Pagination>
                </div>
              )}
            </>
          )}
        </Card.Body>
      </Card>

      {/* Modal de Detalhes */}
      <Modal
        show={!!selectedJob}
        onHide={() => setSelectedJob(null)}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Detalhes do Job</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedJob && (
            <div>
              <Table bordered size="sm">
                <tbody>
                  <tr>
                    <th style={{ width: '140px' }}>Job ID</th>
                    <td><code>{selectedJob.job_id}</code></td>
                  </tr>
                  <tr>
                    <th>Status</th>
                    <td>
                      <Badge bg={getStatusBadge(selectedJob.status)} className="fs-6">
                        {getStatusIcon(selectedJob.status)} {selectedJob.status}
                      </Badge>
                    </td>
                  </tr>
                  <tr>
                    <th>Fonte</th>
                    <td>
                      <Badge bg="info" className="fs-6">
                        {selectedJob.source}
                      </Badge>
                    </td>
                  </tr>
                  <tr>
                    <th>Tipo de Evento</th>
                    <td><code>{selectedJob.event_type}</code></td>
                  </tr>
                  <tr>
                    <th>Criado em</th>
                    <td>{formatFullDate(selectedJob.created_at)}</td>
                  </tr>
                  <tr>
                    <th>Worktree Path</th>
                    <td>
                      {selectedJob.worktree_path ? (
                        <code style={{ fontSize: '0.9em' }}>{selectedJob.worktree_path}</code>
                      ) : (
                        <span className="text-muted">N/A</span>
                      )}
                    </td>
                  </tr>
                </tbody>
              </Table>

              {/* Agent Log (placeholder - se implementado no futuro) */}
              <Alert variant="info" className="mt-3 mb-0">
                <small>
                  ℹ️ Logs detalhados do agente estarão disponíveis em breve via WebSocket (PRD019).
                </small>
              </Alert>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setSelectedJob(null)}>
            Fechar
          </Button>
          {selectedJob?.worktree_path && (
            <Button
              variant="primary"
              onClick={() => {
                setSelectedJob(null)
                window.location.href = '/worktrees'
              }}
            >
              Ver Worktrees →
            </Button>
          )}
        </Modal.Footer>
      </Modal>
    </div>
  )
}
