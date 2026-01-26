# Skybridge WebUI

Dashboard web para monitoramento em tempo real do sistema de webhook agents.

**Status:** 🚧 Fase 0 - Setup (Em Implementação)
**Documentação:** [PRD014](../../docs/prd/PRD014-webui-dashboard.md)

## Stack Técnica

| Tecnologia | Versão |
|------------|--------|
| React | 18.3+ |
| TypeScript | 5.7+ |
| Vite | 6.0+ |
| React Bootstrap | 2.10+ |
| Axios | 1.7+ |
| React Query | 5.28+ |

## Estrutura

```
apps/web/
├── main.py              # Fachada Python (inicia Vite)
├── package.json         # Dependências Node
├── vite.config.ts       # Config Vite (base URL: /web/)
├── tsconfig.json        # Config TypeScript
├── index.html           # Entry HTML
└── src/
    ├── main.tsx         # Entry React
    ├── App.tsx          # Componente principal
    ├── api/
    │   ├── client.ts    # Axios HTTP client
    │   └── endpoints.ts # API endpoints
    ├── components/
    │   └── Header.tsx
    ├── pages/
    │   └── Dashboard.tsx
    └── styles/
        └── main.css
```

## Como Usar

### 1. Instalar Dependências

```bash
cd apps/web
npm install
```

### 2. Iniciar API Backend (Terminal 1)

```bash
python apps/api/main.py
```

### 3. Iniciar WebUI (Terminal 2)

```bash
python apps/web/main.py
```

Ou diretamente com npm:

```bash
cd apps/web
npm run dev
```

### 4. Acessar

Abra no browser: `http://localhost:5173/web/`

## Desenvolvimento

| Comando | Descrição |
|---------|-----------|
| `npm run dev` | Inicia Vite dev server |
| `npm run build` | Build para produção |
| `npm run preview` | Preview do build |
| `npm run lint` | ESLint |

## Roadmap

- [x] **Fase 0:** Setup (estrutura, configs)
- [ ] **Fase 1:** API Client + Layout
- [ ] **Fase 2:** Dashboard com métricas
- [ ] **Fase 3:** Worktrees Table
- [ ] **Fase 4:** Log Streaming (SSE)
- [ ] **Fase 5:** Polish (dark mode, mobile)

> "A interface perfeita é invisível - o usuário vê seus dados, não a aplicação." – made by Sky 🎨
