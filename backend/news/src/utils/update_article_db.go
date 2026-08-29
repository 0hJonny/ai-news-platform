package utils

import (
	"errors"

	"go-gin-postgresql-backend/src/models"
)

// ErrArticleNotFound is returned by UpdateParsingDB when articleID doesn't
// match any row — lets the controller answer 404 instead of a silent no-op.
var ErrArticleNotFound = errors.New("article not found")

// UpdateParsingDB is parsing.scrape_source's only write path: always
// updates ParsingStatus, plus whichever content fields the task actually
// produced — Author/Body directly on the row, Title upserted into titles
// against the article's own language_id (this is the article's native
// title, not a translation — that's the older /p/annotation flow's job).
// Never touches annotations; see CreateAnnotationJobDB/UpdateAnnotationDB
// for that side.
func UpdateParsingDB(articleID string, req *models.ParsingUpdateRequest) error {
	tx := models.DB.Begin()

	statusID, err := resolveParsingStatusID(tx, req.ParsingStatus)
	if err != nil {
		tx.Rollback()
		return err
	}

	result := tx.Exec(`UPDATE articles SET parsing_status_id = ? WHERE id = ?`, statusID, articleID)
	if result.Error != nil {
		tx.Rollback()
		return result.Error
	}
	if result.RowsAffected == 0 {
		tx.Rollback()
		return ErrArticleNotFound
	}

	if req.Author != nil {
		if err := tx.Exec(`UPDATE articles SET author = ? WHERE id = ?`, *req.Author, articleID).Error; err != nil {
			tx.Rollback()
			return err
		}
	}
	if req.Body != nil {
		if err := tx.Exec(`UPDATE articles SET body = ? WHERE id = ?`, *req.Body, articleID).Error; err != nil {
			tx.Rollback()
			return err
		}
	}

	if req.Title != nil {
		var languageID int
		if err := tx.Raw(`SELECT language_id FROM articles WHERE id = ?`, articleID).Scan(&languageID).Error; err != nil {
			tx.Rollback()
			return err
		}

		query := `
			INSERT INTO titles (article_id, title, language_id)
			VALUES (?, ?, ?)
			ON CONFLICT (article_id, language_id)
			DO UPDATE SET title = EXCLUDED.title
		`
		if err := tx.Exec(query, articleID, *req.Title, languageID).Error; err != nil {
			tx.Rollback()
			return err
		}
	}

	return tx.Commit().Error
}
