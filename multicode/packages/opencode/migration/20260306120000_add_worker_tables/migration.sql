-- Worker node table for managing remote workers
CREATE TABLE IF NOT EXISTS worker_node (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  platform TEXT NOT NULL DEFAULT 'unknown',
  arch TEXT NOT NULL DEFAULT 'unknown',
  work_directory TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'offline',
  last_ping INTEGER,
  capabilities TEXT,
  password TEXT,
  time_created INTEGER NOT NULL,
  time_updated INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS worker_node_status_idx ON worker_node(status);

-- Sync session table for tracking file sync sessions
CREATE TABLE IF NOT EXISTS sync_session (
  id TEXT PRIMARY KEY,
  worker_id TEXT NOT NULL REFERENCES worker_node(id) ON DELETE CASCADE,
  directory TEXT NOT NULL,
  remote_directory TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  last_sync INTEGER,
  files_synced INTEGER DEFAULT 0,
  time_created INTEGER NOT NULL,
  time_updated INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS sync_session_worker_idx ON sync_session(worker_id);