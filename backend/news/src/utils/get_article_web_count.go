package utils

import (
	"go-gin-postgresql-backend/src/models"
	"log"
)

func GetArticleWebCount(articleWebQuery *models.ArticleWebQuery) (*models.ArticleWebCount, error) {
	var err error
	var count models.ArticleWebCount

	log.Println("🔎🔎🔎 ArticleWebQuery: " + articleWebQuery.Category)

	args := []interface{}{}

	query := `
		SELECT 
			COUNT(articles.id)
		FROM 
			articles
		LEFT JOIN
			themes ON articles.theme_id = themes.id
		LEFT JOIN
			annotations ON articles.id = annotations.article_id
		LEFT JOIN
			annotation_statuses ans ON ans.id = annotations.status_id`

	if articleWebQuery.Category != "" {
		query += ` WHERE themes.name = ? AND ans.code = ?`
		args = append(args, articleWebQuery.Category, models.AnnotationStatusAnnotated)

	} else {
		query += ` WHERE ans.code = ?`
		args = append(args, models.AnnotationStatusAnnotated)
	}

	query += ` AND annotations.language_id = (SELECT id FROM languages WHERE code = ?);`
	args = append(args, articleWebQuery.LanguageCode)

	err = models.DB.Raw(query, args...).Count(&count.Count).Error
	if err != nil {
		return &models.ArticleWebCount{}, err
	}

	return &count, nil
}
