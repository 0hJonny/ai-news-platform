"""Single source of truth for every status/stage string the pipeline sends
across the wire to the Go API (backend/news). Both parser/tasks.py and
annotation/tasks.py import from here instead of typing the strings
themselves — rename a value once here, and every call site picks it up;
nobody has to grep tasks.py for a bare "PARSING" and hope they found every
occurrence.

These must stay in sync with the Go side's constants (models.ArticleStatus/
AnnotationStatus/PipelineEventStatus in backend/news/src/models/article.go)
and, ultimately, with the lookup tables' `code` columns
(news.parsing_statuses, news.annotation_statuses, news.pipeline_stages,
news.pipeline_event_statuses — see
sql/news/migrations/00007_normalize_status_lookups.sql). There's no
automatic check tying these two sides together (they're different
languages, different repos-within-the-repo) — if you rename a code in one,
rename it in the other and in the matching lookup-table row.
"""

# news.parsing_statuses.code — news.articles.parsing_status_id
PARSING_PENDING = "PENDING_PARSING"
PARSING_IN_PROGRESS = "PARSING"
PARSING_DONE = "PARSED"
PARSING_ERROR = "ERROR"

# news.annotation_statuses.code — news.annotations.status_id
ANNOTATION_PENDING = "PENDING"
ANNOTATION_IN_PROGRESS = "ANNOTATING"
ANNOTATION_DONE = "ANNOTATED"
ANNOTATION_ERROR = "ERROR"

# news.pipeline_stages.name — article_pipeline_log.stage_id, via
# POST /p/articles/:id/events's "stage" field
STAGE_PARSING = "PARSING"
STAGE_ANNOTATION = "ANNOTATION"

# news.pipeline_event_statuses.code — article_pipeline_log.status_id, via
# POST /p/articles/:id/events's "status" field
EVENT_STARTED = "STARTED"
EVENT_SUCCEEDED = "SUCCEEDED"
EVENT_FAILED = "FAILED"
