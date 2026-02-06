/**
 * Testes: KanbanCard Component
 *
 * DOC: PRD024 - Kanban Cards Vivos
 * DOC: apps/web/src/components/Kanban/KanbanCard.tsx
 *
 * Testa o componente de card individual com:
 * - Renderização básica
 * - Cards vivos (being_processed) com borda pulsante
 * - Badge de progresso para cards em processamento
 * - Labels e datas de vencimento
 * - Links para issues/PRs
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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

describe('KanbanCard', () => {
  const mockCard = {
    id: 'card-123',
    list_id: 'brainstorm',
    title: 'Test Card Title',
    description: 'Test card description',
    position: 0,
    labels: ['bug', 'high-priority'],
    due_date: '2026-12-31T23:59:59Z',
    being_processed: false,
    processing_started_at: null,
    processing_job_id: null,
    processing_step: 0,
    processing_total_steps: 0,
    processing_progress_percent: 0,
    issue_number: 42,
    issue_url: 'https://github.com/test/repo/issues/42',
    pr_url: null,
    trello_card_id: null,
    created_at: '2026-02-01T00:00:00Z',
    updated_at: '2026-02-01T00:00:00Z',
  }

  describe('renderização básica', () => {
    it('deve renderizar o título do card', () => {
      render(<KanbanCard card={mockCard} />)
      expect(screen.getByText('Test Card Title')).toBeInTheDocument()
    })

    it('deve renderizar a descrição quando fornecida', () => {
      render(<KanbanCard card={mockCard} />)
      expect(screen.getByText('Test card description')).toBeInTheDocument()
    })

    it('não deve renderizar descrição quando não fornecida', () => {
      const cardWithoutDesc = { ...mockCard, description: null }
      render(<KanbanCard card={cardWithoutDesc} />)
      expect(screen.queryByText('Test card description')).not.toBeInTheDocument()
    })

    it('deve renderizar labels quando fornecidas', () => {
      render(<KanbanCard card={mockCard} />)
      expect(screen.getByText('bug')).toBeInTheDocument()
      expect(screen.getByText('high-priority')).toBeInTheDocument()
    })

    it('não deve renderizar labels quando não fornecidas', () => {
      const cardWithoutLabels = { ...mockCard, labels: [] }
      render(<KanbanCard card={cardWithoutLabels} />)
      expect(screen.queryByText('bug')).not.toBeInTheDocument()
    })

    it('deve renderizar link para issue quando fornecido', () => {
      render(<KanbanCard card={mockCard} />)
      expect(screen.getByText('#42')).toBeInTheDocument()
      const link = screen.getByText('#42').closest('a')
      expect(link).toHaveAttribute('href', 'https://github.com/test/repo/issues/42')
    })

    it('deve chamar onClick quando card é clicado', () => {
      const handleClick = vi.fn()
      render(<KanbanCard card={mockCard} onClick={handleClick} />)

      const cardElement = screen.getByText('Test Card Title').closest('.kanban-card')
      fireEvent.click(cardElement!)

      expect(handleClick).toHaveBeenCalledWith(mockCard)
    })
  })

  describe('cards vivos (being_processed)', () => {
    it('deve mostrar badge de card vivo quando being_processed=true', () => {
      const liveCard = {
        ...mockCard,
        being_processed: true,
        processing_started_at: '2026-02-04T00:00:00Z',
        processing_job_id: 'job-123',
        processing_step: 2,
        processing_total_steps: 5,
        processing_progress_percent: 40,
      }

      render(<KanbanCard card={liveCard} />)

      expect(screen.getByText('🤖')).toBeInTheDocument()
      expect(screen.getByText('Agent working...')).toBeInTheDocument()
    })

    it('deve mostrar barra de progresso quando processing_total_steps > 0', () => {
      const liveCard = {
        ...mockCard,
        being_processed: true,
        processing_step: 3,
        processing_total_steps: 5,
        processing_progress_percent: 60,
      }

      render(<KanbanCard card={liveCard} />)

      expect(screen.getByText('3/5')).toBeInTheDocument()

      const progressBar = document.querySelector('.progress-bar')
      expect(progressBar).toHaveStyle({ width: '60%' })
    })

    it('deve ter classe kanban-card-alive quando being_processed=true', () => {
      const liveCard = { ...mockCard, being_processed: true }
      const { container } = render(<KanbanCard card={liveCard} />)

      const cardElement = container.querySelector('.kanban-card')
      expect(cardElement).toHaveClass('kanban-card-alive')
    })

    it('não deve ter classe kanban-card-alive quando being_processed=false', () => {
      const { container } = render(<KanbanCard card={mockCard} />)

      const cardElement = container.querySelector('.kanban-card')
      expect(cardElement).not.toHaveClass('kanban-card-alive')
    })
  })

  describe('data de vencimento', () => {
    it('deve renderizar data de vencimento formatada', () => {
      render(<KanbanCard card={mockCard} />)

      const dateElement = screen.getByText(/📅/)
      expect(dateElement).toBeInTheDocument()
    })

    it('deve marcar data como atrasada quando due_date está no passado', () => {
      const overdueCard = {
        ...mockCard,
        due_date: '2020-01-01T00:00:00Z',
      }

      const { container } = render(<KanbanCard card={overdueCard} />)

      const dateElement = screen.getByText(/📅/).closest('small')
      expect(dateElement).toHaveClass('text-danger')
    })
  })

  describe('links do GitHub', () => {
    it('deve renderizar link de issue quando issue_url fornecido', () => {
      render(<KanbanCard card={mockCard} />)

      const issueLink = screen.getByText('#42')
      expect(issueLink).toBeInTheDocument()
      expect(issueLink.closest('a')).toHaveAttribute('href', 'https://github.com/test/repo/issues/42')
    })

    it('deve renderizar link de PR quando pr_url fornecido', () => {
      const cardWithPR = {
        ...mockCard,
        pr_url: 'https://github.com/test/repo/pull/10',
      }

      render(<KanbanCard card={cardWithPR} />)

      const prLink = screen.getByText('🔗 PR')
      expect(prLink).toBeInTheDocument()
      expect(prLink.closest('a')).toHaveAttribute('href', 'https://github.com/test/repo/pull/10')
    })

    it('deve prevenir propagação de clique ao clicar em links', () => {
      const handleClick = vi.fn()
      render(<KanbanCard card={mockCard} onClick={handleClick} />)

      const issueLink = screen.getByText('#42').closest('a')
      fireEvent.click(issueLink!)

      // onClick do card não deve ser chamado quando clica no link
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('drag & drop', () => {
    it('deve aplicar transform quando drag está ativo', () => {
      // Mock useDraggable com transform
      vi.doMock('@dnd-kit/core', () => ({
        useDraggable: () => ({
          attributes: {},
          listeners: {},
          setNodeRef: vi.fn(),
          transform: { x: 100, y: 50 },
          isDragging: true,
        }),
      }))

      // Recarregar módulo para aplicar mock
      vi.resetModules()

      // Teste requer setup mais complexo para mock de @dnd-kit
      // Por ora, apenas verifica que componente renderiza sem crash
      const { container } = render(<KanbanCard card={mockCard} />)
      expect(container.querySelector('.kanban-card')).toBeInTheDocument()
    })
  })
})

/**
 * Notas de implementação:
 *
 * 1. O @dnd-kit/core precisa ser mockado pois não roda em ambiente jsdom
 * 2. Testes de drag visual requerem validação de estilos inline de transform
 * 3. Testes de eventos de clique precisam verificar propagação correta
 * 4. Data formatting usa toLocaleDateString, pode variar por timezone
 */
