package utils

import (
	"go-gin-postgresql-backend/src/models"

	"gorm.io/gorm"
)

// resolveParsingStatusID, resolveAnnotationStatusID, and
// resolvePipelineEventStatusID all follow the same pattern already
// established for language_id (GetLanguageIDByCode) and stage_id
// (LogPipelineStageDB): the three status columns these back
// (news.articles.parsing_status_id, news.annotations.status_id,
// news.article_pipeline_log.status_id) are FKs into lookup tables, not
// Postgres ENUMs — see sql/news/migrations/00007_normalize_status_lookups.sql
// for why. db is passed in (rather than always using models.DB) so callers
// mid-transaction resolve against their own tx and stay atomic with it.

func resolveParsingStatusID(db *gorm.DB, code models.ArticleStatus) (int, error) {
	var id int
	err := db.Raw(`SELECT id FROM parsing_statuses WHERE code = ?`, code).Scan(&id).Error
	return id, err
}

func resolveAnnotationStatusID(db *gorm.DB, code models.AnnotationStatus) (int, error) {
	var id int
	err := db.Raw(`SELECT id FROM annotation_statuses WHERE code = ?`, code).Scan(&id).Error
	return id, err
}

func resolvePipelineEventStatusID(db *gorm.DB, code string) (int, error) {
	var id int
	err := db.Raw(`SELECT id FROM pipeline_event_statuses WHERE code = ?`, code).Scan(&id).Error
	return id, err
}
