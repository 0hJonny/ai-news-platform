-- +goose Up
-- Article state machine driven by the Celery-based Parser/Annotation
-- pipeline (see workers/shared/celery_app.py). Every article starts
-- PENDING_PARSING and moves forward as the parsing_queue / annotation_queue
-- tasks claim and process it; ERROR is a terminal state for manual/automatic
-- retry handling to pick up later.
CREATE TYPE news.article_status AS ENUM (
    'PENDING_PARSING',
    'PARSING',
    'PARSED',
    'PENDING_ANNOTATION',
    'ANNOTATED',
    'ERROR'
);

ALTER TABLE news.articles
    ADD COLUMN status news.article_status NOT NULL DEFAULT 'PENDING_PARSING';

-- The pipeline's core access pattern is "give me all articles in state X",
-- so this index is load-bearing from day one, not a later optimization.
CREATE INDEX idx_news_articles_status ON news.articles (status);

-- +goose Down
DROP INDEX IF EXISTS news.idx_news_articles_status;
ALTER TABLE news.articles DROP COLUMN IF EXISTS status;
DROP TYPE IF EXISTS news.article_status;
