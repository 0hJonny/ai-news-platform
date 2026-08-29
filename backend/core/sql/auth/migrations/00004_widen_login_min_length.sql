-- +goose Up
-- Backfill: accounts created back when the minimum was 3 chars (see
-- 00003_add_user_login.sql) can have a login that's now too short for the
-- CHECK below. Padding with a fixed character (e.g. '0') can collide with
-- another existing login and trip the UNIQUE constraint, so pad with a
-- slice of the row's own id instead — every row's id is already globally
-- unique, so the padded login can't collide with anything.
UPDATE auth.users
   SET login = login || left(replace(id::text, '-', ''), 5 - length(login))
 WHERE login IS NOT NULL AND length(login) < 5;

ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_login_format;
ALTER TABLE auth.users ADD CONSTRAINT users_login_format CHECK (login ~ '^[a-z][a-z0-9_]{4,19}$');

-- +goose Down
ALTER TABLE auth.users DROP CONSTRAINT IF EXISTS users_login_format;
ALTER TABLE auth.users ADD CONSTRAINT users_login_format CHECK (login ~ '^[a-z][a-z0-9_]{2,19}$');
