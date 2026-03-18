/**
 * Testes do CardModal - Modal de Detalhes do Card Kanban.
 *
 * DOC: PRD024 Task 8 - Modal de Detalhes do Card
 * DOC: ADR024 - Workspace isolation
 *
 * TDD Estrito: Testes escritos ANTES da implementação.
 */
import { render, screen, fireEvent, within } from '@testing-library/react'
import { vi } from 'vitest'
import { CardModal } from '../CardModal'
import { KanbanDbCard } from '../../../api/endpoints'

describe('CardModal', () => {
  const mockCard: KanbanDbCard = {
    id: 'test-card-1',
    list_id: 'brainstorm',
    title: 'Test Card Title',
    description: 'Test card description with details',
    position: 0,
    labels: ['bug', 'high-priority'],
    due_date: '2026-02-10T00:00:00',
    being_processed: false,
    processing_started_at: null,
    processing_job_id: null,
    processing_step: 0,
    processing_total_steps: 0,
    processing_progress_percent: 0,
    issue_number: 123,
    issue_url: 'https://github.com/h4mn/skybridge/issues/123',
    pr_url: 'https://github.com/h4mn/skybridge/pull/456',
    trello_card_id: 'trello-123',
    created_at: '2026-02-01T00:00:00',
    updated_at: '2026-02-03T00:00:00',
  }

  const mockOnClose = vi.fn()
  const mockOnEdit = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('renderização básica', () => {
    it('deve mostrar título do card', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      expect(screen.getByText('Test Card Title')).toBeInTheDocument()
    })

    it('deve mostrar descrição do card', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      expect(screen.getByText('Test card description with details')).toBeInTheDocument()
    })

    it('deve mostrar labels do card', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      expect(screen.getByText('bug')).toBeInTheDocument()
      expect(screen.getByText('high-priority')).toBeInTheDocument()
    })

    it('deve mostrar data de vencimento formatada', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Deve mostrar a data com emoji de calendário
      expect(screen.getByText(/📅/)).toBeInTheDocument()
    })

    it('não deve renderizar quando show=false', () => {
      render(
        <CardModal
          card={mockCard}
          show={false}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Modal não deve estar visível quando show=false
      expect(screen.queryByText('Test Card Title')).not.toBeInTheDocument()
    })
  })

  describe('cards vivos (being_processed)', () => {
    it('deve mostrar badge quando card está sendo processado', () => {
      const liveCard: KanbanDbCard = {
        ...mockCard,
        being_processed: true,
        processing_started_at: '2026-02-03T10:00:00',
        processing_job_id: 'job-123',
        processing_step: 2,
        processing_total_steps: 5,
        processing_progress_percent: 40,
      }

      render(
        <CardModal
          card={liveCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Verifica o texto específico "Agent working" do badge
      expect(screen.getByText(/Agent working/i)).toBeInTheDocument()

      // Verifica que há pelo menos um emoji de robô (pode haver 2: header + badge)
      const robotEmojis = screen.getAllByText(/🤖/)
      expect(robotEmojis.length).toBeGreaterThan(0)

      // Verifica o ID do job
      expect(screen.getByText(/job-123/)).toBeInTheDocument()
    })

    it('deve mostrar progress bar quando card está vivo', () => {
      const liveCard: KanbanDbCard = {
        ...mockCard,
        being_processed: true,
        processing_step: 3,
        processing_total_steps: 5,
        processing_progress_percent: 60,
      }

      render(
        <CardModal
          card={liveCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Deve mostrar o progresso
      expect(screen.getByText('3/5')).toBeInTheDocument()
    })
  })

  describe('links do GitHub', () => {
    it('deve mostrar link para issue quando issue_url existe', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      const issueLink = screen.getByRole('link', { name: /#123/ })
      expect(issueLink).toBeInTheDocument()
      expect(issueLink).toHaveAttribute('href', mockCard.issue_url)
    })

    it('deve mostrar link para PR quando pr_url existe', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      const prLink = screen.getByRole('link', { name: /Pull Request/ })
      expect(prLink).toBeInTheDocument()
      expect(prLink).toHaveAttribute('href', mockCard.pr_url)
    })

    it('deve abrir links em nova aba', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      const issueLink = screen.getByRole('link', { name: /#123/ })
      expect(issueLink).toHaveAttribute('target', '_blank')
      expect(issueLink).toHaveAttribute('rel', 'noopener noreferrer')
    })
  })

  describe('botões de ação', () => {
    it('deve ter botão de fechar (X no header)', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Botão X do header (closeButton)
      const closeButton = screen.getByRole('button', { name: /Close/i })
      expect(closeButton).toBeInTheDocument()
    })

    it('deve ter botão de editar', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      const editButton = screen.getByRole('button', { name: /Editar Card/i })
      expect(editButton).toBeInTheDocument()

      fireEvent.click(editButton)
      expect(mockOnEdit).toHaveBeenCalledWith(mockCard)
    })

    it('deve ter botão de fechar no footer', () => {
      render(
        <CardModal
          card={mockCard}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Botão "Fechar" no footer
      const footerButton = screen.getAllByRole('button').find(btn =>
        btn.textContent === 'Fechar'
      )
      expect(footerButton).toBeInTheDocument()
    })
  })

  describe('edge cases', () => {
    it('deve handle card sem descrição', () => {
      const cardWithoutDescription: KanbanDbCard = {
        ...mockCard,
        description: null,
      }

      render(
        <CardModal
          card={cardWithoutDescription}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Não deve quebrar
      expect(screen.getByText('Test Card Title')).toBeInTheDocument()
    })

    it('deve handle card sem labels', () => {
      const cardWithoutLabels: KanbanDbCard = {
        ...mockCard,
        labels: [],
      }

      render(
        <CardModal
          card={cardWithoutLabels}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Não deve quebrar
      expect(screen.getByText('Test Card Title')).toBeInTheDocument()
    })

    it('deve handle card sem due_date', () => {
      const cardWithoutDueDate: KanbanDbCard = {
        ...mockCard,
        due_date: null,
      }

      render(
        <CardModal
          card={cardWithoutDueDate}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Não deve quebrar
      expect(screen.getByText('Test Card Title')).toBeInTheDocument()
    })

    it('deve handle card sem links do GitHub', () => {
      const cardWithoutLinks: KanbanDbCard = {
        ...mockCard,
        issue_url: null,
        pr_url: null,
        issue_number: null,
      }

      render(
        <CardModal
          card={cardWithoutLinks}
          show={true}
          onClose={mockOnClose}
          onEdit={mockOnEdit}
        />
      )

      // Não deve quebrar, não deve mostrar links
      expect(screen.queryByText('#123')).not.toBeInTheDocument()
      expect(screen.queryByText(/Pull Request/i)).not.toBeInTheDocument()
    })
  })
})
