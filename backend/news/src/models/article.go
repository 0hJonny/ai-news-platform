// go-gin-postgresql-backend/src/models/article.go

package models

import "time"

// ArticleStatus is the parsing-only state machine parsing.scrape_source
// drives an article through. Backed by news.parsing_statuses (a lookup
// table, code -> id, see sql/news/migrations/00007_normalize_status_lookups.sql)
// rather than a Postgres ENUM — utils resolves the code to its id before
// writing news.articles.parsing_status_id, same pattern already used for
// language_id (GetLanguageIDByCode) and stage_id (LogPipelineStageDB).
// Annotation has its own status now (see AnnotationStatus): finishing
// parsing no longer implies anything about annotation, which may
// eventually run per-language and independently of this.
type ArticleStatus string

const (
	ArticleStatusPendingParsing ArticleStatus = "PENDING_PARSING"
	ArticleStatusParsing        ArticleStatus = "PARSING"
	ArticleStatusParsed         ArticleStatus = "PARSED"
	ArticleStatusError          ArticleStatus = "ERROR"
)

// AnnotationStatus is one annotation job's state, tracked per (article,
// language) row in news.annotations. Backed by news.annotation_statuses
// (lookup table, same resolve-code-to-id pattern as ArticleStatus above —
// see news.annotations.status_id). PENDING is the state a job starts in
// the moment it's created (before the LLM has run at all), which is what
// lets it exist as a row before there's any annotation text to put in it.
type AnnotationStatus string

const (
	AnnotationStatusPending    AnnotationStatus = "PENDING"
	AnnotationStatusAnnotating AnnotationStatus = "ANNOTATING"
	AnnotationStatusAnnotated  AnnotationStatus = "ANNOTATED"
	AnnotationStatusError      AnnotationStatus = "ERROR"
)

// PipelineEventStatus is one pipeline-stage attempt's outcome, backed by
// news.pipeline_event_statuses (same resolve-code-to-id pattern as
// ArticleStatus/AnnotationStatus). PipelineStageEvent.Status stays a plain
// string at the JSON-binding boundary (see its doc comment — Python sends
// whatever the caller names, DB FK is the real validation), but Go's own
// logic (e.g. LogPipelineStageDB deciding whether an event is terminal)
// compares against these named constants instead of a bare literal.
type PipelineEventStatus string

const (
	PipelineEventStarted   PipelineEventStatus = "STARTED"
	PipelineEventSucceeded PipelineEventStatus = "SUCCEEDED"
	PipelineEventFailed    PipelineEventStatus = "FAILED"
)

// Article is the GORM model for news.articles (table name resolved via the
// news,profiles,public search_path — see db.go). It's the full row the
// parsing task reads/updates by ParsingStatus; existing endpoints keep
// using their own narrower query-result structs (ArticleWeb,
// ArticleAnnotation, etc.) for reads that join in other tables.
type Article struct {
	ID         string `json:"id" gorm:"column:id;type:uuid;primaryKey"`
	Author     string `json:"author" gorm:"column:author"`
	SourceLink string `json:"source_link" gorm:"column:source_link"`
	Body       string `json:"body" gorm:"column:body"`
	ThemeID    *int64 `json:"theme_id,omitempty" gorm:"column:theme_id"`
	LanguageID int64  `json:"language_id" gorm:"column:language_id"`
	// Not a literal column anymore (see news.articles.parsing_status_id) —
	// callers populate this by aliasing the joined lookup table's code
	// column as parsing_status in their SELECT (GORM's Scan binds by
	// result column name, same as any other field here).
	ParsingStatus ArticleStatus `json:"parsing_status" gorm:"column:parsing_status"`
	PostDate      time.Time     `json:"post_date" gorm:"column:post_date"`
	CreatedAt     time.Time     `json:"created_at" gorm:"column:created_at;autoCreateTime"`
}

func (Article) TableName() string {
	return "articles"
}

// ArticleDraftRequest is the POST /p/articles payload (the producer's):
// all it knows about a candidate article before anything has been
// scraped is where it came from and what language it's in.
type ArticleDraftRequest struct {
	SourceLink   string `json:"source_link" binding:"required"`
	LanguageCode string `json:"language_code" binding:"required"`
}

// ArticleDraftResponse always carries the row's current ID and
// ParsingStatus, whether it was just created or already existed for that
// SourceLink — Existed tells the producer which case it got so it knows
// whether to enqueue a fresh parsing.scrape_source task or leave an
// in-flight/done article alone.
type ArticleDraftResponse struct {
	ID            string        `json:"id"`
	ParsingStatus ArticleStatus `json:"parsing_status"`
	Existed       bool          `json:"existed"`
}

// ParsingUpdateRequest is the PATCH /p/articles/:id/parsed payload —
// parsing.scrape_source's only write path. Title/Author/Body are pointers
// so a failure report (just ParsingStatus: ERROR) doesn't have to send
// empty strings for content it never produced.
type ParsingUpdateRequest struct {
	ParsingStatus ArticleStatus `json:"parsing_status" binding:"required"`
	Title         *string       `json:"title,omitempty"`
	Author        *string       `json:"author,omitempty"`
	Body          *string       `json:"body,omitempty"`
}

// AnnotationCreateRequest is the POST /p/articles/:id/annotations
// payload — LanguageCode is optional, defaulting to the article's own
// language, so today's single-language call site doesn't have to know its
// own language code just to ask for a job.
type AnnotationCreateRequest struct {
	LanguageCode *string `json:"language_code,omitempty"`
}

// AnnotationJob is both AnnotationCreateRequest's response and
// UpdateAnnotationDB's identity: one row in news.annotations. Existed
// mirrors ArticleDraftResponse's — true if a job for this (article,
// language) pair already existed, so the caller knows not to enqueue a
// duplicate annotation.annotate_article.
type AnnotationJob struct {
	ID         string           `json:"id"`
	ArticleID  string           `json:"article_id"`
	LanguageID int64            `json:"language_id"`
	Status     AnnotationStatus `json:"status"`
	Existed    bool             `json:"existed"`
}

// AnnotationUpdateRequest is the PATCH /p/annotations/:id payload —
// annotation.annotate_article's only write path, addressing one job row
// directly by its own id rather than by (article, language).
type AnnotationUpdateRequest struct {
	Status        AnnotationStatus `json:"status" binding:"required"`
	Annotation    *string          `json:"annotation,omitempty"`
	NeuralNetwork *string          `json:"neural_network,omitempty"`
}

// PipelineStageEvent is the POST /p/articles/:id/events payload — one
// attempt at one stage. Both tasks call this at the start of their work
// (Status: "STARTED") and again when they finish ("SUCCEEDED" or
// "FAILED", with ErrorMessage set on failure), independently of the
// ParsingUpdateRequest/AnnotationUpdateRequest PATCHes that update current
// state. LanguageID is only meaningful (and only sent) for ANNOTATION-stage
// events — PARSING is article-level, not per-language, so it stays nil
// there. Stage/Status are plain strings, not typed enums: they're
// validated by the pipeline_stages/pipeline_event_statuses lookup tables'
// FK constraints (see sql/news/migrations/00005_add_pipeline_stage_log.sql,
// 00007_normalize_status_lookups.sql) rather than duplicating that
// contract in Go.
type PipelineStageEvent struct {
	Stage        string  `json:"stage" binding:"required"`
	Status       string  `json:"status" binding:"required"`
	ErrorMessage *string `json:"error_message,omitempty"`
	LanguageID   *int64  `json:"language_id,omitempty"`
}
