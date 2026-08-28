package utils

import (
	"go-gin-postgresql-backend/src/models"
)

func CreateArticleAnnotationDB(articleData *models.ArticleAnnotation) (models.ArticleAnnotation, error) {
	var err error
	tx := models.DB.Begin()

	language := models.Language{
		Code: articleData.LanguageToAnswerCode}

	language, err = GetLanguageIDByCode(&language)

	if err != nil {
		tx.Rollback()
		return models.ArticleAnnotation{}, err
	}

	query := `SELECT language_id FROM articles WHERE id = ?`

	err = tx.Raw(query, articleData.ID).Scan(&articleData.LanguageID).Error
	if err != nil {
		tx.Rollback()
		return models.ArticleAnnotation{}, err
	}

	if articleData.LanguageID != language.ID {
		query = `
			INSERT INTO titles (article_id, title, language_id, neural_network)
			VALUES (?, ?, ?, ?)
		`
		err = tx.Exec(query, articleData.ID, articleData.Title, language.ID, articleData.NeuralNetworks["translator"]).Error
		if err != nil {
			tx.Rollback()
			return models.ArticleAnnotation{}, err
		}
	}

	if articleData.ThemeName != "" {
		query = `SELECT id AS theme_id FROM themes WHERE name = ?`
		err = tx.Raw(query, articleData.ThemeName).Scan(&articleData).Error
		if err != nil || articleData.ThemeID == 0 {
			tx.Rollback()
			return models.ArticleAnnotation{}, err
		}

		query = `UPDATE articles SET theme_id = ? WHERE id = ?`
		err = tx.Exec(query, articleData.ThemeID, articleData.ID).Error
		if err != nil {
			tx.Rollback()
			return models.ArticleAnnotation{}, err
		}
	}

	query = `
		INSERT INTO annotations (article_id, annotation, language_id, neural_network)
		VALUES (?, ?, ?, ?)
	`
	err = tx.Exec(query, articleData.ID, articleData.Annotation, language.ID, articleData.NeuralNetworks["annotator"]).Error
	if err != nil {
		tx.Rollback()
		return models.ArticleAnnotation{}, err
	}

	if len(articleData.Tags) != 0 {
		err = insertArticleWithTags(articleData.ID, articleData.Tags, tx)
	}

	if err != nil {
		tx.Rollback()
		return models.ArticleAnnotation{}, err
	}

	err = tx.Commit().Error

	if err != nil {
		return models.ArticleAnnotation{}, err
	}

	return *articleData, nil
}
