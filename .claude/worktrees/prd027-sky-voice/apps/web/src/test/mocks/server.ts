/**
 * MSW Server para testes.
 *
 * Inicia o Mock Service Worker para interceptar requisições de API.
 */

import { setupServer } from 'msw/node'
import handlers from './handlers'

export const server = setupServer(...handlers)

export async function startTestServer() {
  server.listen({
    onUnhandledRequest: 'error',
  })
}

export async function stopTestServer() {
  server.close()
  server.resetHandlers()
}
