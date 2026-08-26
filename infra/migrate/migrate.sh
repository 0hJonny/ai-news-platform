#!/bin/sh
set -e

DSN="postgres://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}?sslmode=disable"

# Order matters: chats.sessions references auth.users, profiles.* references auth.users and news.articles.
apply() {
    schema="$1"
    dir="$2"
    echo "== ${schema} schema (goose) =="
    goose -dir "$dir" -table "${schema}.goose_db_version" postgres "$DSN" up
}

apply auth     /sql/core/auth/migrations
apply chats    /sql/core/chats/migrations
apply news     /sql/news/news/migrations
apply profiles /sql/news/profiles/migrations

echo "== all schemas ready =="
