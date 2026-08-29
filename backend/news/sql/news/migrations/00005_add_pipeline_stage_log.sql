-- +goose Up
-- Stage 5 observability: article_status alone tells you the *current*
-- state, but not which stage actually broke or why — every failure just
-- says ERROR. pipeline_stages is the type/lookup table (what stages exist,
-- in what order); article_pipeline_log is the append-only "planner" that
-- records every attempt at every stage for every article, so a stuck or
-- failed article's full history — not just its final status — is a query
-- away.
CREATE TABLE news.pipeline_stages (
    id SMALLINT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    sequence_order SMALLINT NOT NULL UNIQUE
);

INSERT INTO news.pipeline_stages (id, name, sequence_order) VALUES
    (1, 'PARSING', 1),
    (2, 'ANNOTATION', 2);

CREATE TABLE news.article_pipeline_log (
    id BIGSERIAL PRIMARY KEY,
    article_id UUID NOT NULL REFERENCES news.articles(id) ON DELETE CASCADE,
    stage_id SMALLINT NOT NULL REFERENCES news.pipeline_stages(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('STARTED', 'SUCCEEDED', 'FAILED')),
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX idx_article_pipeline_log_article_id ON news.article_pipeline_log (article_id, started_at DESC);
CREATE INDEX idx_article_pipeline_log_stage_status ON news.article_pipeline_log (stage_id, status);

-- One row per article: its most recent stage attempt, with the stage name
-- and error already joined in. This is the "where exactly did it stop"
-- query in one SELECT instead of a hand-rolled DISTINCT ON every time.
CREATE VIEW news.article_pipeline_status AS
SELECT DISTINCT ON (l.article_id)
    l.article_id,
    s.name AS stage_name,
    s.sequence_order,
    l.status AS stage_status,
    l.error_message,
    l.started_at,
    l.finished_at
FROM news.article_pipeline_log l
JOIN news.pipeline_stages s ON s.id = l.stage_id
ORDER BY l.article_id, l.started_at DESC;

-- +goose Down
DROP VIEW IF EXISTS news.article_pipeline_status;
DROP TABLE IF EXISTS news.article_pipeline_log;
DROP TABLE IF EXISTS news.pipeline_stages;
