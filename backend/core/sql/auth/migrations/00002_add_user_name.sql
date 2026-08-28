-- +goose Up
ALTER TABLE auth.users ADD COLUMN name VARCHAR(255);

-- +goose Down
ALTER TABLE auth.users DROP COLUMN name;
