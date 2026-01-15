"""
Skybridge Workflows Plugin

Este plugin define skills para orquestração de workflow multi-agente
na Skybridge, conforme SPEC009 — Orquestração de Workflow Multi-Agente.

Skills implementadas:
- create-issue: Analisa requisito e cria issue estruturada
- resolve-issue: Recebe webhook e implementa solução
- test-issue: Valida solução e roda testes automatizados
- challenge-quality: Executa ataques adversariais para validar qualidade

Autor: Sky
Versão: 1.0.0
Referências:
  - SPEC008: AI Agent Interface
  - SPEC009: Orquestração de Workflow Multi-Agente
  - PRD013: Webhook Autonomous Agents
  - ADR018: Português Brasileiro
"""

__version__ = "1.0.0"
__author__ = "Sky"
