-- +goose Up
-- Redesign, all in one pass (folds what were originally three migrations
-- into one, since none had shipped yet — no reason to create an ENUM
-- column here just to convert it to a lookup-table FK two steps later):
--
-- 1. articles.status used to describe the WHOLE pipeline (parsing AND
--    annotation) as one scalar. That breaks the moment annotation
--    becomes multi-language — "done in EN, pending in FR" can't fit in
--    one column. Split it: articles.parsing_status_id is scoped to
--    parsing only; annotations becomes a proper per-(article, language)
--    job table with its own status_id, ready for multiple annotation
--    jobs per article with no further schema change.
--
-- 2. All three status/stage-event vocabularies become real lookup
--    tables (surrogate SMALLINT id + code + description), matching the
--    languages/pipeline_stages convention already used elsewhere:
--    application code resolves the human-readable code to that id
--    before writing (LogPipelineStageDB already does exactly this for
--    stage_id). These were the least stable fields in the schema —
--    article_status already needed a full migration to narrow its
--    vocabulary once, and article_pipeline_log.status wasn't even an
--    ENUM, just a bare CHECK — a lookup table turns "add a new status"
--    into an INSERT instead of an ALTER TYPE/type-recreation dance.
--    (chats.message_role, chats.feedback_rating, auth.user_role are
--    deliberately left as native ENUMs — stable, fixed-forever protocol
--    vocabularies, not something this project's own pipeline churns on.)
--
-- 3. FKs and indexes are named per this project's convention from the
--    start: fk_<table>_<column>_<referenced_table>_<referenced_column>,
--    ix_<table>_<column1>_<column2> (table name once, even for the
--    two-column indexes — Postgres index names are unique per SCHEMA,
--    not per table, and three different tables here have a
--    `status_id`-shaped column, so bare column names would collide;
--    doubling the table name per column would just be noise since a
--    Postgres index always lives on a single table).
--
-- pipeline_stages/article_pipeline_log themselves (00005) and articles/
-- annotations/titles/themes/tags's original FKs and indexes from
-- 00001_init_schema.sql (and every other schema's 00001) are left on
-- Postgres's default names — renaming those is a separate, much bigger
-- pass across the whole schema, not folded in here.

-- 1. Lookup tables, created with their final shape (code + description)
-- directly — no later ALTER ADD COLUMN needed since nothing has read
-- these yet.
CREATE TABLE news.parsing_statuses (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    sequence_order SMALLINT,
    description TEXT NOT NULL
);
INSERT INTO news.parsing_statuses (id, code, sequence_order, description) VALUES
    (1, 'PENDING_PARSING', 1, 'Draft created, not yet picked up by a parsing.scrape_source task.'),
    (2, 'PARSING', 2, 'A parsing.scrape_source task is actively fetching and parsing the source page.'),
    (3, 'PARSED', 3, 'Parsing finished successfully; author/title/body are populated.'),
    (4, 'ERROR', 99, 'Parsing failed (fetch error, empty body, or failed to persist the result).');

CREATE TABLE news.annotation_statuses (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    sequence_order SMALLINT,
    description TEXT NOT NULL
);
INSERT INTO news.annotation_statuses (id, code, sequence_order, description) VALUES
    (1, 'PENDING', 1, 'Job created, not yet picked up by an annotation.annotate_article task.'),
    (2, 'ANNOTATING', 2, 'An annotation.annotate_article task is actively running the article through the LLM.'),
    (3, 'ANNOTATED', 3, 'Annotation finished successfully; annotation text and neural_network are populated.'),
    (4, 'ERROR', 99, 'Annotation failed (source article unavailable, LLM call failed, or failed to persist the result).');

CREATE TABLE news.pipeline_event_statuses (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT NOT NULL
);
INSERT INTO news.pipeline_event_statuses (id, code, description) VALUES
    (1, 'STARTED', 'A worker began this stage''s attempt (logged before any work happens).'),
    (2, 'SUCCEEDED', 'The stage''s attempt completed successfully.'),
    (3, 'FAILED', 'The stage''s attempt failed; see the log row''s error_message for why.');

-- pipeline_stages itself already exists (00005) without description —
-- that one needs the ALTER, since it's not created here.
ALTER TABLE news.pipeline_stages ADD COLUMN description TEXT;
UPDATE news.pipeline_stages SET description = CASE name
    WHEN 'PARSING' THEN 'The article''s raw content is being fetched and extracted from its source URL.'
    WHEN 'ANNOTATION' THEN 'The article''s parsed content is being summarized/annotated by an LLM.'
END;
ALTER TABLE news.pipeline_stages ALTER COLUMN description SET NOT NULL;

-- 2. news.articles.status (ENUM, 00002) -> parsing_status_id (FK),
-- straight in one step.
--
-- Backfill: the old combined status conflated the two stages — an
-- article whose ERROR actually happened during annotation (parsing
-- succeeded fine) looked identical to one that failed during parsing
-- itself. body is the more trustworthy signal: only the parsing task
-- ever writes it, so a non-empty body means parsing definitely
-- finished, regardless of what the old status said or what happened to
-- annotation afterward. Only fall back to the old status for rows that
-- never got that far.
ALTER TABLE news.articles ADD COLUMN parsing_status_id SMALLINT
    CONSTRAINT fk_articles_parsing_status_id_parsing_statuses_id
    REFERENCES news.parsing_statuses(id);

UPDATE news.articles a SET parsing_status_id = ps.id
FROM news.parsing_statuses ps
WHERE ps.code = CASE
    WHEN a.body IS NOT NULL AND a.body <> '' THEN 'PARSED'
    WHEN a.status IN ('PENDING_ANNOTATION', 'ANNOTATED') THEN 'PARSED'
    WHEN a.status = 'PARSING' THEN 'PARSING'
    WHEN a.status = 'ERROR' THEN 'ERROR'
    ELSE 'PENDING_PARSING'
END;

ALTER TABLE news.articles ALTER COLUMN parsing_status_id SET NOT NULL;
ALTER TABLE news.articles ALTER COLUMN parsing_status_id SET DEFAULT 1; -- PENDING_PARSING

DROP INDEX IF EXISTS news.idx_news_articles_status;
ALTER TABLE news.articles DROP COLUMN status;
DROP TYPE news.article_status;

CREATE INDEX ix_articles_parsing_status_id ON news.articles (parsing_status_id);

-- 3. news.annotations: from "text storage" to "job tracking, one row
-- per (article, language)", with status_id (FK) straight away.
-- status_id defaults to PENDING so a job can be created before the LLM
-- has run at all; annotation/neural_network only get filled in once it
-- has.
ALTER TABLE news.annotations ADD COLUMN status_id SMALLINT
    CONSTRAINT fk_annotations_status_id_annotation_statuses_id
    REFERENCES news.annotation_statuses(id);

-- Backfill: every existing row already has real annotation text — under
-- the old flow a row was only ever inserted once the text existed, so
-- by definition each one is already done.
UPDATE news.annotations a SET status_id = ans.id
FROM news.annotation_statuses ans WHERE ans.code = 'ANNOTATED';

ALTER TABLE news.annotations ALTER COLUMN status_id SET NOT NULL;
ALTER TABLE news.annotations ALTER COLUMN status_id SET DEFAULT 1; -- PENDING

ALTER TABLE news.annotations ALTER COLUMN annotation DROP NOT NULL;
ALTER TABLE news.annotations ALTER COLUMN neural_network DROP NOT NULL;

CREATE INDEX ix_annotations_status_id ON news.annotations (status_id);

-- 4. article_pipeline_log (00005): rename its existing FKs/index to the
-- convention, add language_id (an ANNOTATION-stage event's language;
-- NULL for PARSING events, which are article-level, not per-language),
-- and evolve status (VARCHAR+CHECK) -> status_id (FK).
ALTER TABLE news.article_pipeline_log
    RENAME CONSTRAINT article_pipeline_log_article_id_fkey
    TO fk_article_pipeline_log_article_id_articles_id;
ALTER TABLE news.article_pipeline_log
    RENAME CONSTRAINT article_pipeline_log_stage_id_fkey
    TO fk_article_pipeline_log_stage_id_pipeline_stages_id;

ALTER INDEX news.idx_article_pipeline_log_article_id
    RENAME TO ix_article_pipeline_log_article_id_started_at;

ALTER TABLE news.article_pipeline_log ADD COLUMN language_id BIGINT
    CONSTRAINT fk_article_pipeline_log_language_id_languages_id
    REFERENCES news.languages(id);

-- article_pipeline_status (00005) reads l.status directly, so it has to
-- go before status can be dropped, and gets rebuilt against status_id
-- right after.
DROP VIEW news.article_pipeline_status;

ALTER TABLE news.article_pipeline_log ADD COLUMN status_id SMALLINT
    CONSTRAINT fk_article_pipeline_log_status_id_pipeline_event_statuses_id
    REFERENCES news.pipeline_event_statuses(id);
UPDATE news.article_pipeline_log l SET status_id = pes.id
  FROM news.pipeline_event_statuses pes WHERE pes.code = l.status;
ALTER TABLE news.article_pipeline_log ALTER COLUMN status_id SET NOT NULL;
ALTER TABLE news.article_pipeline_log DROP CONSTRAINT article_pipeline_log_status_check;
-- idx_article_pipeline_log_stage_status (00005) covers (stage_id,
-- status) — Postgres drops a multi-column index outright when a column
-- it covers is dropped, so this disappears here too; recreated below
-- under the new name against status_id.
ALTER TABLE news.article_pipeline_log DROP COLUMN status;

CREATE INDEX ix_article_pipeline_log_stage_id_status_id
    ON news.article_pipeline_log (stage_id, status_id);

CREATE VIEW news.article_pipeline_status AS
SELECT DISTINCT ON (l.article_id)
    l.article_id,
    s.name AS stage_name,
    s.sequence_order,
    pes.code AS stage_status,
    l.error_message,
    l.started_at,
    l.finished_at
FROM news.article_pipeline_log l
JOIN news.pipeline_stages s ON s.id = l.stage_id
JOIN news.pipeline_event_statuses pes ON pes.id = l.status_id
ORDER BY l.article_id, l.started_at DESC;

-- +goose Down
DROP VIEW news.article_pipeline_status;

ALTER TABLE news.article_pipeline_log
    ADD COLUMN status VARCHAR(20) CHECK (status IN ('STARTED', 'SUCCEEDED', 'FAILED'));
UPDATE news.article_pipeline_log l SET status = pes.code
  FROM news.pipeline_event_statuses pes WHERE pes.id = l.status_id;
ALTER TABLE news.article_pipeline_log ALTER COLUMN status SET NOT NULL;

DROP INDEX IF EXISTS news.ix_article_pipeline_log_stage_id_status_id;
ALTER TABLE news.article_pipeline_log DROP COLUMN status_id;
ALTER TABLE news.article_pipeline_log DROP COLUMN language_id;

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

CREATE INDEX idx_article_pipeline_log_stage_status ON news.article_pipeline_log (stage_id, status);

ALTER INDEX news.ix_article_pipeline_log_article_id_started_at
    RENAME TO idx_article_pipeline_log_article_id;

ALTER TABLE news.article_pipeline_log
    RENAME CONSTRAINT fk_article_pipeline_log_stage_id_pipeline_stages_id
    TO article_pipeline_log_stage_id_fkey;
ALTER TABLE news.article_pipeline_log
    RENAME CONSTRAINT fk_article_pipeline_log_article_id_articles_id
    TO article_pipeline_log_article_id_fkey;

DROP INDEX IF EXISTS news.ix_annotations_status_id;
ALTER TABLE news.annotations ALTER COLUMN annotation SET NOT NULL;
ALTER TABLE news.annotations ALTER COLUMN neural_network SET NOT NULL;
ALTER TABLE news.annotations DROP COLUMN status_id;

DROP INDEX IF EXISTS news.ix_articles_parsing_status_id;
CREATE TYPE news.article_status AS ENUM (
    'PENDING_PARSING', 'PARSING', 'PARSED', 'PENDING_ANNOTATION', 'ANNOTATED', 'ERROR'
);
ALTER TABLE news.articles ADD COLUMN status news.article_status;
UPDATE news.articles a SET status = ps.code::news.article_status
  FROM news.parsing_statuses ps WHERE ps.id = a.parsing_status_id;
ALTER TABLE news.articles ALTER COLUMN status SET NOT NULL;
ALTER TABLE news.articles ALTER COLUMN status SET DEFAULT 'PENDING_PARSING';
CREATE INDEX idx_news_articles_status ON news.articles (status);
ALTER TABLE news.articles DROP COLUMN parsing_status_id;

ALTER TABLE news.pipeline_stages DROP COLUMN description;

DROP TABLE IF EXISTS news.pipeline_event_statuses;
DROP TABLE IF EXISTS news.annotation_statuses;
DROP TABLE IF EXISTS news.parsing_statuses;
