-- ==========================================
-- GTD APP - FINAL DATABASE SCHEMA (v2)
-- Multi-user, complete in one script
-- Run once on a fresh database
-- ==========================================

-- USERS: accounts & roles
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(80) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CONTEXTS: "@office", "@home" etc. (unique PER USER)
CREATE TABLE contexts (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    user_id    INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT contexts_name_user_key UNIQUE (name, user_id)
);

-- PROJECTS: "If multi-step, what's the successful outcome?"
CREATE TABLE projects (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    outcome      TEXT,
    notes        TEXT,
    status       VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | on_hold | completed
    user_id      INTEGER REFERENCES users(id),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ITEMS: every piece of "stuff"
-- status: inbox | next_action | scheduled | waiting_for
--         | someday_maybe | reference | done | trash
CREATE TABLE items (
    id           SERIAL PRIMARY KEY,
    title        VARCHAR(500) NOT NULL,
    notes        TEXT,
    status       VARCHAR(30) NOT NULL DEFAULT 'inbox',
    project_id   INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    context_id   INTEGER REFERENCES contexts(id) ON DELETE SET NULL,
    due_date     DATE,
    due_time     TIME,
    delegated_to VARCHAR(200),
    user_id      INTEGER REFERENCES users(id),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes for the app's most frequent queries
CREATE INDEX idx_items_status  ON items(status);
CREATE INDEX idx_items_project ON items(project_id);
CREATE INDEX idx_items_user    ON items(user_id);

-- NOTE: no default contexts here — each new user gets their
-- own 6 contexts automatically at registration.