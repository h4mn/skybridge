import { useState, useEffect } from 'react'
import { Card, Table, Button, Badge, Form, FormControl, InputGroup, Pagination, Spinner } from 'react-bootstrap'
import apiClient from '../api/client'

interface LogEntry {
  timestamp: string
  level: string
  logger: string
  message: string
  message_html: string
}

interface LogFile {
  name: string
  size: number
  modified: string
}

interface LogFileResponse {
  ok: boolean
  entries: LogEntry[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export default function Logs() {
  const [logFiles, setLogFiles] = useState<LogFile[]>([])
  const [selectedFile, setSelectedFile] = useState<string>('')
  const [allLogs, setAllLogs] = useState<LogEntry[]>([]) // Todos os logs do backend
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [totalAvailable, setTotalAvailable] = useState(0) // Total de logs no backend
  const itemsPerPage = 50

  // Carrega lista de arquivos de log
  useEffect(() => {
    fetchLogFiles()
  }, [])

  // Carrega logs do arquivo selecionado - busca TODOS do backend
  useEffect(() => {
    if (selectedFile) {
      fetchAllLogs(selectedFile)
    }
  }, [selectedFile])

  // Filtra logs localmente por termo de busca e nível
  const filteredLogs = allLogs.filter(log => {
    const matchesLevel = levelFilter === 'all' || log.level.toLowerCase() === levelFilter.toLowerCase()
    const matchesSearch = searchTerm === '' ||
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.logger.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesLevel && matchesSearch
  })

  // Conta logs por nível (baseado nos logs filtrados)
  const countByLevel = filteredLogs.reduce((acc, log) => {
    const level = log.level.toUpperCase()
    acc[level] = (acc[level] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const getLevelBadge = (level: string) => {
    const l = level.toUpperCase()
    if (l === 'DEBUG') return 'secondary'
    if (l === 'INFO') return 'primary'
    if (l === 'WARNING') return 'warning'
    if (l === 'ERROR') return 'danger'
    if (l === 'CRITICAL') return 'danger'
    return 'secondary'
  }

  // Formata a data ISO para formato legível
  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate)
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Formata timestamp do log
  const formatLogTimestamp = (timestamp: string) => {
    // Formato esperado: 2026-01-25 15:18:02
    return timestamp
  }

  // Paginação APENAS no frontend (baseado nos logs filtrados)
  const totalFiltered = filteredLogs.length
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredLogs.slice(indexOfFirstItem, indexOfLastItem)
  const totalPages = Math.ceil(totalFiltered / itemsPerPage)

  // Reset para página 1 quando filtros mudam
  useEffect(() => {
    setCurrentPage(1)
  }, [levelFilter, searchTerm])

  const fetchLogFiles = async () => {
    try {
      const response = await apiClient.get<{ files: LogFile[] }>('/logs/files')
      setLogFiles(response.data.files || [])
      if (response.data.files && response.data.files.length > 0) {
        // Seleciona o arquivo mais recente por padrão
        setSelectedFile(response.data.files[0].name)
      }
    } catch (error) {
      console.error('Erro ao carregar arquivos de log:', error)
    }
  }

  // Busca TODOS os logs do backend (sem paginação ou com limite alto)
  const fetchAllLogs = async (filename: string) => {
    setIsLoading(true)
    try {
      // Usa um limite alto para buscar todos os logs
      const response = await apiClient.get<LogFileResponse>(`/logs/file/${filename}`, {
        params: { page: 1, per_page: 500 }
      })
      setAllLogs(response.data.entries || [])
      setTotalAvailable(response.data.total || 0)
    } catch (error) {
      console.error('Erro ao carregar logs:', error)
      setAllLogs([])
      setTotalAvailable(0)
    } finally {
      setIsLoading(false)
    }
  }

  // Recarrega logs (mantém arquivo atual)
  const handleRefresh = () => {
    if (selectedFile) {
      fetchAllLogs(selectedFile)
    }
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="mb-0">📋 Logs do Sistema</h1>
        <Button variant="outline-primary" size="sm" onClick={handleRefresh}>
          🔄 Atualizar
        </Button>
      </div>

      {/* Seção de Arquivos de Log */}
      <Card className="mb-4">
        <Card.Header>Arquivos de Log</Card.Header>
        <Card.Body>
          {logFiles.length === 0 ? (
            <p className="text-muted">Nenhum arquivo de log encontrado.</p>
          ) : (
            <InputGroup>
              <Form.Select
                value={selectedFile}
                onChange={(e) => {
                  setSelectedFile(e.target.value)
                  setCurrentPage(1)
                }}
              >
                {logFiles.map(file => (
                  <option key={file.name} value={file.name}>
                    {file.name} - {formatDate(file.modified)}
                  </option>
                ))}
              </Form.Select>
            </InputGroup>
          )}
        </Card.Body>
      </Card>

      {/* Filtros e Estatísticas */}
      <Card className="mb-4">
        <Card.Body>
          <div className="row g-3">
            <div className="col-md-4">
              <InputGroup>
                <FormControl
                  placeholder="Buscar nos logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </InputGroup>
            </div>
            <div className="col-md-3">
              <Form.Select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
              >
                <option value="all">Todos os níveis</option>
                <option value="debug">DEBUG</option>
                <option value="info">INFO</option>
                <option value="warning">WARNING</option>
                <option value="error">ERROR</option>
                <option value="critical">CRITICAL</option>
              </Form.Select>
            </div>
            <div className="col-md-5">
              <div className="d-flex gap-2 align-items-center pt-2 flex-wrap">
                {Object.entries(countByLevel).map(([level, count]) => (
                  <Badge key={level} bg={getLevelBadge(level)} className="fs-6">
                    {level}: {count}
                  </Badge>
                ))}
                {totalAvailable > 0 && (
                  <Badge bg="info" className="fs-6">
                    Total: {totalAvailable}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Tabela de Logs */}
      <Card>
        <Card.Body className="p-0">
          {isLoading ? (
            <div className="text-center py-5">
              <Spinner animation="border" />
              <p className="mt-3 text-muted">Carregando logs...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-5 text-muted">
              {searchTerm || levelFilter !== 'all'
                ? 'Nenhum log encontrado com os filtros atuais.'
                : allLogs.length === 0
                  ? 'Nenhum log disponível neste arquivo.'
                  : 'Nenhum log corresponde aos filtros.'}
            </div>
          ) : (
            <>
              <Table hover responsive size="sm">
                <thead>
                  <tr>
                    <th style={{ width: '180px' }}>Timestamp</th>
                    <th style={{ width: '100px' }}>Nível</th>
                    <th>Logger</th>
                    <th>Mensagem</th>
                  </tr>
                </thead>
                <tbody>
                  {currentItems.map((log, idx) => {
                    const level = log.level.toUpperCase()
                    return (
                      <tr key={`${log.timestamp}-${idx}`}>
                        <td className="text-monospace" style={{ fontSize: '12px' }}>
                          {formatLogTimestamp(log.timestamp)}
                        </td>
                        <td>
                          <Badge bg={getLevelBadge(level)}>{level}</Badge>
                        </td>
                        <td className="text-monospace" style={{ fontSize: '11px' }}>
                          {log.logger}
                        </td>
                        <td
                          style={{ fontSize: '12px', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}
                          dangerouslySetInnerHTML={{ __html: log.message_html }}
                        />
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
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    />
                    <Pagination.Item active>{currentPage}</Pagination.Item>
                    <span className="align-self-center mx-2">de {totalPages}</span>
                    <Pagination.Next
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    />
                    <Pagination.Last
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                    />
                  </Pagination>
                </div>
              )}

              <div className="mt-3 text-muted small text-center">
                Mostrando {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, totalFiltered)} de {totalFiltered} logs
                {searchTerm || levelFilter !== 'all' ? ` (filtrado de ${totalAvailable} totais)` : ''}
              </div>
            </>
          )}
        </Card.Body>
      </Card>
    </div>
  )
}
