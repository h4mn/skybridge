/**
 * Hook useKanbanSSE - Conecta ao endpoint SSE de Kanban.
 *
 * DOC: PRD024 Task 7 - SSE para atualizações em tempo real
 * DOC: runtime/delivery/kanban_routes.py - /api/kanban/events
 *
 * Funcionalidades:
 * - Conecta ao endpoint SSE
 * - Recebe eventos de cards (created, updated, moved, etc)
 * - Atualiza estado local quando eventos chegam
 * - Reconecta automaticamente se conexão cair
 */
import { useEffect, useRef, useCallback } from 'react'
import { KanbanDbCard } from '../../api/endpoints'

// Tipos de eventos SSE do Kanban
export type KanbanSSEEventType =
  | 'lists_snapshot'
  | 'card_snapshot'
  | 'card_created'
  | 'card_updated'
  | 'card_deleted'
  | 'card_processing_started'
  | 'card_processing_completed'
  | 'error'

export interface KanbanSSEEvent {
  type: KanbanSSEEventType
  data: any
}

interface UseKanbanSSEOptions {
  workspace?: string
  onListsSnapshot?: (lists: any[]) => void
  onCardSnapshot?: (card: KanbanDbCard) => void
  onCardCreated?: (card: KanbanDbCard) => void
  onCardUpdated?: (card: KanbanDbCard) => void
  onCardDeleted?: (cardId: string) => void
  onProcessingStarted?: (card: KanbanDbCard) => void
  onProcessingCompleted?: (card: KanbanDbCard) => void
  onError?: (error: string) => void
}

export function useKanbanSSE(options: UseKanbanSSEOptions = {}) {
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const {
    workspace = 'core',
    onListsSnapshot,
    onCardSnapshot,
    onCardCreated,
    onCardUpdated,
    onCardDeleted,
    onProcessingStarted,
    onProcessingCompleted,
    onError,
  } = options

  // Conecta ao endpoint SSE
  const connect = useCallback(() => {
    // Fecha conexão anterior se existir
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    // Limpa timeout de reconexão
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    try {
      // URL do endpoint SSE com workspace
      const url = `/api/kanban/events?workspace=${workspace}`
      eventSourceRef.current = new EventSource(url)

      // Lista de eventos com seus handlers
      const eventHandlers: Record<string, (data: string) => void> = {
        lists_snapshot: (data) => {
          try {
            const lists = JSON.parse(data)
            onListsSnapshot?.(lists)
          } catch (e) {
            console.error('[useKanbanSSE] Erro ao parsear lists_snapshot:', e)
          }
        },

        card_snapshot: (data) => {
          try {
            const card = JSON.parse(data)
            onCardSnapshot?.(card)
          } catch (e) {
            console.error('[useKanbanSSE] Erro ao parsear card_snapshot:', e)
          }
        },

        card_created: (data) => {
          try {
            const card = JSON.parse(data)
            onCardCreated?.(card)
          } catch (e) {
            console.error('[useKanbanSSE] Erro ao parsear card_created:', e)
          }
        },

        card_updated: (data) => {
          try {
            const card = JSON.parse(data)
            onCardUpdated?.(card)
          } catch (e) {
            console.error('[useKanbanSSE] Erro ao parsear card_updated:', e)
          }
        },

        card_deleted: (data) => {
          try {
            const { id } = JSON.parse(data)
            onCardDeleted?.(id)
          } catch (e) {
            console.error('[useKanbanSSE] Erro ao parsear card_deleted:', e)
          }
        },

        card_processing_started: (data) => {
          try {
            const card = JSON.parse(data)
            onProcessingStarted?.(card)
          } catch (e) {
            console.error('[useKanbanSSE] Erro ao parsear card_processing_started:', e)
          }
        },

        card_processing_completed: (data) => {
          try {
            const card = JSON.parse(data)
            onProcessingCompleted?.(card)
          } catch (e) {
            console.error('[useKanbanSSE] Erro ao parsear card_processing_completed:', e)
          }
        },

        error: (data) => {
          try {
            const { error } = JSON.parse(data)
            onError?.(error)
          } catch (e) {
            onError?.(data)
          }
        },
      }

      // Registra handlers para cada tipo de evento
      Object.entries(eventHandlers).forEach(([eventType, handler]) => {
        eventSourceRef.current?.addEventListener(eventType, (event) => {
          const messageEvent = event as MessageEvent
          handler(messageEvent.data)
        })
      })

      // Handler de erro de conexão
      eventSourceRef.current.onerror = (error) => {
        console.error('[useKanbanSSE] Erro de conexão SSE:', error)

        // Tenta reconectar após 5 segundos
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('[useKanbanSSE] Tentando reconectar...')
          connect()
        }, 5000)
      }

      console.log(`[useKanbanSSE] Conectado ao endpoint SSE (workspace=${workspace})`)
    } catch (error) {
      console.error('[useKanbanSSE] Erro ao criar EventSource:', error)
      onError?.(String(error))
    }
  }, [workspace, onListsSnapshot, onCardSnapshot, onCardCreated, onCardUpdated, onCardDeleted, onProcessingStarted, onProcessingCompleted, onError])

  // Conecta ao montar e desconecta ao desmontar
  useEffect(() => {
    connect()

    return () => {
      // Limpa recursos
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [connect])

  return {
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
  }
}
