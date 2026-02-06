import { useDraggable } from '@dnd-kit/core'
import { Card as BootstrapCard } from 'react-bootstrap'
import { KanbanDbCard } from '../../api/endpoints'

interface KanbanCardProps {
  card: KanbanDbCard
  onClick?: (card: KanbanDbCard) => void
}

/**
 * Componente de card Kanban individual com suporte a drag & drop.
 *
 * Features:
 * - Draggable via @dnd-kit
 * - Cards vivos (being_processed) com borda pulsante azul
 * - Badge de progresso para cards sendo processados
 */
export function KanbanCard({ card, onClick }: KanbanCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
    data: { card },
  })

  const isAlive = card.being_processed

  // Estilo inline para transformação de drag
  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.5 : 1,
      }
    : undefined

  // Classes condicionais para card vivo
  const cardClasses = [
    'kanban-card',
    'h-100',
    isAlive && 'kanban-card-alive',
    isDragging && 'kanban-card-dragging',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={() => onClick?.(card)}
      className={cardClasses}
    >
      <BootstrapCard className="h-100" style={{ cursor: 'grab', minHeight: '80px' }}>
        <BootstrapCard.Body className="p-3">
          {/* Badge de card vivo */}
          {isAlive && (
            <div className="kanban-live-badge mb-2">
              <span className="live-badge-icon">🤖</span>
              <span className="live-badge-text">Agent working...</span>
              {card.processing_total_steps > 0 && (
                <>
                  <div className="progress progress-sm mt-1" style={{ height: '4px' }}>
                    <div
                      className="progress-bar progress-bar-striped progress-bar-animated bg-primary"
                      role="progressbar"
                      style={{ width: `${card.processing_progress_percent}%` }}
                    />
                  </div>
                  <small className="text-muted">
                    {card.processing_step}/{card.processing_total_steps}
                  </small>
                </>
              )}
            </div>
          )}

          {/* Título do card */}
          <BootstrapCard.Text className="mb-2 text-dark fw-semibold text-truncate" title={card.title}>
            {card.title}
          </BootstrapCard.Text>

          {/* Descrição */}
          {card.description && (
            <BootstrapCard.Text className="mb-2 text-muted small text-truncate" title={card.description}>
              {card.description}
            </BootstrapCard.Text>
          )}

          {/* Labels */}
          {card.labels.length > 0 && (
            <div className="mb-2 d-flex flex-wrap gap-1">
              {card.labels.map((label: string) => (
                <span key={label} className="badge bg-light text-dark small">
                  {label}
                </span>
              ))}
            </div>
          )}

          {/* Footer com data de vencimento */}
          <div className="d-flex justify-content-between align-items-center mt-2">
            {card.due_date && (
              <small className={isOverdue(card.due_date) ? 'text-danger' : 'text-muted'}>
                📅 {formatDate(card.due_date)}
              </small>
            )}
            {card.issue_url && (
              <a
                href={card.issue_url}
                target="_blank"
                rel="noopener noreferrer"
                className="small text-muted"
                onClick={(e) => e.stopPropagation()}
              >
                #{card.issue_number}
              </a>
            )}
          </div>

          {/* PR Link */}
          {card.pr_url && (
            <div className="mt-1">
              <a
                href={card.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="small text-success"
                onClick={(e) => e.stopPropagation()}
              >
                🔗 PR
              </a>
            </div>
          )}
        </BootstrapCard.Body>
      </BootstrapCard>
    </div>
  )
}

// ============================================================================
// Helpers
// ============================================================================

function isOverdue(dateString: string): boolean {
  const date = new Date(dateString)
  return date < new Date()
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}
