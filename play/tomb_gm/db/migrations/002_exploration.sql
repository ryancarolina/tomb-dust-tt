-- Exploration system: cell features, dungeon rooms, scene state
-- Schema version 2

UPDATE schema_version SET version = 2 WHERE version < 2;

-- Persistent features discovered in surface cells
CREATE TABLE IF NOT EXISTS cell_features (
  id TEXT PRIMARY KEY,
  cell_address TEXT NOT NULL,
  feature_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  scene_position INTEGER NOT NULL,
  discovered INTEGER NOT NULL DEFAULT 0,
  state TEXT NOT NULL DEFAULT 'pristine',
  data_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cell_features_address ON cell_features(cell_address);
CREATE INDEX IF NOT EXISTS idx_cell_features_address_scene ON cell_features(cell_address, scene_position);

-- Track visited cells and player scene position
CREATE TABLE IF NOT EXISTS cell_visits (
  cell_address TEXT NOT NULL,
  campaign_slug TEXT NOT NULL,
  first_visited_at TEXT NOT NULL,
  last_visited_at TEXT NOT NULL,
  times_visited INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (cell_address, campaign_slug)
);

-- Dungeon / site room graphs (persistent layout)
CREATE TABLE IF NOT EXISTS site_rooms (
  id TEXT PRIMARY KEY,
  site_address TEXT NOT NULL,
  room_id TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  exits_json TEXT NOT NULL DEFAULT '[]',
  tags_json TEXT NOT NULL DEFAULT '[]',
  visited INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE(site_address, room_id)
);

CREATE INDEX IF NOT EXISTS idx_site_rooms_address ON site_rooms(site_address);

-- Persistent features within dungeon rooms
CREATE TABLE IF NOT EXISTS room_features (
  id TEXT PRIMARY KEY,
  site_address TEXT NOT NULL,
  room_id TEXT NOT NULL,
  feature_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  state TEXT NOT NULL DEFAULT 'pristine',
  data_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_room_features_site_room ON room_features(site_address, room_id);
