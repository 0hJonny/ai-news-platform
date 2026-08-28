package utils

import (
	"fmt"
	"go-gin-postgresql-backend/src/models"
)

func GetArticleWeb(articleWebQuery *models.ArticleWebQuery) (*[]models.ArticleWeb, error) {
	var err error
	var articleWebCollection []models.ArticleWeb

	articleWebQuery.Offset = (articleWebQuery.Page - 1) * articleWebQuery.Limit

	query := `
		SELECT
			articles.id,
			COALESCE(titles.title, '') AS title,
			articles.created_at,
			themes.name AS theme_name,
			json_agg(tags.name) AS tags,
			annotations.annotation
		FROM
			articles
		LEFT JOIN
			themes ON articles.theme_id = themes.id
		LEFT JOIN
			article_tags ON articles.id = article_tags.article_id
		LEFT JOIN
			tags ON article_tags.tag_id = tags.id
		LEFT JOIN
			languages lang ON lang.code = ?
		LEFT JOIN
			annotations ON articles.id = annotations.article_id AND annotations.language_id = lang.id
		LEFT JOIN
			titles ON articles.id = titles.article_id AND titles.language_id = lang.id
	`

	args := []interface{}{articleWebQuery.LanguageCode}

	if articleWebQuery.Category != "" {
		query += ` WHERE themes.name = ? AND annotations.article_id IS NOT NULL`
		args = append(args, articleWebQuery.Category)
	} else {
		query += ` WHERE annotations.article_id IS NOT NULL`
	}

	query += `
		GROUP BY articles.id, titles.title, themes.name, annotations.annotation
		ORDER BY articles.post_date DESC
		LIMIT ? OFFSET ?;`

	args = append(args, articleWebQuery.Limit, articleWebQuery.Offset)

	err = models.DB.Raw(query, args...).Scan(&articleWebCollection).Error

	if err != nil {
		return &[]models.ArticleWeb{}, err
	}

	for i := range articleWebCollection {
		articleWebCollection[i].ImageSource = fmt.Sprintf("/images/%s.png", articleWebCollection[i].ID)
		articleWebCollection[i].LanguageCode = articleWebQuery.LanguageCode
	}

	return &articleWebCollection, nil
}
