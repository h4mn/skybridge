import { Modal, Button, Form, Spinner, Alert } from 'react-bootstrap'
import { useState, useEffect } from 'react'
import { KanbanDbCard, KanbanDbList, kanbanDbApi } from '../../api/endpoints'

interface CreateCardModalProps {
  show: boolean
  onClose: () => void
  onSuccess?: (card: KanbanDbCard) => void
  defaultListId?: string
}

/**
 * Modal de Criação de Card Kanban.
 *
 * DOC: PRD024 Task 9 - Modal de Criação de Card
 *
 * Features:
 * - Formulário com título (obrigatório), descrição, lista, labels, due_date
 * - Validação de formulário
 * - POST /api/kanban/cards
 * - Feedback visual de sucesso/erro
 */
export function CreateCardModal({ show, onClose, onSuccess, defaultListId }: CreateCardModalProps) {
  const [lists, setLists] = useState<KanbanDbList[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form fields
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [listId, setListId] = useState(defaultListId || '')
  const [labels, setLabels] = useState('')
  const [dueDate, setDueDate] = useState('')

  // Carrega listas ao montar
  useEffect(() => {
    const loadLists = async () => {
      try {
        const response = await kanbanDbApi.getLists()
        setLists(response.data)
        // Define lista padrão se não foi especificada
        if (!defaultListId && response.data.length > 0) {
          setListId(response.data[0].id)
        }
      } catch (err) {
        console.error('Erro ao carregar listas:', err)
        setError('Não foi possível carregar as listas')
      }
    }

    if (show) {
      loadLists()
    }
  }, [show, defaultListId])

  // Limpa formulário ao fechar
  useEffect(() => {
    if (!show) {
      resetForm()
    }
  }, [show])

  const resetForm = () => {
    setTitle('')
    setDescription('')
    setListId(defaultListId || '')
    setLabels('')
    setDueDate('')
    setError(null)
  }

  // Converte string de labels para array
  const parseLabels = (labelsString: string): string[] => {
    return labelsString
      .split(',')
      .map(l => l.trim())
      .filter(l => l.length > 0)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const newCard = await kanbanDbApi.createCard({
        list_id: listId,
        title,
        description: description || undefined,
        labels: parseLabels(labels),
        due_date: dueDate || undefined,
      })

      onSuccess?.(newCard.data)
      resetForm()
      onClose()
    } catch (err) {
      console.error('Erro ao criar card:', err)
      setError('Não foi possível criar o card. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      show={show}
      onHide={onClose}
      size="lg"
      aria-labelledby="create-card-modal-title"
      centered
    >
      <Modal.Header closeButton>
        <Modal.Title id="create-card-modal-title">
          ✨ Criar Novo Card
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {/* Alerta de erro */}
        {error && (
          <Alert variant="danger" dismissible onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Form onSubmit={handleSubmit}>
          {/* Título */}
          <Form.Group className="mb-3" controlId="formCardTitle">
            <Form.Label>Título *</Form.Label>
            <Form.Control
              type="text"
              required
              placeholder="Ex: Implementar feature X"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={loading}
              autoFocus
            />
          </Form.Group>

          {/* Descrição */}
          <Form.Group className="mb-3" controlId="formCardDescription">
            <Form.Label>Descrição</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              placeholder="Descreva os detalhes do card..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
            />
          </Form.Group>

          {/* Lista */}
          <Form.Group className="mb-3" controlId="formCardList">
            <Form.Label>Lista *</Form.Label>
            <Form.Select
              required
              value={listId}
              onChange={(e) => setListId(e.target.value)}
              disabled={loading}
            >
              {lists.map((list) => (
                <option key={list.id} value={list.id}>
                  {list.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>

          {/* Labels */}
          <Form.Group className="mb-3" controlId="formCardLabels">
            <Form.Label>Labels</Form.Label>
            <Form.Control
              type="text"
              placeholder="bug, feature, enhancement (separados por vírgula)"
              value={labels}
              onChange={(e) => setLabels(e.target.value)}
              disabled={loading}
            />
            <Form.Text className="text-muted">
              Separe múltiplos labels com vírgula
            </Form.Text>
          </Form.Group>

          {/* Data de Vencimento */}
          <Form.Group className="mb-3" controlId="formCardDueDate">
            <Form.Label>Data de Vencimento</Form.Label>
            <Form.Control
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              disabled={loading}
            />
          </Form.Group>

          {/* Botão de submit (oculto, formulário é submetido pelo footer) */}
          <button type="submit" style={{ display: 'none' }} />
        </Form>
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          Cancelar
        </Button>
        <Button
          variant="primary"
          onClick={(e) => {
            // Trigger form submit
            const form = e.currentTarget.closest('form')
            form?.requestSubmit()
          }}
          disabled={loading || !title.trim() || !listId}
        >
          {loading ? (
            <>
              <Spinner animation="border" size="sm" /> Criando...
            </>
          ) : (
            'Criar Card'
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  )
}
