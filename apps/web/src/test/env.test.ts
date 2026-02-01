/**
 * Teste simples para validar o ambiente.
 */

import { describe, it, expect } from 'vitest'

describe('Ambiente de Testes', () => {
  it('deve conseguir fazer uma soma simples', () => {
    expect(1 + 1).toBe(2)
  })

  it('deve conseguir verificar verdade', () => {
    expect(true).toBe(true)
  })
})
