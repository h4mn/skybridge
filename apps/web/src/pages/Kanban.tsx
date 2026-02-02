import { useQuery } from '@tanstack/react-query'
import { Alert, Badge, Card, Col, Container, Placeholder, Row } from 'react-bootstrap'
import { kanbanApi, CardStatus, KanbanCard as ApiKanbanCard } from '../api/endpoints'

/**
 * Página Kanban - Visualização em modo leitura do board Trello.
 *
 * Fase 1: Apenas leitura (sem drag & drop)
 * - Busca board via API /kanban/board
 * - Exibe cards organizados por coluna (status)
 * - Cards clicáveis abrem o Trello
 * - Respeita workspace ativo (ADR024)
 */
export default function Kanban() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['kanban-board'],
    queryFn: async () => {
      const response = await kanbanApi.getBoard()
      return response.data
    },
    retry: 1,
  })

  if (isLoading) {
    return (
      <div className="p-4">
        <h2 className="mb-4">Kanban - Fluxo de Agentes</h2>
        <KanbanSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4">
        <h2 className="mb-4">Kanban - Fluxo de Agentes</h2>
        <Alert variant="danger" className="d-flex align-items-center gap-2">
          <span>⚠️</span>
          <div className="flex-grow-1">
            <Alert.Heading>Erro ao carregar board</Alert.Heading>
            <p className="mb-0">
              {(error as Error).message || 'Não foi possível carregar o board Kanban. Verifique se o Trello está configurado.'}
            </p>
          </div>
        </Alert>
      </div>
    )
  }

  if (!data?.ok || !data.board) {
    return (
      <div className="p-4">
        <h2 className="mb-4">Kanban - Fluxo de Agentes</h2>
        <Alert variant="warning" className="d-flex align-items-center gap-2">
          <span>📋</span>
          <div className="flex-grow-1">
            <Alert.Heading>Trello não configurado</Alert.Heading>
            <p className="mb-0">
              Configure as variáveis de ambiente TRELLO_API_KEY, TRELLO_API_TOKEN e TRELLO_BOARD_ID no workspace ativo.
            </p>
          </div>
        </Alert>
      </div>
    )
  }

  // Agrupa cards por status
  const cardsByStatus = groupCardsByStatus(data.cards)

  return (
    <div className="p-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="mb-0">Kanban - {data.board.name}</h2>
        <a
          href={data.board.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-outline-primary btn-sm"
        >
          Abrir no Trello ↗
        </a>
      </div>

      <KanbanBoard cardsByStatus={cardsByStatus} />
    </div>
  )
}

/**
 * Componente do board Kanban com colunas.
 */
function KanbanBoard({ cardsByStatus }: { cardsByStatus: Map<CardStatus, ApiKanbanCard[]> }) {
  const statuses: Array<{ status: CardStatus; label: string; color: string; emoji: string }> = [
    { status: CardStatus.BACKLOG, label: 'Backlog', color: 'secondary', emoji: '🧠' },
    { status: CardStatus.TODO, label: 'A Fazer', color: 'primary', emoji: '📋' },
    { status: CardStatus.IN_PROGRESS, label: 'Em Andamento', color: 'info', emoji: '🚧' },
    { status: CardStatus.REVIEW, label: 'Revisão/Teste', color: 'warning', emoji: '👀' },
    { status: CardStatus.CHALLENGE, label: 'Desafio', color: 'danger', emoji: '⚔️' },
    { status: CardStatus.DONE, label: 'Pronto', color: 'success', emoji: '✅' },
    { status: CardStatus.BLOCKED, label: 'Bloqueado', color: 'dark', emoji: '🚫' },
  ]

  return (
    <Container fluid className="px-0">
      <Row className="g-3">
        {statuses.map(({ status, label, color, emoji }) => {
          const cards = cardsByStatus.get(status) || []

          return (
            <Col key={status} xs={12} sm={6} lg={4} xl={3} className="kanban-column">
              <Card className="h-100 kanban-column-card">
                <Card.Header className={`bg-${color} text-white d-flex justify-content-between align-items-center`}>
                  <span>
                    {emoji} {label}
                  </span>
                  <Badge bg="white" text={color}>
                    {cards.length}
                  </Badge>
                </Card.Header>
                <Card.Body className="p-2 d-flex flex-column gap-2 kanban-cards-container">
                  {cards.length === 0 ? (
                    <div className="text-center text-muted py-4 small">
                      Vazio
                    </div>
                  ) : (
                    cards.map((card) => <KanbanCardItem key={card.id} card={card} />)
                  )}
                </Card.Body>
              </Card>
            </Col>
          )
        })}
      </Row>
    </Container>
  )
}

/**
 * Componente de card Kanban individual.
 */
function KanbanCardItem({ card }: { card: ApiKanbanCard }) {
  return (
    <a
      href={card.url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-decoration-none kanban-card-link"
    >
      <Card className="kanban-card h-100" style={{ cursor: 'pointer' }}>
        <Card.Body className="p-3">
          <Card.Text className="mb-2 text-dark fw-semibold text-truncate" title={card.title}>
            {card.title}
          </Card.Text>

          {card.description && (
            <Card.Text className="mb-2 text-muted small text-truncate" title={card.description}>
              {card.description}
            </Card.Text>
          )}

          {card.labels.length > 0 && (
            <div className="mb-2 d-flex flex-wrap gap-1">
              {card.labels.map((label) => (
                <Badge key={label} bg="light" text="dark" className="small">
                  {label}
                </Badge>
              ))}
            </div>
          )}

          <div className="d-flex justify-content-between align-items-center mt-2">
            {card.due_date && (
              <small className={`text-muted ${isOverdue(card.due_date) ? 'text-danger' : ''}`}>
                📅 {formatDate(card.due_date)}
              </small>
            )}
            <small className="text-muted">→</small>
          </div>
        </Card.Body>
      </Card>
    </a>
  )
}

/**
 * Skeleton de loading para o board Kanban.
 */
function KanbanSkeleton() {
  return (
    <Container fluid className="px-0">
      <Row className="g-3">
        {[1, 2, 3, 4].map((i) => (
          <Col key={i} xs={12} sm={6} lg={4} xl={3}>
            <Card className="h-100">
              <Card.Header className="d-flex justify-content-between align-items-center">
                <Placeholder xs={4} />
                <Placeholder xs={1} />
              </Card.Header>
              <Card.Body className="p-2 d-flex flex-column gap-2">
                {[1, 2, 3].map((j) => (
                  <div key={j} className="p-3 border rounded bg-light">
                    <Placeholder xs={7} />
                    <Placeholder xs={4} />
                  </div>
                ))}
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </Container>
  )
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Agrupa cards por status.
 */
function groupCardsByStatus(cards: ApiKanbanCard[]) {
  const grouped = new Map<CardStatus, any[]>()

  // Inicializa todos os status
  Object.values(CardStatus).forEach((status) => {
    grouped.set(status as CardStatus, [])
  })

  // Agrupa cards
  for (const card of cards) {
    const status = card.status as CardStatus
    const list = grouped.get(status) || []
    list.push(card)
    grouped.set(status, list)
  }

  return grouped
}

/**
 * Verifica se uma data está atrasada.
 */
function isOverdue(dateString: string): boolean {
  const date = new Date(dateString)
  return date < new Date()
}

/**
 * Formata data para exibição.
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}
