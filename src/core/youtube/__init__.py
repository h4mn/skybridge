"""
YouTube Core Domain

Este módulo encapsula toda a lógica relacionada à integração com YouTube:
- Download de vídeos e legendas
- Transcrição e análise de conteúdo
- Indexação para busca semântica (RAG)
- Gerenciamento de biblioteca de conhecimento

Arquitetura: DDD (Domain-Driven Design)
├── domain/        # Entidades, Value Objects, Events
├── application/   # Use Cases, Services, DTOs
└── infrastructure/ # Adapters, Implementações externas
"""

__version__ = "0.1.0"
