-- +goose Up
ALTER TABLE auth.users ADD COLUMN login VARCHAR(20) UNIQUE;
ALTER TABLE auth.users ADD CONSTRAINT users_login_format CHECK (login ~ '^[a-z][a-z0-9_]{2,19}$');

-- +goose Down
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_login_format;
ALTER TABLE auth.users DROP COLUMN IF EXISTS login;
