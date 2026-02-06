import { useState } from 'react'
import { KanbanBoard, CardModal, CreateCardModal } from '../components/Kanban'
import { KanbanDbCard as Card } from '../api/endpoints'
import './KanbanPage.css'

/**
 * Página Kanban - Visualização interativa do board (Fase 2).
 *
 * Fase 2: kanban.db como fonte única da verdade
 * - Carrega boards/lists/cards via API /kanban/*
 * - Drag & drop entre colunas (mover cards)
 * - Cards vivos com borda pulsante azul
 * - Respeita workspace ativo (ADR024)
 *
 * DOC: PRD024 - Kanban Cards Vivos
 * DOC: ADR024 - Workspace isolation via X-Workspace header
 */
export default function Kanban() {
  const [selectedCard, setSelectedCard] = useState<Card | null>(null)
  const [showCardModal, setShowCardModal] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Handler para clique no card
  const handleCardClick = (card: Card) => {
    setSelectedCard(card)
    setShowCardModal(true)
  }

  // Handler para fechar modal
  const handleCloseModal = () => {
    setShowCardModal(false)
    setSelectedCard(null)
  }

  // Handler para editar card
  const handleEditCard = (card: Card) => {
    // TODO: Implementar edição de card (Task 9)
    console.log('Editar card:', card)
    handleCloseModal()
  }

  return (
    <div className="p-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="mb-0">📋 Kanban - Skybridge</h2>
        <div className="d-flex gap-2">
          <button
            className="btn btn-primary btn-sm"
            onClick={() => setShowCreateModal(true)}
          >
            ✨ Criar Card
          </button>
          <a
            className="btn btn-outline-primary btn-sm"
            href="https://trello.com/b/skybridge"
            target="_blank"
            rel="noopener noreferrer"
          >
            Abrir no Trello ↗
          </a>
        </div>
      </div>

      {/* Board Kanban */}
      <KanbanBoard onCardClick={handleCardClick} />

      {/* Modal de Detalhes do Card */}
      {selectedCard && (
        <CardModal
          card={selectedCard}
          show={showCardModal}
          onClose={handleCloseModal}
          onEdit={handleEditCard}
        />
      )}

      {/* Modal de Criação de Card */}
      <CreateCardModal
        show={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          // Card criado com sucesso, atualização virá via SSE
          setShowCreateModal(false)
        }}
      />
    </div>
  )
}
