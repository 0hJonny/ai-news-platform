package utils

import (
	"errors"
	"fmt"
	"time"

	"go-gin-postgresql-backend/src/models"
)

// ErrUnknownPipelineStage is returned when the caller names a stage that
// isn't in news.pipeline_stages.
var ErrUnknownPipelineStage = errors.New("unknown pipeline stage")

// ErrUnknownPipelineEventStatus is returned when the caller names a status
// that isn't in news.pipeline_event_statuses.
var ErrUnknownPipelineEventStatus = errors.New("unknown pipeline event status")

// LogPipelineStageDB records one stage-attempt event for an article. Status
// "STARTED" leaves finished_at NULL; "SUCCEEDED"/"FAILED" stamps it — the
// lookup tables' FK constraints are the real validation, this just resolves
// the stage/status names to their ids and fills in the timestamp.
func LogPipelineStageDB(articleID string, event *models.PipelineStageEvent) error {
	var stageID int
	err := models.DB.Raw(`SELECT id FROM pipeline_stages WHERE name = ?`, event.Stage).Scan(&stageID).Error
	if err != nil {
		return err
	}
	if stageID == 0 {
		return fmt.Errorf("%w: %q", ErrUnknownPipelineStage, event.Stage)
	}

	statusID, err := resolvePipelineEventStatusID(models.DB, event.Status)
	if err != nil {
		return err
	}
	if statusID == 0 {
		return fmt.Errorf("%w: %q", ErrUnknownPipelineEventStatus, event.Status)
	}

	var finishedAt *time.Time
	if event.Status != string(models.PipelineEventStarted) {
		now := time.Now().UTC()
		finishedAt = &now
	}

	return models.DB.Exec(
		`INSERT INTO article_pipeline_log (article_id, stage_id, status_id, error_message, finished_at, language_id)
		 VALUES (?, ?, ?, ?, ?, ?)`,
		articleID, stageID, statusID, event.ErrorMessage, finishedAt, event.LanguageID,
	).Error
}
