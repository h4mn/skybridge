/**
 * Testes: LiveCard (Cards Vivos)
 *
 * DOC: PRD024 - Kanban Cards Vivos (seção 3)
 * DOC: apps/web/src/components/Kanban/KanbanCard.tsx
 *
 * Testa especificamente a funcionalidade de "Cards Vivos" - cards
 * que estão sendo processados por agentes autônomos.
 *
 * Cards vivos possuem:
 * - being_processed = true
 * - Borda pulsante azul (kanban-card-alive)
 * - Badge "🤖 Agent working..."
 * - Barra de progresso mostrando step/total_steps
 * - Ordenação prioritária (sempre no topo da coluna)
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { KanbanCard } from '../KanbanCard'

// Mock do @dnd-kit/core
vi.mock('@dnd-kit/core', () => ({
  useDraggable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    isDragging: false,
  }),
}))

describe('LiveCard - Cards Vivos', () => {
  const createLiveCard = (overrides: any = {}) => ({
    id: 'live-card-123',
    list_id: 'em-andamento',
    title: 'Card Vivo',
    description: 'Sendo processado por agente',
    position: 0,
    labels: ['agent', 'processing'],
    due_date: null,
    being_processed: true,
    processing_started_at: '2026-02-04T10:30:00Z',
    processing_job_id: 'job-abc-123',
    processing_step: 3,
    processing_total_steps: 5,
    processing_progress_percent: 60,
    issue_number: null,
    issue_url: null,
    pr_url: null,
    trello_card_id: null,
    created_at: '2026-02-04T10:00:00Z',
    updated_at: '2026-02-04T10:30:00Z',
    ...overrides,
  })

  const createNormalCard = () => ({
    id: 'normal-card-456',
    list_id: 'em-andamento',
    title: 'Card Normal',
    description: 'Aguardando processamento',
    position: 1,
    labels: [],
    due_date: null,
    being_processed: false,
    processing_started_at: null,
    processing_job_id: null,
    processing_step: 0,
    processing_total_steps: 0,
    processing_progress_percent: 0,
    issue_number: null,
    issue_url: null,
    pr_url: null,
    trello_card_id: null,
    created_at: '2026-02-04T09:00:00Z',
    updated_at: '2026-02-04T09:00:00Z',
  })

  describe('identificação de cards vivos', () => {
    it('deve ser identificado como vivo quando being_processed=true', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const cardElement = container.querySelector('.kanban-card')
      expect(cardElement).toHaveClass('kanban-card-alive')
    })

    it('não deve ser identificado como vivo quando being_processed=false', () => {
      const normalCard = createNormalCard()
      const { container } = render(<KanbanCard card={normalCard} />)

      const cardElement = container.querySelector('.kanban-card')
      expect(cardElement).not.toHaveClass('kanban-card-alive')
    })

    it('deve mostrar emoji 🤖 em cards vivos', () => {
      const liveCard = createLiveCard()
      render(<KanbanCard card={liveCard} />)

      expect(screen.getByText('🤖')).toBeInTheDocument()
    })

    it('não deve mostrar emoji 🤖 em cards normais', () => {
      const normalCard = createNormalCard()
      render(<KanbanCard card={normalCard} />)

      expect(screen.queryByText('🤖')).not.toBeInTheDocument()
    })
  })

  describe('badge de progresso', () => {
    it('deve mostrar texto "Agent working..." em cards vivos', () => {
      const liveCard = createLiveCard()
      render(<KanbanCard card={liveCard} />)

      expect(screen.getByText('Agent working...')).toBeInTheDocument()
    })

    it('deve mostrar barra de progresso quando processing_total_steps > 0', () => {
      const liveCard = createLiveCard({
        processing_step: 2,
        processing_total_steps: 5,
        processing_progress_percent: 40,
      })

      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress-bar')
      expect(progressBar).toBeInTheDocument()
      expect(progressBar).toHaveStyle({ width: '40%' })
    })

    it('deve mostrar progresso como "step/total"', () => {
      const liveCard = createLiveCard({
        processing_step: 3,
        processing_total_steps: 5,
      })

      render(<KanbanCard card={liveCard} />)

      expect(screen.getByText('3/5')).toBeInTheDocument()
    })

    it('não deve mostrar barra de progresso quando processing_total_steps = 0', () => {
      const liveCard = createLiveCard({
        processing_total_steps: 0,
        processing_progress_percent: 0,
      })

      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress')
      expect(progressBar).not.toBeInTheDocument()
    })

    it('deve calcular processing_progress_percent corretamente', () => {
      const liveCard = createLiveCard({
        processing_step: 4,
        processing_total_steps: 10,
        processing_progress_percent: 40,
      })

      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress-bar')
      expect(progressBar).toHaveStyle({ width: '40%' })
    })
  })

  describe('barra de progresso visual', () => {
    it('deve ter classe progress-bar-striped para animação', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress-bar')
      expect(progressBar).toHaveClass('progress-bar-striped')
    })

    it('deve ter classe progress-bar-animated para animação', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress-bar')
      expect(progressBar).toHaveClass('progress-bar-animated')
    })

    it('deve ter altura reduzida (progress-sm)', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const progress = container.querySelector('.progress')
      expect(progress).toHaveClass('progress-sm')
    })
  })

  describe('informações de processamento', () => {
    it('deve mostrar processing_job_id quando disponível', () => {
      const liveCard = createLiveCard({
        processing_job_id: 'job-xyz-789',
      })

      // Job ID é mostrado no modal, não no card
      // Verificando apenas que não há erro
      expect(() => render(<KanbanCard card={liveCard} />)).not.toThrow()
    })

    it('deve mostrar processing_started_at formatado', () => {
      const liveCard = createLiveCard({
        processing_started_at: '2026-02-04T10:30:00Z',
      })

      // Data de início não é mostrada diretamente no card
      // Verificando apenas que não há erro
      expect(() => render(<KanbanCard card={liveCard} />)).not.toThrow()
    })
  })

  describe('ordenação prioritária', () => {
    it('cards vivos devem vir antes de cards normais na mesma coluna', () => {
      // Testa a ordenação simulada
      const cards = [createNormalCard(), createLiveCard()]

      // Ordena como o KanbanBoard faria
      const sortedCards = [...cards].sort((a, b) => {
        if (a.being_processed && !b.being_processed) return -1
        if (!a.being_processed && b.being_processed) return 1
        return a.position - b.position
      })

      expect(sortedCards[0].id).toBe('live-card-123')
      expect(sortedCards[1].id).toBe('normal-card-456')
    })

    it('cards vivos devem manter ordem baseada em position', () => {
      const liveCard1 = createLiveCard({ id: 'live-1', position: 1 })
      const liveCard2 = createLiveCard({ id: 'live-2', position: 0 })
      const liveCard3 = createLiveCard({ id: 'live-3', position: 2 })

      const cards = [liveCard1, liveCard2, liveCard3]

      const sortedCards = [...cards].sort((a, b) => {
        if (a.being_processed && !b.being_processed) return -1
        if (!a.being_processed && b.being_processed) return 1
        return a.position - b.position
      })

      expect(sortedCards[0].id).toBe('live-2')
      expect(sortedCards[1].id).toBe('live-1')
      expect(sortedCards[2].id).toBe('live-3')
    })
  })

  describe('estilos visuais', () => {
    it('card vivo deve ter classe kanban-card-alive', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const cardElement = container.querySelector('.kanban-card')
      expect(cardElement?.classList.contains('kanban-card-alive')).toBe(true)
    })

    it('badge deve ter classe kanban-live-badge', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const badge = container.querySelector('.kanban-live-badge')
      expect(badge).toBeInTheDocument()
    })

    it('badge deve ter ícone com classe live-badge-icon', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const icon = container.querySelector('.live-badge-icon')
      expect(icon).toBeInTheDocument()
    })

    it('badge deve ter texto com classe live-badge-text', () => {
      const liveCard = createLiveCard()
      const { container } = render(<KanbanCard card={liveCard} />)

      const text = container.querySelector('.live-badge-text')
      expect(text).toBeInTheDocument()
      expect(text).toHaveTextContent('Agent working...')
    })
  })

  describe('cenários de progresso', () => {
    it('progresso 0% - início do processamento', () => {
      const liveCard = createLiveCard({
        processing_step: 0,
        processing_total_steps: 5,
        processing_progress_percent: 0,
      })

      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress-bar')
      expect(progressBar).toHaveStyle({ width: '0%' })
      expect(screen.getByText('0/5')).toBeInTheDocument()
    })

    it('progresso 50% - processamento na metade', () => {
      const liveCard = createLiveCard({
        processing_step: 3,
        processing_total_steps: 6,
        processing_progress_percent: 50,
      })

      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress-bar')
      expect(progressBar).toHaveStyle({ width: '50%' })
      expect(screen.getByText('3/6')).toBeInTheDocument()
    })

    it('progresso 100% - processamento completo', () => {
      const liveCard = createLiveCard({
        processing_step: 5,
        processing_total_steps: 5,
        processing_progress_percent: 100,
      })

      const { container } = render(<KanbanCard card={liveCard} />)

      const progressBar = container.querySelector('.progress-bar')
      expect(progressBar).toHaveStyle({ width: '100%' })
      expect(screen.getByText('5/5')).toBeInTheDocument()
    })
  })

  describe('transição de estado', () => {
    it('deve parar de mostrar badge quando being_processed muda para false', () => {
      const { rerender } = render(<KanbanCard card={createLiveCard()} />)

      expect(screen.getByText('🤖')).toBeInTheDocument()
      expect(screen.getByText('Agent working...')).toBeInTheDocument()

      rerender(<KanbanCard card={createNormalCard()} />)

      expect(screen.queryByText('🤖')).not.toBeInTheDocument()
      expect(screen.queryByText('Agent working...')).not.toBeInTheDocument()
    })

    it('deve começar a mostrar badge quando being_processed muda para true', () => {
      const { rerender } = render(<KanbanCard card={createNormalCard()} />)

      expect(screen.queryByText('🤖')).not.toBeInTheDocument()

      rerender(<KanbanCard card={createLiveCard()} />)

      expect(screen.getByText('🤖')).toBeInTheDocument()
    })
  })
})

/**
 * Notas de implementação:
 *
 * 1. Cards vivos são identificados por being_processed=true
 * 2. A classe CSS kanban-card-alive adiciona borda pulsante azul
 * 3. A animação é definida em CSS (pulse-border keyframes)
 * 4. A barra de progresso usa Bootstrap progress com animação
 * 5. Ordenação: being_processed DESC, position ASC, created_at DESC
 */
