import axios from 'axios'

/**
 * Axios HTTP client configurado para comunicação com a API.
 * Inclui interceptors para correlation_id e tratamento de erros.
 */
const apiClient = axios.create({
  baseURL: '/api', // Usará proxy durante desenvolvimento
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar correlation_id
apiClient.interceptors.request.use(
  (config) => {
    // Gera correlation_id se não existir
    const correlationId = config.headers['x-correlation-id'] as string ||
      crypto.randomUUID?.() ||
      Math.random().toString(36).substring(2)
    config.headers['x-correlation-id'] = correlationId
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para tratamento unificado de erros
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log estruturado de erro
    console.error('[API Error]', {
      url: error.config?.url,
      status: error.response?.status,
      message: error.message,
      correlationId: error.config?.headers?.['x-correlation-id'],
    })

    return Promise.reject(error)
  }
)

export default apiClient
