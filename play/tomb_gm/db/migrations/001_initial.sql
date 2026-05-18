-- Tomb Dust GM schema v1
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER PRIMARY KEY
);

INSERT OR IGNORE INTO schema_version (version) VALUES (1);

CREATE TABLE IF NOT EXISTS campaigns (
  slug TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  content_pin_json TEXT NOT NULL DEFAULT '{}',
  account_state_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  campaign_slug TEXT NOT NULL REFERENCES campaigns(slug),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  phase TEXT NOT NULL DEFAULT 'preparation',
  summary_id INTEGER
);

CREATE TABLE IF NOT EXISTS party_state (
  session_id TEXT PRIMARY KEY REFERENCES sessions(id),
  address TEXT NOT NULL DEFAULT '32-C',
  mode TEXT NOT NULL DEFAULT 'surface',
  site_id TEXT,
  site_node_id TEXT,
  phase TEXT NOT NULL DEFAULT 'preparation',
  stamp_json TEXT,
  clocks_json TEXT NOT NULL DEFAULT '{"ingress":0,"delve":0,"extract":0,"max":6}',
  gold_in_transit INTEGER NOT NULL DEFAULT 0,
  flags_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS characters (
  id TEXT NOT NULL,
  campaign_slug TEXT NOT NULL REFERENCES campaigns(slug),
  slot INTEGER,
  sheet_json TEXT NOT NULL,
  alive INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  PRIMARY KEY (id, campaign_slug)
);

CREATE TABLE IF NOT EXISTS combat_state (
  session_id TEXT PRIMARY KEY REFERENCES sessions(id),
  active INTEGER NOT NULL DEFAULT 0,
  round INTEGER NOT NULL DEFAULT 0,
  turn_index INTEGER NOT NULL DEFAULT 0,
  initiative_json TEXT NOT NULL DEFAULT '[]',
  combatants_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  beat_id TEXT,
  ts TEXT NOT NULL,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_events_session_ts ON events(session_id, ts);

CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_slug TEXT NOT NULL,
  fact TEXT NOT NULL,
  entities_json TEXT NOT NULL DEFAULT '[]',
  address TEXT,
  importance INTEGER NOT NULL DEFAULT 3,
  source_event_id INTEGER,
  superseded_by INTEGER,
  created_at TEXT NOT NULL,
  last_recalled_at TEXT
);

CREATE TABLE IF NOT EXISTS memory_embeddings (
  memory_id INTEGER PRIMARY KEY REFERENCES memories(id),
  vector_blob BLOB
);

CREATE TABLE IF NOT EXISTS scene_summaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  text TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gates (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  gate_type TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  resolved_at TEXT,
  resolution TEXT
);

CREATE TABLE IF NOT EXISTS rules_fts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL,
  heading TEXT,
  chunk TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rules_fts_chunk ON rules_fts(chunk);
