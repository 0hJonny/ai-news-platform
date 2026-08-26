package utils

import (
	"encoding/base64"
	"go-gin-postgresql-backend/src/middlewares"
	"go-gin-postgresql-backend/src/models"
)

func CreateParsedArticleDB(parsedArticle *models.ParsedArticle) (models.ParsedArticle, error) {
	var err error
	tx := models.DB.Begin()

	parsedArticle.Language, err = GetLanguageIDByCode(&parsedArticle.Language)

	if err != nil {
		tx.Rollback()
		return models.ParsedArticle{}, err
	}

	err = tx.Raw("INSERT INTO articles (author, source_link, body, language_id, post_date) VALUES (?, ?, ?, ?, ?) RETURNING id", parsedArticle.Author, parsedArticle.PostHref, parsedArticle.Body, parsedArticle.Language.ID, parsedArticle.Date).Scan(&parsedArticle).Error
	if err != nil {
		tx.Rollback()
		return models.ParsedArticle{}, err
	}

	err = tx.Exec("INSERT INTO titles (article_id, title, language_id) VALUES (?, ?, ?)", parsedArticle.ID, parsedArticle.Title, parsedArticle.Language.ID).Error

	if err != nil {
		tx.Rollback()
		return models.ParsedArticle{}, err
	}

	minioClient, err := middlewares.NewMinioClient()

	if err != nil {
		tx.Rollback()
		return models.ParsedArticle{}, err
	}

	decodedImage, err := base64.StdEncoding.DecodeString(parsedArticle.Image)
	if err != nil {
		tx.Rollback()
		return models.ParsedArticle{}, err
	}
	err = minioClient.UploadFromBytes("images", parsedArticle.ID+".png", []byte(decodedImage))

	if err != nil {
		tx.Rollback()
		return models.ParsedArticle{}, err
	}

	err = tx.Commit().Error

	if err != nil {
		return models.ParsedArticle{}, err
	}

	return *parsedArticle, nil
}
