package utils

import (
	"errors"

	"go-gin-postgresql-backend/src/models"

	"github.com/jackc/pgx/v5/pgconn"
)

// ErrAnnotationNotFound is returned by UpdateAnnotationDB when
// annotationID doesn't match any row.
var ErrAnnotationNotFound = errors.New("annotation job not found")

// CreateAnnotationJobDB reserves a PENDING annotation job for (articleID,
// language) if one doesn't exist yet — language comes from req.LanguageCode
// when given, or from the article's own language otherwise (today's only
// call site: parsing.scrape_source asking for its own article's native
// language). Same existing-row-wins pattern as CreateArticleDraftDB: the
// UNIQUE(article_id, language_id) constraint on annotations is what
// actually guarantees one job per (article, language), this just hands
// back the existing job instead of erroring when there already is one.
func CreateAnnotationJobDB(articleID string, req *models.AnnotationCreateRequest) (models.AnnotationJob, error) {
	languageID, err := resolveAnnotationLanguageID(articleID, req)
	if err != nil {
		return models.AnnotationJob{}, err
	}

	if existing, found, err := findAnnotationJob(articleID, languageID); err != nil {
		return models.AnnotationJob{}, err
	} else if found {
		existing.Existed = true
		return existing, nil
	}

	// status_id isn't set explicitly — it defaults to 1 (PENDING, see
	// news.annotation_statuses), so a freshly created job's status is
	// known without reading it back.
	var created models.AnnotationJob
	err = models.DB.Raw(
		`INSERT INTO annotations (article_id, language_id)
		 VALUES (?, ?)
		 RETURNING id, article_id, language_id`,
		articleID, languageID,
	).Scan(&created).Error
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == pgUniqueViolation {
			existing, found, findErr := findAnnotationJob(articleID, languageID)
			if findErr != nil {
				return models.AnnotationJob{}, findErr
			}
			if found {
				existing.Existed = true
				return existing, nil
			}
		}
		return models.AnnotationJob{}, err
	}
	created.Status = models.AnnotationStatusPending
	created.Existed = false

	return created, nil
}

func resolveAnnotationLanguageID(articleID string, req *models.AnnotationCreateRequest) (int64, error) {
	if req.LanguageCode != nil && *req.LanguageCode != "" {
		language, err := GetLanguageIDByCode(&models.Language{Code: *req.LanguageCode})
		if err != nil {
			return 0, err
		}
		if language.ID == 0 {
			return 0, errors.New("unknown language_code")
		}
		return int64(language.ID), nil
	}

	var languageID int64
	err := models.DB.Raw(`SELECT language_id FROM articles WHERE id = ?`, articleID).Scan(&languageID).Error
	if err != nil {
		return 0, err
	}
	return languageID, nil
}

func findAnnotationJob(articleID string, languageID int64) (models.AnnotationJob, bool, error) {
	var row models.AnnotationJob
	err := models.DB.Raw(
		`SELECT a.id, a.article_id, a.language_id, ans.code AS status
		 FROM annotations a
		 JOIN annotation_statuses ans ON ans.id = a.status_id
		 WHERE a.article_id = ? AND a.language_id = ?
		 LIMIT 1`,
		articleID, languageID,
	).Scan(&row).Error
	if err != nil {
		return models.AnnotationJob{}, false, err
	}
	return row, row.ID != "", nil
}

// UpdateAnnotationDB is annotation.annotate_article's only write path:
// updates the job row's Status, plus Annotation/NeuralNetwork once the LLM
// has actually produced them. Addresses the row by its own id (returned
// from CreateAnnotationJobDB), not by (article, language) — the task
// already has it, no need to re-derive.
func UpdateAnnotationDB(annotationID string, req *models.AnnotationUpdateRequest) error {
	tx := models.DB.Begin()

	statusID, err := resolveAnnotationStatusID(tx, req.Status)
	if err != nil {
		tx.Rollback()
		return err
	}

	result := tx.Exec(`UPDATE annotations SET status_id = ? WHERE id = ?`, statusID, annotationID)
	if result.Error != nil {
		tx.Rollback()
		return result.Error
	}
	if result.RowsAffected == 0 {
		tx.Rollback()
		return ErrAnnotationNotFound
	}

	if req.Annotation != nil {
		if err := tx.Exec(`UPDATE annotations SET annotation = ? WHERE id = ?`, *req.Annotation, annotationID).Error; err != nil {
			tx.Rollback()
			return err
		}
	}
	if req.NeuralNetwork != nil {
		if err := tx.Exec(`UPDATE annotations SET neural_network = ? WHERE id = ?`, *req.NeuralNetwork, annotationID).Error; err != nil {
			tx.Rollback()
			return err
		}
	}

	return tx.Commit().Error
}
