-- +goose Up
-- Stage 5: the producer now inserts a draft row (source_link + language
-- only, status PENDING_PARSING) before the parsing task has fetched
-- anything — author/body aren't known yet at that point, so they can no
-- longer be NOT NULL. The parsing task fills them in via
-- PATCH /p/articles/:id once it actually scrapes the page.
ALTER TABLE news.articles ALTER COLUMN author DROP NOT NULL;
ALTER TABLE news.articles ALTER COLUMN body DROP NOT NULL;

-- +goose Down
UPDATE news.articles SET author = '' WHERE author IS NULL;
UPDATE news.articles SET body = '' WHERE body IS NULL;
ALTER TABLE news.articles ALTER COLUMN author SET NOT NULL;
ALTER TABLE news.articles ALTER COLUMN body SET NOT NULL;
