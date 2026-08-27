-- +goose Up
CREATE SCHEMA IF NOT EXISTS news;

CREATE TABLE news.themes (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

INSERT INTO news.themes (name) VALUES
    ('technology'), ('crypto'), ('privacy'), ('security')
ON CONFLICT DO NOTHING;

CREATE TABLE news.languages (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(5) UNIQUE NOT NULL,
    name VARCHAR(255) UNIQUE NOT NULL
);

INSERT INTO news.languages (code, name) VALUES
    ('ru-RU', 'Russian'), ('en-US', 'English'), ('fr-FR', 'French'), ('de-DE', 'German')
ON CONFLICT DO NOTHING;

CREATE TABLE news.articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author VARCHAR(255) NOT NULL,
    source_link VARCHAR(2048) UNIQUE NOT NULL,
    body TEXT NOT NULL,
    theme_id BIGINT REFERENCES news.themes(id) ON DELETE CASCADE,
    language_id BIGINT REFERENCES news.languages(id) ON DELETE CASCADE,
    post_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_news_articles_source_link ON news.articles (source_link);

CREATE TABLE news.tags (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE news.article_tags (
    article_id UUID NOT NULL REFERENCES news.articles(id) ON DELETE CASCADE,
    tag_id BIGINT NOT NULL REFERENCES news.tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

CREATE INDEX idx_news_article_tags_tag_id ON news.article_tags (tag_id);

CREATE TABLE news.annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES news.articles(id) ON DELETE CASCADE,
    language_id BIGINT REFERENCES news.languages(id) ON DELETE CASCADE,
    annotation TEXT NOT NULL,
    neural_network VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_news_annotations_article_language UNIQUE (article_id, language_id)
);

CREATE INDEX idx_news_annotations_language_id ON news.annotations (language_id);

CREATE TABLE news.titles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES news.articles(id) ON DELETE CASCADE,
    language_id BIGINT REFERENCES news.languages(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    neural_network VARCHAR(255) NOT NULL DEFAULT 'native',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_news_titles_article_language UNIQUE (article_id, language_id)
);

CREATE INDEX idx_news_titles_language_id ON news.titles (language_id);

-- Requires the rum package (postgresql-16-rum) in the Postgres image.
CREATE EXTENSION IF NOT EXISTS rum;
CREATE INDEX idx_news_titles_rum ON news.titles USING rum (to_tsvector('simple', title));
CREATE INDEX idx_news_annotations_rum ON news.annotations USING rum (to_tsvector('simple', annotation));

CREATE TABLE news.audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation CHAR(1) NOT NULL, -- I / U / D
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- +goose StatementBegin
CREATE OR REPLACE FUNCTION news.log_change() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO news.audit_log (table_name, operation, new_data)
        VALUES (TG_TABLE_NAME, 'I', row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO news.audit_log (table_name, operation, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'U', row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO news.audit_log (table_name, operation, old_data)
        VALUES (TG_TABLE_NAME, 'D', row_to_json(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;
-- +goose StatementEnd

CREATE TRIGGER articles_audit AFTER INSERT OR UPDATE OR DELETE ON news.articles
    FOR EACH ROW EXECUTE FUNCTION news.log_change();
CREATE TRIGGER tags_audit AFTER INSERT OR UPDATE OR DELETE ON news.tags
    FOR EACH ROW EXECUTE FUNCTION news.log_change();
CREATE TRIGGER article_tags_audit AFTER INSERT OR DELETE ON news.article_tags
    FOR EACH ROW EXECUTE FUNCTION news.log_change();
CREATE TRIGGER annotations_audit AFTER INSERT OR UPDATE OR DELETE ON news.annotations
    FOR EACH ROW EXECUTE FUNCTION news.log_change();

-- +goose Down
DROP TRIGGER IF EXISTS annotations_audit ON news.annotations;
DROP TRIGGER IF EXISTS article_tags_audit ON news.article_tags;
DROP TRIGGER IF EXISTS tags_audit ON news.tags;
DROP TRIGGER IF EXISTS articles_audit ON news.articles;
DROP FUNCTION IF EXISTS news.log_change();
DROP TABLE IF EXISTS news.audit_log;
DROP TABLE IF EXISTS news.titles;
DROP TABLE IF EXISTS news.annotations;
DROP TABLE IF EXISTS news.article_tags;
DROP TABLE IF EXISTS news.tags;
DROP TABLE IF EXISTS news.articles;
DROP TABLE IF EXISTS news.languages;
DROP TABLE IF EXISTS news.themes;
DROP SCHEMA IF EXISTS news CASCADE;
