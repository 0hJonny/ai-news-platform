-- +goose Up
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_login_format;
ALTER TABLE auth.users ADD CONSTRAINT users_login_format CHECK (login ~ '^[a-z][a-z0-9_]{4,19}$');

-- +goose Down
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_login_format;
ALTER TABLE auth.users ADD CONSTRAINT users_login_format CHECK (login ~ '^[a-z][a-z0-9_]{2,19}$');
