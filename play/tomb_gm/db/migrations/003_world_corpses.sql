-- World-persistent delver corpses (survive campaign wipes)
-- Schema version 3

UPDATE schema_version SET version = 3 WHERE version < 3;

CREATE TABLE IF NOT EXISTS world_corpses (
  id TEXT PRIMARY KEY,
  site_address TEXT,
  cell_address TEXT,
  room_id TEXT,
  display_name TEXT NOT NULL,
  description TEXT,
  state TEXT NOT NULL DEFAULT 'pristine',
  loot_json TEXT NOT NULL DEFAULT '{}',
  data_json TEXT NOT NULL DEFAULT '{}',
  died_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_world_corpses_site_room ON world_corpses(site_address, room_id);
CREATE INDEX IF NOT EXISTS idx_world_corpses_cell ON world_corpses(cell_address);
