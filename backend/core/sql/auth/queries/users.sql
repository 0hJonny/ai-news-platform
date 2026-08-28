-- name: CreateUser :one
INSERT INTO auth.users (email, password_hash, role, name, login)
VALUES ($1, $2, $3, $4, $5)
RETURNING *;

-- name: GetUserByEmail :one
SELECT a.id,
       a.email,
       a.password_hash,
       a.created_at,
       a.role,
       a.name,
       a.login
  FROM auth.users a
WHERE a.email = $1
LIMIT 1;

-- name: GetUserById :one
SELECT a.id,
       a.email,
       a.password_hash,
       a.created_at,
       a.role,
       a.name,
       a.login
  FROM auth.users a
WHERE a.id = $1
LIMIT 1;

-- name: UpdateUserToRegistered :one
UPDATE auth.users
   SET email = $1,
       password_hash = $2,
       name = $3,
       login = $4,
       role = 'user',
       updated_at = CURRENT_TIMESTAMP
 WHERE id = $5
RETURNING *;

-- name: IsLoginAvailable :one
SELECT NOT EXISTS (SELECT 1 FROM auth.users WHERE login = $1) AS available;
