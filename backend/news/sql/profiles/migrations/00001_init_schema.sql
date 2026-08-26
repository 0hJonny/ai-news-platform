-- +goose Up
CREATE SCHEMA IF NOT EXISTS profiles;

CREATE TABLE profiles.bookmarks (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES news.articles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_bookmarks_user_id ON profiles.bookmarks (user_id);

CREATE TABLE profiles.likes (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES news.articles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_likes_user_id ON profiles.likes (user_id);

CREATE TABLE profiles.history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES news.articles(id) ON DELETE CASCADE,
    viewed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_history_user_id ON profiles.history (user_id);

-- +goose Down
DROP TABLE IF EXISTS profiles.history;
DROP TABLE IF EXISTS profiles.likes;
DROP TABLE IF EXISTS profiles.bookmarks;
DROP SCHEMA IF EXISTS profiles CASCADE;
