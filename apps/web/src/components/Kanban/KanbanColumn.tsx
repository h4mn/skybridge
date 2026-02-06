import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { Card, Badge } from 'react-bootstrap'
import { KanbanDbCard, KanbanDbList } from '../../api/endpoints'
import { SortableCard } from './SortableCard'

interface KanbanColumnProps {
  list: KanbanDbList
  cards: KanbanDbCard[]
  onCardClick?: (card: KanbanDbCard) => void
}

/**
 * Componente de coluna Kanban com suporte a drop zone.
 *
 * Features:
 * - Droppable via @dnd-kit
 * - SortableContext para ordenar cards dentro da coluna
 * - Contador de cards
 */
export function KanbanColumn({ list, cards, onCardClick }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: list.id,
    data: { list },
  })

  // Cores para cada lista (baseado no nome)
  const getColor = (name: string): string => {
    const colors: Record<string, string> = {
      'Issues': 'secondary',
      'Brainstorm': 'info',
      'A Fazer': 'primary',
      'Em Andamento': 'warning',
      'Em Revisão': 'danger',
      'Publicar': 'success',
    }
    return colors[name] || 'secondary'
  }

  // Emojis para cada lista
  const getEmoji = (name: string): string => {
    const emojis: Record<string, string> = {
      'Issues': '📥',
      'Brainstorm': '🧠',
      'A Fazer': '📋',
      'Em Andamento': '🚧',
      'Em Revisão': '👀',
      'Publicar': '🚀',
    }
    return emojis[name] || '📋'
  }

  const color = getColor(list.name)
  const emoji = getEmoji(list.name)

  return (
    <div
      ref={setNodeRef}
      className={`kanban-column ${isOver ? 'kanban-column-over' : ''}`}
      style={{
        minHeight: '200px',
        padding: '8px',
      }}
    >
      <Card className="h-100 kanban-column-card">
        <Card.Header
          className={`bg-${color} text-white d-flex justify-content-between align-items-center`}
          style={{ cursor: 'default' }}
        >
          <span>
            {emoji} {list.name}
          </span>
          <Badge bg="white" text={color}>
            {cards.length}
          </Badge>
        </Card.Header>
        <Card.Body className="p-2 kanban-cards-container d-flex flex-column gap-2">
          {cards.length === 0 ? (
            <div className="text-center text-muted py-4 small kanban-empty">
              Arraste cards para cá
            </div>
          ) : (
            <SortableContext items={cards.map(c => c.id)} strategy={verticalListSortingStrategy}>
              {cards.map((card) => (
                <SortableCard
                  key={card.id}
                  card={card}
                  onClick={onCardClick}
                />
              ))}
            </SortableContext>
          )}
        </Card.Body>
      </Card>
    </div>
  )
}
