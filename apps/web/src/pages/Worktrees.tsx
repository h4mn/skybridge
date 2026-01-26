import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import { webhooksApi, type Worktree } from '../api/endpoints'

/**
 * Página Worktrees - Lista e gerencia worktrees.
 * Objetivo: RF002 - Tabela de Worktrees Ativos (Fase 3)
 * Segurança: Múltiplas camadas de proteção para deleção
 */
export default function Worktrees() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10
  const [expandedDiffs, setExpandedDiffs] = useState<Set<number>>(new Set())

  // Query para worktrees
  const {
    data: worktreesData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['worktrees'],
    queryFn: async () => {
      const res = await webhooksApi.listWorktrees()
      return res.data
    },
    refetchInterval: 10000, // Atualiza a cada 10s
  })

  // Mutation para deletar worktree (agora requer senha)
  const deleteMutation = useMutation({
    mutationFn: ({ name, password }: { name: string; password: string }) =>
      webhooksApi.deleteWorktree(name, password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worktrees'] })
      setShowDeleteConfirm(false)
      setWorktreeToDelete(null)
      setDeletePassword('')
      setConfirmationText('')
      setConfirmedChecked(false)
      setCountdown(5)
    },
  })

  // Modal states
  const [selectedWorktree, setSelectedWorktree] = useState<Worktree | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [worktreeToDelete, setWorktreeToDelete] = useState<Worktree | null>(null)

  // Delete confirmation states
  const [deletePassword, setDeletePassword] = useState('')
  const [confirmationText, setConfirmationText] = useState('')
  const [confirmedChecked, setConfirmedChecked] = useState(false)
  const [countdown, setCountdown] = useState(5)
  const [deleteError, setDeleteError] = useState('')

  const countdownRef = useRef<NodeJS.Timeout | null>(null)

  // Inicia contagem regressiva quando modal abre
  useEffect(() => {
    // Limpa interval anterior se existir
    if (countdownRef.current) {
      clearInterval(countdownRef.current)
      countdownRef.current = null
    }

    if (showDeleteConfirm) {
      setCountdown(5)
      setDeleteError('')

      countdownRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            // Limpa o interval quando chega a 0
            if (countdownRef.current) {
              clearInterval(countdownRef.current)
              countdownRef.current = null
            }
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }

    // Cleanup: garante que o interval é limpo ao desmontar ou re-executar
    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current)
        countdownRef.current = null
      }
    }
  }, [showDeleteConfirm])

  const worktrees = worktreesData?.worktrees ?? []

  // Filtros
  const filteredWorktrees = worktrees.filter((wt) => {
    const matchesSearch =
      searchTerm === '' ||
      wt.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      wt.path.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'unknown' && (!wt.status || wt.status === 'UNKNOWN')) ||
      wt.status === statusFilter.toUpperCase()

    return matchesSearch && matchesStatus
  })

  // Paginação
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredWorktrees.slice(indexOfFirstItem, indexOfLastItem)
  const totalPages = Math.ceil(filteredWorktrees.length / itemsPerPage)

  // Handlers
  const handleView = (worktree: Worktree) => {
    setSelectedWorktree(worktree)
  }

  const handleDelete = (worktree: Worktree) => {
    // Só permite deletar se status for COMPLETED ou FAILED
    if (worktree.status !== 'COMPLETED' && worktree.status !== 'FAILED') {
      return
    }
    setWorktreeToDelete(worktree)
    setShowDeleteConfirm(true)
  }

  const confirmDelete = () => {
    if (!worktreeToDelete) return

    // Validações
    if (!deletePassword) {
      setDeleteError('Senha é obrigatória')
      return
    }

    // Extrai hash final do nome (últimos 7 caracteres após o último hífen)
    const nameParts = worktreeToDelete.name.split('-')
    const expectedHash = nameParts[nameParts.length - 1]

    if (confirmationText !== expectedHash) {
      setDeleteError(`Hash incorreto. Digite: ${expectedHash}`)
      return
    }

    if (!confirmedChecked) {
      setDeleteError('Você deve confirmar que entende as consequências')
      return
    }

    // Tenta deletar
    deleteMutation.mutate({
      name: worktreeToDelete.name,
      password: deletePassword,
    })
  }

  const handleKeep = (worktree: Worktree) => {
    // TODO: Implementar "Keep" - marcar worktree para não limpar automaticamente
    alert(`Worktree ${worktree.name} marcado para preservar (em implementação)`)
  }

  const toggleDiff = (idx: number) => {
    setExpandedDiffs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(idx)) {
        newSet.delete(idx)
      } else {
        newSet.add(idx)
      }
      return newSet
    })
  }

  // Verifica se worktree pode ser deletado
  const canDelete = (status: string | undefined) => {
    return status === 'COMPLETED' || status === 'FAILED'
  }

  // Calcula diff entre snapshots
  const getSnapshotDiff = (snapshot: Record<string, unknown> | undefined) => {
    if (!snapshot) return null

    const initial = snapshot.initial as Record<string, unknown> | undefined
    const final = snapshot.final as Record<string, unknown> | undefined
    const validation = snapshot.validation as Record<string, unknown> | undefined

    if (!initial || !final) return null

    const initialStats = initial.stats as Record<string, unknown> | undefined
    const finalStats = final.stats as Record<string, unknown> | undefined

    if (!initialStats || !finalStats) return null

    const initialFiles = initialStats.files as number | undefined ?? 0
    const finalFiles = finalStats.files as number | undefined ?? 0
    const filesDiff = finalFiles - initialFiles

    const initialLines = initialStats.lines as number | undefined ?? 0
    const finalLines = finalStats.lines as number | undefined ?? 0
    const linesDiff = finalLines - initialLines

    const validationStatus = validation?.status as Record<string, unknown> | undefined
    const staged = validationStatus?.staged as number | undefined ?? 0
    const unstaged = validationStatus?.unstaged as number | undefined ?? 0
    const untracked = validationStatus?.untracked as number | undefined ?? 0

    return {
      files: { initial: initialFiles, final: finalFiles, diff: filesDiff },
      lines: { initial: initialLines, final: finalLines, diff: linesDiff },
      changes: { staged, unstaged, untracked },
    }
  }

  // Extrai dados de git_diff do snapshot
  const getGitDiffData = (snapshot: Record<string, unknown> | undefined) => {
    if (!snapshot) return null

    const gitDiff = snapshot.git_diff as Record<string, unknown> | undefined
    if (!gitDiff) return null

    const files = gitDiff.files as Array<Record<string, unknown>> | undefined
    const diffs = gitDiff.diffs as Record<string, string> | undefined
    const summary = gitDiff.summary as Record<string, unknown> | undefined

    return {
      files: files ?? [],
      diffs: diffs ?? {},
      summary: summary ?? {},
    }
  }

  // Retorna classe CSS baseada no status do arquivo
  const getFileStatusBadge = (status: string) => {
    const s = status.toUpperCase()
    if (s === 'A') return 'success'  // Added
    if (s === 'M' || s === 'MM') return 'warning'  // Modified
    if (s === 'D') return 'danger'  // Deleted
    if (s === 'R') return 'info'  // Renamed
    return 'secondary'
  }

  const getFileStatusLabel = (status: string) => {
    const s = status.toUpperCase()
    if (s === 'A') return 'Criado'
    if (s === 'M' || s === 'MM') return 'Alterado'
    if (s === 'D') return 'Excluído'
    if (s === 'R') return 'Renomeado'
    return s
  }

  // Status badge helper
  const getStatusBadge = (status: string | undefined) => {
    const s = status?.toUpperCase() || 'UNKNOWN'
    if (s === 'COMPLETED') return 'success'
    if (s === 'FAILED') return 'danger'
    if (s === 'PROCESSING' || s === 'PENDING') return 'primary'
    return 'secondary'
  }

  // Trunca caminho para exibição
  const truncatePath = (path: string, maxLength = 60) => {
    if (path.length <= maxLength) return path
    return '...' + path.slice(-(maxLength - 3))
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="mb-0">Worktrees</h1>
        <Button variant="outline-primary" size="sm" onClick={() => refetch()}>
          🔄 Atualizar
        </Button>
      </div>

      {error && (
        <Alert variant="warning">
          Erro ao carregar worktrees. Verifique se a API está rodando.
        </Alert>
      )}

      {/* Filtros */}
      <Card className="mb-4">
        <Card.Body>
          <div className="row g-3">
            <div className="col-md-6">
              <InputGroup>
                <FormControl
                  placeholder="Buscar por nome ou caminho..."
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
                <option value="completed">Completados</option>
                <option value="failed">Falharam</option>
                <option value="processing">Em processamento</option>
                <option value="unknown">Desconhecido</option>
              </Form.Select>
            </div>
            <div className="col-md-3">
              <div className="text-muted pt-2">
                Mostrando {filteredWorktrees.length} de {worktrees.length} worktrees
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
              <p className="mt-3 text-muted">Carregando worktrees...</p>
            </div>
          ) : filteredWorktrees.length === 0 ? (
            <div className="text-center py-5 text-muted">
              {searchTerm || statusFilter !== 'all'
                ? 'Nenhum worktree encontrado com os filtros atuais.'
                : 'Nenhum worktree encontrado.'}
            </div>
          ) : (
            <>
              <Table hover responsive>
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Status</th>
                    <th>Caminho</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {currentItems.map((wt) => {
                    const deletable = canDelete(wt.status)

                    return (
                      <tr key={wt.name}>
                        <td>
                          <code className="text-primary">{wt.name}</code>
                        </td>
                        <td>
                          <Badge bg={getStatusBadge(wt.status)}>
                            {wt.status || 'UNKNOWN'}
                          </Badge>
                        </td>
                        <td>
                          <small className="text-muted" title={wt.path}>
                            {truncatePath(wt.path)}
                          </small>
                        </td>
                        <td>
                          <Button
                            size="sm"
                            variant="outline-primary"
                            className="me-1"
                            onClick={() => handleView(wt)}
                            title="Ver detalhes"
                          >
                            👁️
                          </Button>
                          <Button
                            size="sm"
                            variant="outline-success"
                            className="me-1"
                            onClick={() => handleKeep(wt)}
                            title="Preservar (não limpar automaticamente)"
                          >
                            📌
                          </Button>
                          <Button
                            size="sm"
                            variant={deletable ? "outline-danger" : "outline-secondary"}
                            onClick={() => handleDelete(wt)}
                            title={deletable ? "Limpar worktree" : "Apenas worktrees COMPLETED ou FAILED podem ser deletados"}
                            disabled={!deletable}
                          >
                            🗑️
                          </Button>
                        </td>
                      </tr>
                    )
                  })}
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
        show={!!selectedWorktree}
        onHide={() => setSelectedWorktree(null)}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Detalhes do Worktree</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedWorktree && (
            <div>
              <Table bordered size="sm">
                <tbody>
                  <tr>
                    <th style={{ width: '120px' }}>Nome</th>
                    <td><code>{selectedWorktree.name}</code></td>
                  </tr>
                  <tr>
                    <th>Status</th>
                    <td>
                      <Badge bg={getStatusBadge(selectedWorktree.status)}>
                        {selectedWorktree.status || 'UNKNOWN'}
                      </Badge>
                    </td>
                  </tr>
                  <tr>
                    <th>Caminho</th>
                    <td><code>{selectedWorktree.path}</code></td>
                  </tr>
                </tbody>
              </Table>

              {/* Snapshot com diff */}
              {selectedWorktree.snapshot ? (
                <div className="mt-4">
                  <h6>Snapshot & Diff</h6>
                  {(() => {
                    const diff = getSnapshotDiff(selectedWorktree.snapshot)

                    if (!diff) {
                      return (
                        <Alert variant="info">
                          <small>Snapshot disponível mas sem estrutura de diff inicial/final.</small>
                          <pre className="bg-light p-3 rounded mt-2 mb-0">
                            <code>{JSON.stringify(selectedWorktree.snapshot, null, 2)}</code>
                          </pre>
                        </Alert>
                      )
                    }

                    return (
                      <div>
                        <Table size="sm" bordered>
                          <thead>
                            <tr>
                              <th>Métrica</th>
                              <th>Inicial</th>
                              <th>Final</th>
                              <th>Diff</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td>📄 Arquivos</td>
                              <td>{diff.files.initial}</td>
                              <td>{diff.files.final}</td>
                              <td className={diff.files.diff >= 0 ? 'text-success' : 'text-danger'}>
                                {diff.files.diff >= 0 ? '+' : ''}{diff.files.diff}
                              </td>
                            </tr>
                            <tr>
                              <td>📝 Linhas</td>
                              <td>{diff.lines.initial}</td>
                              <td>{diff.lines.final}</td>
                              <td className={diff.lines.diff >= 0 ? 'text-success' : 'text-danger'}>
                                {diff.lines.diff >= 0 ? '+' : ''}{diff.lines.diff}
                              </td>
                            </tr>
                          </tbody>
                        </Table>

                        <div className="mt-3">
                          <h6>Alterações por Estado</h6>
                          <div className="d-flex gap-3">
                            <Badge bg="success">Staged: {diff.changes.staged}</Badge>
                            <Badge bg="warning">Unstaged: {diff.changes.unstaged}</Badge>
                            <Badge bg="secondary">Untracked: {diff.changes.untracked}</Badge>
                          </div>
                        </div>

                        {/* Seção de Arquivos e Diffs */}
                        {(() => {
                          const gitDiffData = getGitDiffData(selectedWorktree.snapshot)
                          if (!gitDiffData || gitDiffData.files.length === 0) {
                            return (
                              <Alert variant="secondary" className="mt-3 mb-0">
                                <small>Nenhum arquivo alterado detectado.</small>
                              </Alert>
                            )
                          }

                          return (
                            <div className="mt-4">
                              <h6>📋 Arquivos Alterados</h6>

                              {/* Resumo */}
                              <div className="mb-3">
                                <div className="d-flex gap-2 flex-wrap">
                                  <Badge bg="success">
                                    ➕ Criados: {gitDiffData.summary.added ?? 0}
                                  </Badge>
                                  <Badge bg="warning">
                                    ✏️ Alterados: {gitDiffData.summary.modified ?? 0}
                                  </Badge>
                                  <Badge bg="danger">
                                    ➖ Excluídos: {gitDiffData.summary.deleted ?? 0}
                                  </Badge>
                                </div>
                              </div>

                              {/* Lista de arquivos com badges */}
                              <div className="mb-3">
                                {gitDiffData.files.map((file: Record<string, unknown>, idx: number) => {
                                  const path = file.path as string
                                  const status = file.status as string
                                  const hasDiff = gitDiffData.diffs[path]

                                  return (
                                    <div key={idx} className="d-flex align-items-center mb-2 p-2 bg-light rounded">
                                      <Badge bg={getFileStatusBadge(status)} className="me-2">
                                        {getFileStatusLabel(status)}
                                      </Badge>
                                      <code className="flex-grow-1 text-truncate">{path}</code>
                                      {hasDiff && (
                                        <Button
                                          size="sm"
                                          variant="outline-secondary"
                                          className="ms-2"
                                          onClick={() => toggleDiff(idx)}
                                        >
                                          📝 Ver diff
                                        </Button>
                                      )}
                                    </div>
                                  )
                                })}
                              </div>

                              {/* Diffs expandíveis */}
                              {gitDiffData.files.map((file: Record<string, unknown>, idx: number) => {
                                const path = file.path as string
                                const diffContent = gitDiffData.diffs[path]

                                if (!diffContent) return null

                                return (
                                  <details
                                    key={`diff-${idx}`}
                                    open={expandedDiffs.has(idx)}
                                    className="mt-2"
                                  >
                                    <summary className="cursor-pointer fw-bold" onClick={(e) => {
                                      e.preventDefault()
                                      toggleDiff(idx)
                                    }}>
                                      Diff: {path}
                                    </summary>
                                    <pre className="bg-dark text-light p-3 rounded mt-2 mb-0" style={{
                                      maxHeight: '400px',
                                      overflow: 'auto',
                                      fontSize: '12px',
                                      lineHeight: '1.4'
                                    }}>
                                      <code style={{ color: '#f8f8f2' }}>{diffContent}</code>
                                    </pre>
                                  </details>
                                )
                              })}
                            </div>
                          )
                        })()}

                        <details className="mt-3">
                          <summary style={{ cursor: 'pointer' }}>Ver JSON completo</summary>
                          <pre className="bg-light p-3 rounded mt-2">
                            <code>{JSON.stringify(selectedWorktree.snapshot, null, 2)}</code>
                          </pre>
                        </details>
                      </div>
                    )
                  })()}
                </div>
              ) : (
                <Alert variant="info" className="mt-4">
                  Nenhum snapshot disponível para este worktree.
                </Alert>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setSelectedWorktree(null)}>
            Fechar
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Modal de Confirmação de Exclusão MELHORADO */}
      <Modal show={showDeleteConfirm} onHide={() => setShowDeleteConfirm(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            <span className="text-danger">⚠️ Confirmar Exclusão</span>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {worktreeToDelete && (
            <div>
              <Alert variant="danger">
                <strong>ATENÇÃO:</strong> Você está prestes a deletar dados reais do disco!
                <br /><br />
                Worktree: <code>{worktreeToDelete.name}</code>
                <br />
                Caminho: <code>{worktreeToDelete.path}</code>
                <br /><br />
                ⚠️ Esta ação <strong>NÃO pode ser desfeita</strong>.
              </Alert>

              <Form className="mt-4">
                {/* 1. Senha */}
                <Form.Group className="mb-3">
                  <Form.Label>Senha de Deleção</Form.Label>
                  <Form.Control
                    type="password"
                    placeholder="Digite a senha configurada em WEBUI_DELETE_PASSWORD"
                    value={deletePassword}
                    onChange={(e) => {
                      setDeletePassword(e.target.value)
                      setDeleteError('')
                    }}
                    isInvalid={!!deleteError}
                  />
                  <Form.Text className="text-muted">
                    Senha obrigatória para deletar worktrees (configure em .env)
                  </Form.Text>
                </Form.Group>

                {/* 2. Confirmar digitando hash final */}
                <Form.Group className="mb-3">
                  <Form.Label>
                    Confirme digitando o hash final do nome: <code className="bg-light px-2 py-1">
                      {worktreeToDelete.name.split('-').pop()}
                    </code>
                  </Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Digite o hash acima para confirmar"
                    value={confirmationText}
                    onChange={(e) => {
                      setConfirmationText(e.target.value)
                      setDeleteError('')
                    }}
                    isInvalid={!!deleteError && !deletePassword}
                  />
                  <Form.Text className="text-muted">
                    Últimos 7 caracteres após o último hífen
                  </Form.Text>
                </Form.Group>

                {/* 3. Checkbox de confirmação */}
                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Entendo que esta ação não pode ser desfeita e que os dados serão perdidos permanentemente"
                    checked={confirmedChecked}
                    onChange={(e) => {
                      setConfirmedChecked(e.target.checked)
                      setDeleteError('')
                    }}
                    isInvalid={!!deleteError && !confirmationText && !deletePassword}
                  />
                </Form.Group>

                {/* Mensagem de erro */}
                {deleteError && (
                  <Alert variant="danger" className="mb-0">
                    {deleteError}
                  </Alert>
                )}

                {/* Informações adicionais */}
                <div className="mt-3 p-3 bg-light rounded">
                  <small className="text-muted">
                    <strong>Status atual:</strong> <Badge bg={getStatusBadge(worktreeToDelete.status)}>{worktreeToDelete.status || 'UNKNOWN'}</Badge>
                    <br />
                    <strong>Regra:</strong> Apenas worktrees com status <Badge bg="success">COMPLETED</Badge> ou <Badge bg="danger">FAILED</Badge> podem ser deletados.
                  </small>
                </div>
              </Form>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteConfirm(false)}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            onClick={confirmDelete}
            disabled={
              countdown > 0 ||
              deleteMutation.isPending ||
              !deletePassword ||
              !confirmationText ||
              !confirmedChecked
            }
          >
            {deleteMutation.isPending
              ? 'Excluindo...'
              : countdown > 0
              ? `Aguarde ${countdown}s...`
              : 'Confirmar Exclusão'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  )
}
