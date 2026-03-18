import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import { useMemo, useState, useEffect, useCallback } from 'react'
import { Container, Row, Alert } from 'react-bootstrap'
import { KanbanDbCard, KanbanDbList, kanbanDbApi } from '../../api/endpoints'
import { KanbanColumn } from './KanbanColumn'
import { KanbanCard } from './KanbanCard'
import { useKanbanSSE } from './useKanbanSSE'

interface KanbanBoardProps {
  onCardClick?: (card: KanbanDbCard) => void
}

/**
 * Componente principal do board Kanban com drag & drop.
 *
 * Features:
 * - Carrega lists e cards da API kanban.db
 * - Drag & drop entre colunas (mover cards)
 * - Cards vivos (being_processed) ordenados primeiro
 * - Cards vivos têm visual especial (borda pulsante)
 * - SSE para atualizações em tempo real (PRD024 Task 7)
 */
export function KanbanBoard({ onCardClick }: KanbanBoardProps) {
  const [lists, setLists] = useState<KanbanDbList[]>([])
  const [cards, setCards] = useState<KanbanDbCard[]>([])
  const [activeCard, setActiveCard] = useState<KanbanDbCard | null>(null)
  const [sseError, setSseError] = useState<string | null>(null)
  const [initialLoadDone, setInitialLoadDone] = useState(false)

  // Sensors para drag & drop
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px de movimento antes de iniciar drag
      },
    })
  )

  // Agrupa cards por lista
  const cardsByList = useMemo(() => {
    const grouped = new Map<string, KanbanDbCard[]>()
    lists.forEach(list => grouped.set(list.id, []))

    // Ordena: cards vivos primeiro (being_processed DESC), depois por position
    const sortedCards = [...cards].sort((a, b) => {
      // Cards vivos sempre primeiro
      if (a.being_processed && !b.being_processed) return -1
      if (!a.being_processed && b.being_processed) return 1

      // Depois por position
      return a.position - b.position
    })

    sortedCards.forEach(card => {
      const list = grouped.get(card.list_id)
      if (list) {
        list.push(card)
      }
    })

    return grouped
  }, [lists, cards])

  // Carrega dados ao montar
  useEffect(() => {
    const loadData = async () => {
      try {
        const [listsRes, cardsRes] = await Promise.all([
          kanbanDbApi.getLists(),
          kanbanDbApi.getCards(),
        ])

        setLists(listsRes.data)
        setCards(cardsRes.data)
        setInitialLoadDone(true)
      } catch (error) {
        console.error('Erro ao carregar Kanban:', error)
      }
    }

    loadData()
  }, [])

  // Helper para comparar timestamps - previne race condition SSE vs atualização local
  const isNewerThan = (localTimestamp: string, remoteTimestamp: string): boolean => {
    const localTime = new Date(localTimestamp).getTime()
    const remoteTime = new Date(remoteTimestamp).getTime()
    return remoteTime > localTime
  }

  // Helper para mover elemento no array (arrayMove do @dnd-kit)
  const arrayMove = <T,>(array: T[], from: number, to: number): T[] => {
    const newArray = [...array]
    const element = newArray[from]
    newArray.splice(from, 1)
    newArray.splice(to, 0, element)
    return newArray
  }

  // Handlers SSE para atualizações em tempo real
  const handleCardSnapshot = useCallback((card: KanbanDbCard) => {
    // Durante carregamento inicial via SSE, adiciona card se não existe
    setCards(prev => {
      if (prev.some(c => c.id === card.id)) {
        return prev.map(c => c.id === card.id ? card : c)
      }
      return [...prev, card]
    })
  }, [])

  const handleCardUpdated = useCallback((card: KanbanDbCard) => {
    setCards(prevCards =>
      prevCards.map(c => {
        if (c.id !== card.id) return c

        // Compara timestamps - só aceita SSE se for mais recente que o local
        // Previne race condition onde SSE desatualizado reverte atualização local
        if (!isNewerThan(c.updated_at, card.updated_at)) {
          return c // Ignora dado desatualizado do SSE
        }

        return { ...c, ...card }
      })
    )
  }, [])

  const handleCardCreated = useCallback((card: KanbanDbCard) => {
    setCards(prevCards => [...prevCards, card])
  }, [])

  const handleCardDeleted = useCallback((cardId: string) => {
    setCards(prevCards => prevCards.filter(c => c.id !== cardId))
  }, [])

  const handleProcessingStarted = useCallback((card: KanbanDbCard) => {
    setCards(prevCards =>
      prevCards.map(c =>
        c.id === card.id
          ? { ...c, being_processed: true, processing_started_at: card.processing_started_at, processing_job_id: card.processing_job_id }
          : c
      )
    )
  }, [])

  const handleProcessingCompleted = useCallback((card: KanbanDbCard) => {
    setCards(prevCards =>
      prevCards.map(c =>
        c.id === card.id
          ? { ...c, being_processed: false, processing_step: card.processing_step, processing_total_steps: card.processing_total_steps }
          : c
      )
    )
  }, [])

  const handleSseError = useCallback((error: string) => {
    console.error('[KanbanBoard] Erro SSE:', error)
    setSseError(error)
    // Limpa erro após 5 segundos
    setTimeout(() => setSseError(null), 5000)
  }, [])

  // Conecta ao SSE após carregamento inicial
  useKanbanSSE({
    workspace: 'core', // TODO: pegar workspace ativo do contexto
    onCardSnapshot: initialLoadDone ? undefined : handleCardSnapshot,
    onCardCreated: handleCardCreated,
    onCardUpdated: handleCardUpdated,
    onCardDeleted: handleCardDeleted,
    onProcessingStarted: handleProcessingStarted,
    onProcessingCompleted: handleProcessingCompleted,
    onError: handleSseError,
  })

  // Handler para início de drag
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event

    // Encontra o card sendo arrastado
    const card = cards.find(c => c.id === active.id)
    setActiveCard(card || null)
  }

  // Handler para fim de drag
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    setActiveCard(null)

    if (!over) {
      return
    }

    const activeCard = cards.find(c => c.id === active.id)
    if (!activeCard) {
      return
    }

    const targetListId = over.id as string

    // Verifica se é movimento entre listas ou reordenação na mesma lista
    const isSameList = activeCard.list_id === targetListId

    if (isSameList) {
      // REORDENAÇÃO NA MESMA LISTA (Task 10 PRD024)
      await handleReorder(event, activeCard)
    } else {
      // MOVIMENTO ENTRE LISTAS
      await handleMoveToList(activeCard.id, targetListId)
    }
  }

  // Move card para outra lista
  const handleMoveToList = async (cardId: string, targetListId: string) => {
    try {
      const updatedCard = await kanbanDbApi.updateCard(cardId, {
        list_id: targetListId,
      })

      // Atualiza estado local
      setCards(prevCards =>
        prevCards.map(c =>
          c.id === cardId ? updatedCard.data : c
        )
      )
    } catch (error) {
      console.error('Erro ao mover card:', error)
    }
  }

  // Reordena cards dentro da mesma lista (Task 10 PRD024)
  const handleReorder = async (event: DragEndEvent, activeCard: KanbanDbCard) => {
    const { active, over } = event
    if (!over) return

    // Pega cards da mesma lista ordenados por position
    const listCards = cards
      .filter(c => c.list_id === activeCard.list_id)
      .sort((a, b) => a.position - b.position)

    // Encontra índices
    const oldIndex = listCards.findIndex(c => c.id === active.id)
    const newIndex = listCards.findIndex(c => c.id === over.id)

    // Se não mudou de posição, nada a fazer
    if (oldIndex === newIndex) {
      return
    }

    // Reordena usando arrayMove
    const newOrder = arrayMove(listCards, oldIndex, newIndex)

    // Atualiza posições (começando do menor position existente)
    const basePosition = listCards[0]?.position || 0
    const updates = newOrder.map((card: KanbanDbCard, index: number) => ({
      id: card.id,
      position: basePosition + index,
    }))

    // Envia atualizações em paralelo
    try {
      await Promise.all(
        updates.map((u: { id: string; position: number }) =>
          kanbanDbApi.updateCard(u.id, { position: u.position })
        )
      )

      // Atualiza estado local otimista
      setCards(prevCards =>
        prevCards.map((prevCard: KanbanDbCard) => {
          const update = updates.find((u: { id: string; position: number }) => u.id === prevCard.id)
          return update ? { ...prevCard, position: update.position } : prevCard
        })
      )
    } catch (error) {
      console.error('Erro ao reordenar cards:', error)
      // TODO: Mostrar erro ao usuário
    }
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <Container fluid className="px-0">
        {/* Alerta de erro SSE */}
        {sseError && (
          <Alert variant="warning" className="mb-3" dismissible onClose={() => setSseError(null)}>
            <small>⚠️ Erro de conexão SSE: {sseError}</small>
          </Alert>
        )}

        <Row className="g-3">
          {lists.map((list) => {
            const listCards = cardsByList.get(list.id) || []

            return (
              <div key={list.id} style={{ flex: '1 0 0', minWidth: '280px', maxWidth: '400px' }}>
                <KanbanColumn
                  list={list}
                  cards={listCards}
                  onCardClick={onCardClick}
                />
              </div>
            )
          })}
        </Row>
      </Container>

      {/* Drag overlay - mostra card enquanto arrasta */}
      <DragOverlay>
        {activeCard ? (
          <div style={{ opacity: 0.8, cursor: 'grabbing' }}>
            <KanbanCard card={activeCard} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}
