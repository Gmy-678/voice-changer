-- Minimal schema for /api/v1/voice-library backed by Postgres.
-- Apply with psql against your database.

CREATE TABLE IF NOT EXISTS voice_library_voices (
  id            BIGINT PRIMARY KEY,
  voice_id      TEXT UNIQUE NOT NULL,
  display_name  TEXT NOT NULL,

  -- "built-in" | "user"
  voice_type    TEXT NOT NULL DEFAULT 'built-in',
  owner_user_id TEXT NULL,

  labels        TEXT[] NOT NULL DEFAULT '{}',
  file_path     TEXT NULL,

  meta_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
  meta_text     TEXT NULL,

  is_public     BOOLEAN NOT NULL DEFAULT TRUE,
  url           TEXT NULL,
  fallbackurl   TEXT NULL,

  language_type TEXT NULL,
  age           TEXT NULL,
  gender        TEXT NULL,
  scene         TEXT[] NOT NULL DEFAULT '{}',
  emotion       TEXT[] NOT NULL DEFAULT '{}',

  voice_description TEXT NULL,
  creation_mode     TEXT NOT NULL DEFAULT 'public',
  can_delete        BOOLEAN NOT NULL DEFAULT FALSE,

  create_time   BIGINT NOT NULL,
  use_count     BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_vl_owner ON voice_library_voices(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_vl_create_time ON voice_library_voices(create_time DESC);
CREATE INDEX IF NOT EXISTS idx_vl_use_count ON voice_library_voices(use_count DESC);
CREATE INDEX IF NOT EXISTS idx_vl_scene_gin ON voice_library_voices USING GIN(scene);
CREATE INDEX IF NOT EXISTS idx_vl_emotion_gin ON voice_library_voices USING GIN(emotion);
