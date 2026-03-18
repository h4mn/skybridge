import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Table,
  Button,
  Badge,
  Spinner,
  Alert,
  Form,
  FormControl,
  InputGroup,
  Pagination,
  Accordion,
} from 'react-bootstrap'
import { agentsApi, AgentState, type AgentExecution } from '../api/endpoints'

/**
 * Página Agents - Lista e gerencia execuções de agentes.
 * PRD: Página de Agents (Agent Spawns)
 */
export default function Agents() {
  const [searchTerm, setSearchTerm] = useState('')
  const [stateFilter, setStateFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Query para execuções (sem auto-refresh - atualiza apenas sob demanda)
  const {
    data: executionsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['agent-executions'],
    queryFn: async () => {
      const res = await agentsApi.listExecutions()
      return res.data
    },
    // refetchInterval removido - atualiza apenas via botão ou interação
  })

  const executions = executionsData?.executions ?? []
  const metrics = executionsData?.metrics

  // Filtros
  const filteredExecutions = executions.filter((exec) => {
    const matchesSearch =
      searchTerm === '' ||
      exec.job_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      exec.skill.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesState =
      stateFilter === 'all' || exec.state === stateFilter

    return matchesSearch && matchesState
  })

  // Paginação
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredExecutions.slice(indexOfFirstItem, indexOfLastItem)
  const totalPages = Math.ceil(filteredExecutions.length / itemsPerPage)

  // Status badge helper
  const getStateBadge = (state: AgentState) => {
    switch (state) {
      case AgentState.COMPLETED:
        return 'success'
      case AgentState.FAILED:
      case AgentState.TIMED_OUT:
        return 'danger'
      case AgentState.RUNNING:
        return 'primary'
      case AgentState.CREATED:
        return 'secondary'
      default:
        return 'secondary'
    }
  }

  // Status icon helper
  const getStateIcon = (state: AgentState) => {
    switch (state) {
      case AgentState.COMPLETED:
        return '✅'
      case AgentState.FAILED:
        return '❌'
      case AgentState.TIMED_OUT:
        return '⏱️'
      case AgentState.RUNNING:
        return '⚙️'
      case AgentState.CREATED:
        return '⏳'
      default:
        return '❓'
    }
  }

  // Formata duração
  const formatDuration = (durationMs: number | null) => {
    if (durationMs === null) return '-'
    const seconds = Math.floor(durationMs / 1000)
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
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
        <h1 className="mb-0">🤖 Agents</h1>
        <Button variant="outline-primary" size="sm" onClick={() => refetch()}>
          🔄 Atualizar
        </Button>
      </div>

      {error && (
        <Alert variant="warning">
          Erro ao carregar execuções. Verifique se a API está rodando.
        </Alert>
      )}

      {/* Métricas Summary */}
      {metrics && (
        <Card className="mb-4 bg-light">
          <Card.Body>
            <div className="row text-center">
              <div className="col-md-2">
                <div className="text-muted small">Total</div>
                <div className="h4 mb-0">{metrics.total ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Criados</div>
                <div className="h4 mb-0 text-secondary">{metrics.created ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Executando</div>
                <div className="h4 mb-0 text-primary">{metrics.running ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Concluídos</div>
                <div className="h4 mb-0 text-success">{metrics.completed ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Falharam</div>
                <div className="h4 mb-0 text-danger">{metrics.failed ?? 0}</div>
              </div>
              <div className="col-md-2">
                <div className="text-muted small">Timeout</div>
                <div className="h4 mb-0 text-warning">{metrics.timed_out ?? 0}</div>
              </div>
            </div>
            {metrics.success_rate !== null && (
              <div className="text-center mt-2">
                <small className="text-muted">
                  Taxa de Sucesso: <strong>{metrics.success_rate.toFixed(1)}%</strong>
                </small>
              </div>
            )}
          </Card.Body>
        </Card>
      )}

      {/* Filtros */}
      <Card className="mb-4">
        <Card.Body>
          <div className="row g-3">
            <div className="col-md-6">
              <InputGroup>
                <FormControl
                  placeholder="Buscar por job_id ou skill..."
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
                value={stateFilter}
                onChange={(e) => {
                  setStateFilter(e.target.value)
                  setCurrentPage(1)
                }}
              >
                <option value="all">Todos os estados</option>
                <option value={AgentState.CREATED}>Criados</option>
                <option value={AgentState.RUNNING}>Executando</option>
                <option value={AgentState.COMPLETED}>Concluídos</option>
                <option value={AgentState.FAILED}>Falharam</option>
                <option value={AgentState.TIMED_OUT}>Timeout</option>
              </Form.Select>
            </div>
            <div className="col-md-3">
              <div className="text-muted pt-2">
                Mostrando {filteredExecutions.length} de {executions.length} execuções
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Tabela com Accordion para detalhes */}
      <Card>
        <Card.Body className="p-0">
          {isLoading ? (
            <div className="text-center py-5">
              <Spinner animation="border" />
              <p className="mt-3 text-muted">Carregando execuções...</p>
            </div>
          ) : filteredExecutions.length === 0 ? (
            <div className="text-center py-5 text-muted">
              {searchTerm || stateFilter !== 'all'
                ? 'Nenhuma execução encontrada com os filtros atuais.'
                : 'Nenhuma execução encontrada.'}
            </div>
          ) : (
            <>
              <Accordion defaultActiveKey="-1">
                {currentItems.map((exec) => (
                  <Accordion.Item
                    key={exec.job_id}
                    eventKey={exec.job_id}
                    className="border-0"
                  >
                    <Accordion.Header className="bg-hover-light">
                      <div className="d-flex w-100 align-items-center">
                        <div className="me-2">
                          <Badge bg={getStateBadge(exec.state)}>
                            {getStateIcon(exec.state)} {exec.state.toUpperCase()}
                          </Badge>
                        </div>
                        <div className="flex-grow-1">
                          <small className="text-primary" style={{ fontFamily: 'monospace' }}>
                            {exec.job_id.length > 30 ? exec.job_id.slice(0, 30) + '...' : exec.job_id}
                          </small>
                          <br />
                          <small className="text-muted">
                            {exec.skill} · {exec.agent_type}
                          </small>
                        </div>
                        <div className="text-end me-3">
                          <div>
                            <small className="text-muted">
                              {formatDuration(exec.duration_ms)}
                            </small>
                          </div>
                          <div>
                            <small className="text-muted" title={formatFullDate(exec.timestamps.created_at)}>
                              {formatRelativeTime(exec.timestamps.created_at)}
                            </small>
                          </div>
                        </div>
                      </div>
                    </Accordion.Header>
                    <Accordion.Body>
                      <AgentDetails execution={exec} />
                    </Accordion.Body>
                  </Accordion.Item>
                ))}
              </Accordion>

              {/* Paginação */}
              {totalPages > 1 && (
                <div className="d-flex justify-content-center mt-4 p-3 border-top">
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
    </div>
  )
}

/**
 * Componente para mostrar detalhes de uma execução expandida.
 */
function AgentDetails({ execution }: { execution: AgentExecution }) {
  const [showMessages, setShowMessages] = useState(false)
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [messages, setMessages] = useState<string[] | null>(null)

  const handleLoadMessages = async () => {
    if (messages) {
      setShowMessages(!showMessages)
      return
    }

    setMessagesLoading(true)
    try {
      const res = await agentsApi.getMessages(execution.job_id)
      setMessages(res.data.messages)
      setShowMessages(true)
    } catch (err) {
      console.error('Erro ao carregar mensagens:', err)
    } finally {
      setMessagesLoading(false)
    }
  }

  return (
    <div>
      <Table bordered size="sm" className="mb-3">
        <tbody>
          <tr>
            <th style={{ width: '140px' }}>Job ID</th>
            <td><code style={{ fontSize: '0.9em' }}>{execution.job_id}</code></td>
          </tr>
          <tr>
            <th>Estado</th>
            <td>
              <Badge bg={
                execution.state === AgentState.COMPLETED ? 'success' :
                execution.state === AgentState.FAILED ? 'danger' :
                execution.state === AgentState.RUNNING ? 'primary' :
                execution.state === AgentState.TIMED_OUT ? 'warning' : 'secondary'
              }>
                {execution.state.toUpperCase()}
              </Badge>
            </td>
          </tr>
          <tr>
            <th>Agente</th>
            <td><code>{execution.agent_type}</code></td>
          </tr>
          <tr>
            <th>Skill</th>
            <td><code>{execution.skill}</code></td>
          </tr>
          <tr>
            <th>Worktree</th>
            <td><code style={{ fontSize: '0.85em' }}>{execution.worktree_path}</code></td>
          </tr>
          <tr>
            <th>Duração</th>
            <td>
              {execution.duration_ms
                ? `${(execution.duration_ms / 1000).toFixed(2)}s`
                : '-'}
            </td>
          </tr>
          <tr>
            <th>Criado</th>
            <td>{new Date(execution.timestamps.created_at).toLocaleString('pt-BR')}</td>
          </tr>
          {execution.timestamps.started_at && (
            <tr>
              <th>Iniciado</th>
              <td>{new Date(execution.timestamps.started_at).toLocaleString('pt-BR')}</td>
            </tr>
          )}
          {execution.timestamps.completed_at && (
            <tr>
              <th>Concluído</th>
              <td>{new Date(execution.timestamps.completed_at).toLocaleString('pt-BR')}</td>
            </tr>
          )}
          {execution.error_message && (
            <tr>
              <th className="text-danger">Erro</th>
              <td className="text-danger"><small>{execution.error_message}</small></td>
            </tr>
          )}
        </tbody>
      </Table>

      {/* Result */}
      {execution.result && (
        <div className="mb-3">
          <h6 className="text-muted mb-2">Resultado</h6>
          <Card bg="light" className="mb-2">
            <Card.Body>
              <div className="row text-center">
                <div className="col-md-3">
                  <small className="text-muted d-block">Sucesso</small>
                  <strong className={execution.result.success ? 'text-success' : 'text-danger'}>
                    {execution.result.success ? '✅ Sim' : '❌ Não'}
                  </strong>
                </div>
                <div className="col-md-3">
                  <small className="text-muted d-block">Alterações</small>
                  <strong>{execution.result.changes_made ? '✅ Sim' : '❌ Não'}</strong>
                </div>
                <div className="col-md-3">
                  <small className="text-muted d-block">Arquivos</small>
                  <strong>
                    {execution.result.files_created.length + execution.result.files_modified.length}
                  </strong>
                </div>
                <div className="col-md-3">
                  <small className="text-muted d-block">Commit</small>
                  <strong>
                    {execution.result.commit_hash
                      ? <code style={{ fontSize: '0.85em' }}>{execution.result.commit_hash.slice(0, 8)}</code>
                      : '-'}
                  </strong>
                </div>
              </div>
              {execution.result.pr_url && (
                <div className="text-center mt-2">
                  <a href={execution.result.pr_url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-outline-primary">
                    🔗 Ver Pull Request
                  </a>
                </div>
              )}
            </Card.Body>
          </Card>
          {(execution.result.files_created.length > 0 || execution.result.files_modified.length > 0) && (
            <div>
              {execution.result.files_created.length > 0 && (
                <div className="mb-2">
                  <small className="text-muted">Criados:</small>
                  <ul className="mb-0 ps-3">
                    {execution.result.files_created.map((file, i) => (
                      <li key={i}><code style={{ fontSize: '0.85em' }}>{file}</code></li>
                    ))}
                  </ul>
                </div>
              )}
              {execution.result.files_modified.length > 0 && (
                <div>
                  <small className="text-muted">Modificados:</small>
                  <ul className="mb-0 ps-3">
                    {execution.result.files_modified.map((file, i) => (
                      <li key={i}><code style={{ fontSize: '0.85em' }}>{file}</code></li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Mensagens do stream */}
      <div>
        <Button
          variant="outline-secondary"
          size="sm"
          onClick={handleLoadMessages}
          disabled={messagesLoading}
        >
          {messagesLoading ? 'Carregando...' : showMessages ? '🔽 Ocultar mensagens' : '🔽 Ver mensagens do stream'}
        </Button>

        {showMessages && messages && (
          <Card bg="dark" className="mt-3">
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <pre
                className="mb-0 text-light"
                style={{
                  fontSize: '0.85rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {messages.length > 0 ? messages.join('\n') : '<sem mensagens>'}
              </pre>
            </Card.Body>
          </Card>
        )}
      </div>
    </div>
  )
}
