# PRD025: Wiki - Markdown Colaborativa por Workspace

**Status:** 📋 Planejado
**Data:** 2026-02-02
**Autor:** Sky
**Versão:** 1.0
**Depende de:** ADR024 (Workspace isolation)

---

## 1. Executivo Resumido

### Problema

Atualmente o Skybridge não possui uma Wiki para documentação colaborativa de tarefas e procedimentos. Conforme a visão Skybridge (core/vision.md), há necessidade de uma Wiki para organizar conhecimento por workspace.

### Solução

**Implementar Wiki colaborativa** com:
- Markdown completo com live preview
- Organização hierárquica de páginas
- Busca full-text
- Histórico de versões
- Suporte a múltiplos workspaces (ADR024)

### Proposta de Valor

| Benefício | Descrição |
|-----------|-----------|
| Documentação organizada | Hierarquia clara de páginas por workspace |
| Colaboração | Múltiplos editores com lock de edição |
- Busca rápida | Full-text search em todo o conteúdo |
| Histórico | Versionamento completo de edições |

---

## 2. Funcionalidades

### 2.1 RF001: Páginas Wiki

**Descrição:** Criar, editar, visualizar páginas de documentação

**Requisitos:**
- Suporte completo a Markdown (CommonMark + GFM)
- Live preview de Markdown enquanto edita
- Syntax highlighting para código
- Imagens embedadas
- Tabelas, listas, checkboxes
- Links internos entre páginas
- **Prioridade:** Alta

### 2.2 RF002: Organização

**Descrição:** Hierarquia de páginas, categorias, tags

**Requisitos:**
- Estrutura de pastas/diretórios
- Categorias e tags para páginas
- Full-text search em todas as páginas
- Sidebar com árvore de navegação
- **Prioridade:** Média

### 2.3 RF003: Colaboração

**Descrição:** Múltiplos editores, comentários, sugestões

**Requisitos:**
- Edição colaborativa com lock (prevenir conflitos)
- Histórico de versões com diff
- Comentários em páginas
- Sistema de sugestões (edits propostos)
- **Prioridade:** Baixa

---

## 3. Backend API

### 3.1 Endpoints

```python
# Páginas
GET    /api/wiki/pages              # Lista páginas (filtrar por workspace)
GET    /api/wiki/pages/{slug}       # Retorna página wiki específica
POST   /api/wiki/pages              # Cria nova página wiki no workspace
PUT    /api/wiki/pages/{slug}       # Atualiza página wiki
DELETE /api/wiki/pages/{slug}       # Deleta página wiki do workspace

# Busca
GET    /api/wiki/search?q={query}   # Full-text search em páginas

# Histórico
GET    /api/wiki/pages/{slug}/history      # Histórico de versões
GET    /api/wiki/pages/{slug}/history/{id} # Versão específica
POST   /api/wiki/pages/{slug}/rollback/{id} # Rollback para versão

# Árvore
GET    /api/wiki/tree                # Árvore de páginas (sidebar)

# Lock
POST   /api/wiki/pages/{slug}/lock   # Adquire lock de edição
DELETE /api/wiki/pages/{slug}/lock   # Libera lock de edição
```

### 3.2 Filtro por Workspace

Todos os endpoints respeitam o header `X-Workspace` (ADR024):

```python
@router.get("/api/wiki/pages")
async def get_pages(request: Request):
    workspace_id = request.headers.get("X-Workspace", "core")
    return wiki_service.get_pages(workspace_id)

@router.post("/api/wiki/pages")
async def create_page(request: Request, page: PageCreate):
    workspace_id = request.headers.get("X-Workspace", "core")
    return wiki_service.create_page(workspace_id, page)
```

---

## 4. Frontend Components

### 4.1 Estrutura

```
apps/web/src/
├── pages/
│   └── Wiki.tsx                     # Página principal
├── components/
│   └── Wiki/
│       ├── WikiList.tsx             # Lista de páginas
│       ├── WikiPage.tsx             # Visualizador de página (Markdown renderizado)
│       ├── WikiEditor.tsx           # Editor Markdown com preview
│       ├── WikiSearch.tsx           # Busca full-text
│       ├── WikiSidebar.tsx          # Árvore de páginas
│       ├── WikiHistory.tsx          # Histórico de versões com diff
│       ├── PageLock.tsx             # Indicador de lock de edição
│       └── __tests__/
│           └── Wiki.test.tsx        # Testes de isolamento
```

### 4.2 WikiPage Component

```typescript
interface WikiPageProps {
  slug: string
}

export function WikiPage({ slug }: WikiPageProps) {
  const { data: page, isLoading } = useQuery({
    queryKey: ['wiki-page', slug],
    queryFn: () => wikiApi.getPage(slug)
  })

  if (isLoading) return <LoadingSpinner />
  if (!page) return <NotFound />

  return (
    <div className="wiki-page">
      <WikiSidebar />
      <div className="wiki-content">
        <h1>{page.title}</h1>
        <MarkdownRenderer content={page.content} />
        <PageMetadata
          updatedAt={page.updated_at}
          updatedBy={page.updated_by}
        />
      </div>
    </div>
  )
}
```

### 4.3 WikiEditor Component

```typescript
interface WikiEditorProps {
  slug?: string  // Se vazio, cria nova página
}

export function WikiEditor({ slug }: WikiEditorProps) {
  const [content, setContent] = useState('')
  const [preview, setPreview] = useState(false)

  // Adquire lock de edição
  useEffect(() => {
    if (slug) {
      wikiApi.lockPage(slug)
      return () => wikiApi.unlockPage(slug)
    }
  }, [slug])

  return (
    <div className="wiki-editor">
      <WikiEditorToolbar
        preview={preview}
        onTogglePreview={() => setPreview(!preview)}
      />
      <div className="wiki-editor-content">
        {preview ? (
          <MarkdownRenderer content={content} />
        ) : (
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Escreva em Markdown..."
          />
        )}
      </div>
    </div>
  )
}
```

---

## 5. Roadmap de Implementação

| Fase | Tarefa | Status |
|------|--------|--------|
| 1 | Backend: Endpoints Wiki básicos | 🔮 Pendente |
| 2 | Frontend: WikiList + WikiPage básicos | 🔮 Pendente |
| 3 | Frontend: Editor Markdown + Preview | 🔮 Pendente |
| 4 | Frontend: Árvore de páginas (sidebar) | 🔮 Pendente |
| 5 | Frontend: Busca full-text | 🔮 Pendente |
| 6 | Frontend: Histórico de versões com diff | 🔮 Pendente |
| 7 | Frontend: Lock de edição colaborativa | 🔮 Pendente |
| 8 | Frontend: Filtros workspace | 🔮 Pendente |
| 9 | Testes: Isolamento workspace | 🔮 Pendente |

---

## 6. Estrutura de Dados

### 6.1 Schema SQL

```sql
CREATE TABLE wiki_pages (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    parent_id TEXT,  -- Para hierarquia
    position INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    is_published BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (parent_id) REFERENCES wiki_pages(id) ON DELETE SET NULL
);

CREATE INDEX idx_wiki_workspace ON wiki_pages(workspace_id);
CREATE INDEX idx_wiki_parent ON wiki_pages(parent_id);
CREATE INDEX idx_wiki_slug ON wiki_pages(slug);

CREATE TABLE wiki_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id TEXT NOT NULL,
    content TEXT NOT NULL,
    changed_by TEXT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES wiki_pages(id) ON DELETE CASCADE
);

CREATE TABLE wiki_locks (
    page_id TEXT PRIMARY KEY,
    locked_by TEXT NOT NULL,
    locked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (page_id) REFERENCES wiki_pages(id) ON DELETE CASCADE
);
```

### 6.2 Models

```python
@dataclass
class WikiPage:
    id: str
    workspace_id: str
    slug: str
    title: str
    content: str
    parent_id: Optional[str] = None
    position: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    is_published: bool = True

@dataclass
class WikiHistory:
    id: int
    page_id: str
    content: str
    changed_by: Optional[str] = None
    changed_at: datetime = field(default_factory=datetime.utcnow)
```

---

## 7. Testes

### 7.1 Backend Tests

```
tests/integration/wiki/
├── test_wiki_adapter.py            # Testes CRUD de páginas
├── test_wiki_history.py            # Testes de histórico
├── test_wiki_lock.py               # Testes de lock de edição
└── test_wiki_search.py             # Testes de busca full-text
```

### 7.2 Frontend Tests

```
apps/web/src/components/__tests__/
└── Wiki/
    ├── WikiList.test.tsx           # Testes da lista de páginas
    ├── WikiPage.test.tsx           # Testes do visualizador
    ├── WikiEditor.test.tsx         # Testes do editor
    ├── WikiSearch.test.tsx         # Testes da busca
    └── workspace-isolation.test.tsx # Testes de isolamento
```

---

## 8. Bibliotecas Recomendadas

### Frontend

- **react-markdown:** Renderizador de Markdown
- **remark-gfm:** GitHub Flavored Markdown (tabelas, checkboxes)
- **react-syntax-highlighter:** Syntax highlighting para código
- **@uiw/react-md-editor:** Editor Markdown com preview

### Backend

- **markdown2:** Parser Markdown (Python)
- **bleach:** Sanitização HTML (segurança)
- **whoosh:** Full-text search (Python)

---

## 9. Referências

- **ADR024:** Workspace isolation via X-Workspace header
- **core/vision.md:** Visão Skybridge sobre Wiki
- **CommonMark:** Especificação Markdown padrão
- **GFM:** GitHub Flavored Markdown

---

> "A documentação é o amor que o código dá ao futuro" – made by Sky 🚀
