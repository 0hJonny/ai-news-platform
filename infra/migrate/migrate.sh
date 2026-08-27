#!/bin/sh
set -e

DSN="postgres://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}?sslmode=disable"

# Order matters: chats.sessions references auth.users, profiles.* references auth.users and news.articles.
apply() {
    schema="$1"
    dir="$2"
    echo "== ${schema} schema (goose) =="
    # goose's own version table must live somewhere that already exists — the target
    # schema itself is created by each set's 00001_init_schema.sql, so track versions
    # in public instead, one table per schema to avoid collisions.
    goose -dir "$dir" -table "public.goose_db_version_${schema}" postgres "$DSN" up
}

apply auth     /sql/core/auth/migrations
apply chats    /sql/core/chats/migrations
apply news     /sql/news/news/migrations
apply profiles /sql/news/profiles/migrations

echo "== all schemas ready =="
