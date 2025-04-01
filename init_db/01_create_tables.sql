CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT false,
    last_request TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    content_type VARCHAR(50),
    content TEXT,
    media_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
