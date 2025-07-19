-- Database initialization script for Radio Russell
-- This script is run automatically when the PostgreSQL container starts

-- Ensure we're using the correct database
\c radio_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create song_ratings table
CREATE TABLE IF NOT EXISTS song_ratings (
    id SERIAL PRIMARY KEY,
    song_id VARCHAR(100) NOT NULL,
    user_fingerprint VARCHAR(32) NOT NULL,
    rating INTEGER NOT NULL CHECK(rating IN (1, -1)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(song_id, user_fingerprint)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_song_ratings_song_id ON song_ratings(song_id);
CREATE INDEX IF NOT EXISTS idx_song_ratings_user_fingerprint ON song_ratings(user_fingerprint);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_song_ratings_created_at ON song_ratings(created_at DESC);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE radio_db TO radio_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO radio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO radio_user;

-- Insert some sample data for testing (optional)
-- INSERT INTO users (name, email) VALUES ('Test User', 'test@example.com') ON CONFLICT DO NOTHING;
