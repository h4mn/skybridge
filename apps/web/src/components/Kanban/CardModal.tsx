import { Modal, Button, Badge, Spinner } from 'react-bootstrap'
import { useState, useEffect } from 'react'
import { KanbanDbCard, CardHistory, kanbanDbApi } from '../../api/endpoints'

interface CardModalProps {
  card: KanbanDbCard
  show: boolean
  onClose: () => void
  onEdit?: (card: KanbanDbCard) => void
}

/**
 * Modal de Detalhes do Card Kanban.
 *
 * DOC: PRD024 Task 8 - Modal de Detalhes do Card
 * DOC: ADR024 - Workspace isolation
 *
 * Features:
 * - Mostra título, descrição, labels, due_date
 * - Mostra informações de processamento (se being_processed)
 * - Links para issue/PR do GitHub
 * - Histórico de movimentos e eventos do card
 * - Botão para editar card
 */
export function CardModal({ card, show, onClose, onEdit }: CardModalProps) {
  const [history, setHistory] = useState<CardHistory[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const isAlive = card.being_processed

  // Carrega histórico quando modal abre
  useEffect(() => {
    if (show) {
      loadHistory()
    }
  }, [show, card.id])

  const loadHistory = async () => {
    setHistoryLoading(true)
    setHistoryError(null)
    try {
      const response = await kanbanDbApi.getCardHistory(card.id)
      setHistory(response.data)
    } catch (error) {
      console.error('Erro ao carregar histórico:', error)
      setHistoryError('Não foi possível carregar o histórico')
    } finally {
      setHistoryLoading(false)
    }
  }

  // Formata evento para exibição
  const formatEvent = (historyItem: CardHistory): { text: string; icon: string; variant: string } => {
    const { event, from_list_id, to_list_id } = historyItem

    switch (event) {
      case 'created':
        return { text: 'Card criado', icon: '✨', variant: 'success' }
      case 'moved':
        return {
          text: `Movido de ${from_list_id || '?'} para ${to_list_id || '?'}`,
          icon: '↔️',
          variant: 'info'
        }
      case 'processing_started':
        return { text: 'Processamento iniciado', icon: '🤖', variant: 'primary' }
      case 'processing_completed':
        return { text: 'Processamento concluído', icon: '✅', variant: 'success' }
      case 'updated':
        return { text: 'Card atualizado', icon: '✏️', variant: 'secondary' }
      case 'deleted':
        return { text: 'Card deletado', icon: '🗑️', variant: 'danger' }
      default:
        return { text: event, icon: '📌', variant: 'light' }
    }
  }

  // Formata data de vencimento
  const formatDueDate = (dateString: string | null) => {
    if (!dateString) return null
    const date = new Date(dateString)
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }

  // Verifica se data está atrasada
  const isOverdue = (dateString: string | null) => {
    if (!dateString) return false
    const date = new Date(dateString)
    return date < new Date()
  }

  const dueDateFormatted = formatDueDate(card.due_date)
  const isDueDateOverdue = isOverdue(card.due_date)

  return (
    <Modal
      show={show}
      onHide={onClose}
      size="lg"
      aria-labelledby="card-modal-title"
      centered
    >
      <Modal.Header closeButton>
        <Modal.Title id="card-modal-title" className="d-flex align-items-center gap-2">
          {isAlive && (
            <span className="text-primary" role="img" aria-label="Card sendo processado">
              🤖
            </span>
          )}
          <span>{card.title}</span>
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {/* Badge de card vivo */}
        {isAlive && (
          <div className="mb-3 p-2 bg-primary bg-opacity-10 border border-primary rounded">
            <div className="d-flex align-items-center gap-2 mb-2">
              <span role="img" aria-label="Robô">🤖</span>
              <strong className="text-primary">Agent working...</strong>
            </div>
            {card.processing_total_steps > 0 && (
              <div className="d-flex align-items-center gap-2">
                <div className="flex-grow-1 progress" style={{ height: '6px' }}>
                  <div
                    className="progress-bar progress-bar-striped progress-bar-animated"
                    role="progressbar"
                    style={{ width: `${card.processing_progress_percent}%` }}
                    aria-valuenow={card.processing_step}
                    aria-valuemin={0}
                    aria-valuemax={card.processing_total_steps}
                  />
                </div>
                <small className="text-muted">
                  {card.processing_step}/{card.processing_total_steps}
                </small>
              </div>
            )}
            {card.processing_job_id && (
              <small className="text-muted d-block mt-1">
                Job: <code>{card.processing_job_id}</code>
              </small>
            )}
          </div>
        )}

        {/* Descrição */}
        {card.description && (
          <div className="mb-3">
            <h6 className="text-muted mb-2">Descrição</h6>
            <p className="mb-0">{card.description}</p>
          </div>
        )}

        {/* Labels */}
        {card.labels.length > 0 && (
          <div className="mb-3">
            <h6 className="text-muted mb-2">Labels</h6>
            <div className="d-flex gap-2 flex-wrap">
              {card.labels.map((label) => (
                <Badge key={label} bg="light" text="dark" className="text-capitalize">
                  {label}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Data de vencimento */}
        {dueDateFormatted && (
          <div className="mb-3">
            <h6 className="text-muted mb-2">Data de Vencimento</h6>
            <span className={isDueDateOverdue ? 'text-danger fw-semibold' : 'text-muted'}>
              📅 {dueDateFormatted}
            </span>
          </div>
        )}

        {/* Links do GitHub */}
        {(card.issue_url || card.pr_url) && (
          <div className="mb-3">
            <h6 className="text-muted mb-2">GitHub</h6>
            <div className="d-flex flex-column gap-2">
              {card.issue_url && (
                <div>
                  <a
                    href={card.issue_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-decoration-none"
                    aria-label={`Issue #${card.issue_number}`}
                  >
                    🔗 Issue #{card.issue_number}
                  </a>
                </div>
              )}
              {card.pr_url && (
                <div>
                  <a
                    href={card.pr_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-decoration-none text-success"
                    aria-label="Pull Request"
                  >
                    🔗 Pull Request
                  </a>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Histórico do Card */}
        <div className="mb-3">
          <h6 className="text-muted mb-2 d-flex align-items-center gap-2">
            📜 Histórico
            {historyLoading && <Spinner animation="border" size="sm" />}
          </h6>
          {historyError && (
            <small className="text-danger">{historyError}</small>
          )}
          {!historyLoading && history.length === 0 && (
            <small className="text-muted">Nenhum evento registrado</small>
          )}
          {!historyLoading && history.length > 0 && (
            <div className="border rounded p-2 bg-light" style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {history.map((item) => {
                const { text, icon, variant } = formatEvent(item)
                return (
                  <div key={item.id} className="d-flex align-items-start gap-2 mb-2" style={{ fontSize: '0.875rem' }}>
                    <span style={{ minWidth: '20px' }}>{icon}</span>
                    <div className="flex-grow-1">
                      <span className={`badge bg-${variant} mb-1`}>{text}</span>
                      <div className="text-muted small" style={{ fontSize: '0.75rem' }}>
                        {new Date(item.created_at).toLocaleString('pt-BR')}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Metadados */}
        <div className="text-muted small">
          <div>ID: <code>{card.id}</code></div>
          <div>Lista: <code>{card.list_id}</code></div>
          <div>Criado em: {new Date(card.created_at).toLocaleDateString('pt-BR')}</div>
          {card.updated_at !== card.created_at && (
            <div>Atualizado em: {new Date(card.updated_at).toLocaleDateString('pt-BR')}</div>
          )}
        </div>
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Fechar
        </Button>
        {onEdit && (
          <Button variant="primary" onClick={() => onEdit(card)}>
            Editar Card
          </Button>
        )}
      </Modal.Footer>
    </Modal>
  )
}
