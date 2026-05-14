from __future__ import annotations

# catalog: произвольный slug (global, user, matrix_2026_04, …) — без CHECK для поддержки версий.
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dn_diagnosis_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (catalog, name)
);

CREATE TABLE IF NOT EXISTS dn_specialty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (catalog, name)
);

CREATE TABLE IF NOT EXISTS dn_diagnosis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    code TEXT NOT NULL,
    category_id INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (catalog, code),
    FOREIGN KEY (category_id) REFERENCES dn_diagnosis_category(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_dn_diagnosis_catalog_code ON dn_diagnosis(catalog, code);

CREATE TABLE IF NOT EXISTS dn_diagnosis_specialty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    diagnosis_id INTEGER NOT NULL,
    specialty_id INTEGER NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('primary', 'joint')),
    UNIQUE (catalog, diagnosis_id, specialty_id, source),
    FOREIGN KEY (diagnosis_id) REFERENCES dn_diagnosis(id) ON DELETE CASCADE,
    FOREIGN KEY (specialty_id) REFERENCES dn_specialty(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dn_diagnosis_group (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    code TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    rule TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (catalog, code)
);

CREATE TABLE IF NOT EXISTS dn_diagnosis_group_membership (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    group_id INTEGER NOT NULL,
    diagnosis_id INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (catalog, group_id, diagnosis_id),
    FOREIGN KEY (group_id) REFERENCES dn_diagnosis_group(id) ON DELETE CASCADE,
    FOREIGN KEY (diagnosis_id) REFERENCES dn_diagnosis(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dn_service (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE (catalog, code)
);

CREATE TABLE IF NOT EXISTS dn_service_price_period (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    date_start TEXT NOT NULL,
    date_end TEXT,
    title TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dn_service_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    service_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    price REAL NOT NULL,
    UNIQUE (catalog, service_id, period_id),
    FOREIGN KEY (service_id) REFERENCES dn_service(id) ON DELETE CASCADE,
    FOREIGN KEY (period_id) REFERENCES dn_service_price_period(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dn_service_requirement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL DEFAULT 'global',
    service_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    specialty_id INTEGER NOT NULL,
    is_required INTEGER NOT NULL DEFAULT 1,
    UNIQUE (catalog, service_id, group_id, specialty_id),
    FOREIGN KEY (service_id) REFERENCES dn_service(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES dn_diagnosis_group(id) ON DELETE CASCADE,
    FOREIGN KEY (specialty_id) REFERENCES dn_specialty(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dn_service_requirement_catalog ON dn_service_requirement(catalog);

CREATE TABLE IF NOT EXISTS dn_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dn_catalog_registry (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    effective_from TEXT,
    effective_to TEXT,
    read_only INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
