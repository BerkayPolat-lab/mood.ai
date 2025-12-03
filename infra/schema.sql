-- mood.ai Database Schema

-- ## Database Schema

-- The application uses three main tables:

-- ### uploads
-- - `id` (UUID) - Primary key
-- - `audio_file_path` (TEXT) - Path to uploaded audio file
-- - `file_size` (BIGINT) - Size of the file in bytes
-- - `user_id_sha256` (TEXT) - SHA256 hash of user ID
-- - `created_at` (TIMESTAMP) - Upload timestamp

-- ### jobs
-- - `id` (UUID) - Primary key
-- - `upload_id` (UUID) - Foreign key to uploads table
-- - `user_id_sha256` (TEXT) - SHA256 hash of user ID
-- - `status` (TEXT) - Job status: 'queued', 'processing', 'completed', 'failed'
-- - `error` (TEXT) - Error message if job failed
-- - `started_at` (TIMESTAMP) - Job start time
-- - `finished_at` (TIMESTAMP) - Job completion time
-- - `created_at` (TIMESTAMP) - Job creation timestamp

-- ### predictions
-- - `id` (UUID) - Primary key
-- - `user_id_sha256` (TEXT) - SHA256 hash of user ID
-- - `upload_id` (UUID) - Foreign key to uploads table
-- - `scores` (JSONB) - ML pipeline output (mood, emotion, energy_level, confidence)
-- - `model_version` (TEXT) - Version of the ML model used
-- - `inference_time` (FLOAT) - Time taken for inference
-- - `model_name` (TEXT) - Name of the ML model
-- - `created_at` (TIMESTAMP) - Prediction timestamp


-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Uploads table
-- Stores uploaded audio files with metadata
CREATE TABLE IF NOT EXISTS uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audio_file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    user_id_sha256 TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id_sha256 for faster queries
CREATE INDEX IF NOT EXISTS idx_uploads_user_id ON uploads(user_id_sha256);
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at);

-- Jobs table
-- Tracks ML pipeline processing jobs
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    user_id_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    error TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes on jobs table
CREATE INDEX IF NOT EXISTS idx_jobs_upload_id ON jobs(upload_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id_sha256);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Predictions table
-- Stores ML pipeline inference results
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id_sha256 TEXT NOT NULL,
    upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    scores JSONB NOT NULL,
    model_version TEXT NOT NULL,
    inference_time FLOAT,
    model_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes on predictions table
CREATE INDEX IF NOT EXISTS idx_predictions_upload_id ON predictions(upload_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id_sha256);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_model_name ON predictions(model_name);

-- Example JSON structure for scores column:
-- {
--   "mood": "calm",
--   "emotion": "content",
--   "energy_level": "low",
--   "confidence": 0.91
-- }

-- Playlists table
-- Stores Spotify playlist recommendations associated with audio uploads
CREATE TABLE IF NOT EXISTS playlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    spotify_playlist_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    owner JSONB NOT NULL,
    images JSONB NOT NULL,
    link TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes on playlists table
CREATE INDEX IF NOT EXISTS idx_playlists_upload_id ON playlists(upload_id);
CREATE INDEX IF NOT EXISTS idx_playlists_spotify_id ON playlists(spotify_playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlists_created_at ON playlists(created_at);

-- Example JSON structure for owner column:
-- {
--   "display_name": "John Doe",
--   "id": "user123",
--   "external_urls": {"spotify": "https://open.spotify.com/user/user123"},
--   "href": "https://api.spotify.com/v1/users/user123",
--   "type": "user",
--   "uri": "spotify:user:user123"
-- }

-- Example JSON structure for images column:
-- [
--   {
--     "url": "https://i.scdn.co/image/...",
--     "height": 300,
--     "width": 300
--   }
-- ]

