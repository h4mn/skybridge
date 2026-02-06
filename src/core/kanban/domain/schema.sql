-- ============================================================================
-- Kanban Database Schema (SQLite)
-- ============================================================================
-- FONTE ÚNICA DA VERDADE do sistema Kanban Skybridge
-- Localização: workspace/skybridge/kanban.db
-- DOC: ADR024 - Workspace isolation
-- DOC: FLUXO_GITHUB_TRELO_COMPONENTES.md
-- ============================================================================

-- =============================================================================
-- Boards
-- =============================================================================

CREATE TABLE IF NOT EXISTS boards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trello_board_id TEXT,
    trello_sync_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_boards_trello ON boards(trello_board_id);

-- =============================================================================
-- Lists (colunas do Kanban)
-- =============================================================================

CREATE TABLE IF NOT EXISTS lists (
    id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    name TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    trello_list_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lists_board ON lists(board_id);
CREATE INDEX IF NOT EXISTS idx_lists_position ON lists(board_id, position);

-- =============================================================================
-- Cards (com suporte para "Cards Vivos")
-- =============================================================================

CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    list_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    labels TEXT,  -- JSON array: ["bug", "high-priority"]
    due_date TIMESTAMP,

    -- Cards Vivos - Agent Processing
    being_processed BOOLEAN DEFAULT 0,
    processing_started_at TIMESTAMP,
    processing_job_id TEXT,
    processing_step INTEGER DEFAULT 0,
    processing_total_steps INTEGER DEFAULT 0,

    -- Integração GitHub
    issue_number INTEGER,
    issue_url TEXT,
    pr_url TEXT,

    -- Integração Trello
    trello_card_id TEXT,

    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_cards_list ON cards(list_id);
CREATE INDEX IF NOT EXISTS idx_cards_position ON cards(list_id, position);
CREATE INDEX IF NOT EXISTS idx_cards_being_processed ON cards(being_processed, position);
CREATE INDEX IF NOT EXISTS idx_cards_trello ON cards(trello_card_id);
CREATE INDEX IF NOT EXISTS idx_cards_issue ON cards(issue_number);

-- =============================================================================
-- Card History (audit trail opcional)
-- =============================================================================

CREATE TABLE IF NOT EXISTS card_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    event TEXT NOT NULL,  -- 'created', 'moved', 'updated', 'processing_started', 'processing_completed'
    from_list_id TEXT,
    to_list_id TEXT,
    metadata TEXT,  -- JSON: {"step": 3, "total_steps": 5, "job_id": "..."}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_card_history_card ON card_history(card_id);
CREATE INDEX IF NOT EXISTS idx_card_history_created ON card_history(created_at);

-- =============================================================================
-- Triggers para atualizar updated_at automaticamente
-- =============================================================================

CREATE TRIGGER IF NOT EXISTS update_boards_timestamp
AFTER UPDATE ON boards
BEGIN
    UPDATE boards SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_lists_timestamp
AFTER UPDATE ON lists
BEGIN
    UPDATE lists SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_cards_timestamp
AFTER UPDATE ON cards
BEGIN
    UPDATE cards SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =============================================================================
-- View para buscar cards ordenados (cards vivos primeiro)
-- =============================================================================

CREATE VIEW IF NOT EXISTS cards_ordered AS
SELECT
    c.*,
    l.name as list_name,
    l.position as list_position
FROM cards c
JOIN lists l ON c.list_id = l.id
ORDER BY
    c.being_processed DESC,  -- Cards vivos PRIMEIRO
    c.position ASC,           -- Depois por posição manual
    c.created_at DESC;        -- Depois por data de criação
