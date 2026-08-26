-- name: CreateSession :one
INSERT INTO chats.sessions (user_id, title)
VALUES ($1, $2)
RETURNING *;

-- name: GetSessionByID :one
-- Needed to validate user permissions in the service before any action
SELECT id, user_id, title, created_at, updated_at, deleted_at
  FROM chats.sessions
 WHERE id = $1 LIMIT 1;

-- name: GetUserSessions :many
SELECT id, user_id, title, created_at, updated_at, deleted_at
  FROM chats.sessions
 WHERE user_id = $1 AND deleted_at IS NULL
 ORDER BY updated_at DESC;

-- name: UpdateSessionTitle :exec
UPDATE chats.sessions
   SET title = $2, updated_at = now()
 WHERE id = $1;

-- name: SoftDeleteSession :exec
-- Instead of a physical delete, we set a timestamp
UPDATE chats.sessions
   SET deleted_at = now()
 WHERE id = $1;

-- name: AppendMessage :one
INSERT INTO chats.messages (session_id, parent_id, role, content, trace_id, meta_data)
VALUES ($1, $2, $3, $4, $5, $6)
RETURNING *;

-- name: GetSessionMessages :many
SELECT id, session_id, parent_id, role, content, trace_id, meta_data, created_at
  FROM chats.messages
 WHERE session_id = $1
 ORDER BY created_at ASC;

-- name: GetMessageByID :one
-- Needed to check that the message exists before setting a like/dislike
SELECT id, session_id, parent_id, role, content, trace_id, meta_data, created_at
  FROM chats.messages
 WHERE id = $1 LIMIT 1;

-- name: SetFeedback :one
-- We use ON CONFLICT since there's a UNIQUE index on message_id.
-- If the user changes their mind and clicks 'dislike' instead of 'like', the row gets updated.
INSERT INTO chats.feedback (message_id, rating, comment)
VALUES ($1, $2, $3)
ON CONFLICT (message_id) 
DO UPDATE SET 
    rating = EXCLUDED.rating,
    comment = EXCLUDED.comment,
    created_at = now()
RETURNING *;
