-- +goose Up
CREATE SCHEMA IF NOT EXISTS auth;

CREATE TYPE auth.user_role AS ENUM ('anonymous', 'user', 'admin');

CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    role auth.user_role NOT NULL DEFAULT 'anonymous',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON auth.users(email) WHERE email IS NOT NULL;

-- +goose Down
DROP INDEX IF EXISTS auth.idx_users_email;
DROP TABLE IF EXISTS auth.users;
DROP TYPE IF EXISTS auth.user_role;
DROP SCHEMA IF EXISTS auth CASCADE;
