package utils

import (
	"go-gin-postgresql-backend/src/models"
)

func GetCheckArticleDB(article *models.CheckForExistingParsedArticle) (models.CheckForExistingParsedArticle, error) {

	err := models.DB.Raw(`SELECT EXISTS(SELECT 1 FROM articles WHERE source_link = ? );`, article.PostHref).Scan(&article).Error

	if err != nil {
		return models.CheckForExistingParsedArticle{}, err
	}

	return *article, nil
}
