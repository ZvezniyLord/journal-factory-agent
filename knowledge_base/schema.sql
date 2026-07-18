PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    source_id INTEGER PRIMARY KEY,
    conference_id INTEGER NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(conference_id, source_path, source_sha256)
);

CREATE TABLE IF NOT EXISTS entities (
    entity_id INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK(entity_type IN (
        'PERSON_NAME', 'SURNAME', 'INSTITUTION', 'DEPARTMENT', 'POSITION',
        'ACADEMIC_DEGREE', 'CITY', 'COUNTRY', 'SECTION', 'MARKER', 'IDENTIFIER_PATTERN'
    )),
    canonical_value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    language TEXT,
    trust_level TEXT NOT NULL CHECK(trust_level IN ('CONFIRMED', 'OBSERVED', 'SUGGESTED', 'REJECTED')),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    created_at TEXT NOT NULL,
    UNIQUE(entity_type, normalized_value, language)
);

CREATE TABLE IF NOT EXISTS aliases (
    alias_id INTEGER PRIMARY KEY,
    entity_id INTEGER NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    alias_value TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    language TEXT,
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    UNIQUE(entity_id, normalized_alias, language)
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id INTEGER PRIMARY KEY,
    entity_id INTEGER REFERENCES entities(entity_id),
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    evidence_text TEXT NOT NULL,
    paragraph_index INTEGER,
    extraction_method TEXT NOT NULL,
    review_status TEXT NOT NULL CHECK(review_status IN ('CONFIRMED', 'REVIEW', 'REJECTED')),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_observations (
    rule_observation_id INTEGER PRIMARY KEY,
    rule_id TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    outcome TEXT NOT NULL CHECK(outcome IN ('TRUE_POSITIVE', 'TRUE_NEGATIVE', 'FALSE_POSITIVE', 'FALSE_NEGATIVE')),
    evidence TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS build_runs (
    run_id TEXT PRIMARY KEY,
    conference_id INTEGER NOT NULL,
    pass_id TEXT NOT NULL,
    branch TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    input_manifest_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    body_text_parity REAL,
    object_loss_count INTEGER,
    article_missing_count INTEGER,
    article_duplicate_count INTEGER,
    rendered_page_count INTEGER,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS regression_failures (
    failure_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES build_runs(run_id) ON DELETE CASCADE,
    failure_class TEXT NOT NULL,
    article_id TEXT,
    source_path TEXT,
    message TEXT NOT NULL,
    fixture_path TEXT,
    resolved_by_commit TEXT,
    created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS entity_search USING fts5(
    entity_type,
    canonical_value,
    aliases,
    tokenize = 'unicode61'
);

CREATE INDEX IF NOT EXISTS idx_sources_conference ON sources(conference_id);
CREATE INDEX IF NOT EXISTS idx_entities_type_normalized ON entities(entity_type, normalized_value);
CREATE INDEX IF NOT EXISTS idx_observations_source ON observations(source_id);
CREATE INDEX IF NOT EXISTS idx_rules_rule_id ON rule_observations(rule_id);
CREATE INDEX IF NOT EXISTS idx_runs_conference_pass ON build_runs(conference_id, pass_id);
