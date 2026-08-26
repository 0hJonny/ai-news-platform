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
			themes ON articles.theme_id = themes.theme_id
		LEFT JOIN 
			annotations ON articles.id = annotations.article_id`

	if articleWebQuery.Category != "" {
		query += ` WHERE themes.theme_name = ? AND annotations.article_id IS NOT NULL`
		args = append(args, articleWebQuery.Category)

	} else {
		query += ` WHERE annotations.article_id IS NOT NULL`
	}

	query += ` AND annotations.language_id = (SELECT language_id FROM languages WHERE language_code = ?);`
	args = append(args, articleWebQuery.LanguageCode)

	err = models.DB.Raw(query, args...).Count(&count.Count).Error
	if err != nil {
		return &models.ArticleWebCount{}, err
	}

	return &count, nil
}
