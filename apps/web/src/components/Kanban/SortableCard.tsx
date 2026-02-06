import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { KanbanDbCard } from '../../api/endpoints'
import { KanbanCard } from './KanbanCard'

interface SortableCardProps {
  card: KanbanDbCard
  onClick?: (card: KanbanDbCard) => void
}

/**
 * Wrapper sortable para KanbanCard.
 *
 * Usa useSortable do @dnd-kit para permitir que cards
 * sejam reordenados dentro de uma coluna.
 */
export function SortableCard({ card, onClick }: SortableCardProps) {
  const {
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: card.id,
    data: { card },
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style}>
      <KanbanCard card={card} onClick={onClick} />
    </div>
  )
}
