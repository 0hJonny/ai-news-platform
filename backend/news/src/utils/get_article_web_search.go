package utils

import (
	"fmt"
	"go-gin-postgresql-backend/src/models"
	"strings"

	"github.com/lib/pq"
)

func GetArticleSearch(articleWebQuery *models.ArticleWebQuery) (*[]models.ArticleWeb, error) {
	var err error
	var articleWebCollection []models.ArticleWeb

	articleWebQuery.Offset = (articleWebQuery.Page - 1) * articleWebQuery.Limit

	var content string
	var tags []string

	parsedQuery := strings.ReplaceAll(articleWebQuery.Query, "\\", "")
	queryParts := strings.Split(parsedQuery, "!!")
	content = queryParts[0]
	for _, tag := range queryParts[1:] {
		if tag == "" {
			continue
		}
		tags = append(tags, strings.TrimSpace(strings.Trim(tag, " ")))
	}

	query := `
		SELECT 
			articles.id, 
			COALESCE(titles.title, '') AS title, 
			articles.created_at, 
			themes.theme_name,
			json_agg(tags.tag_name) AS tags,
			annotations.annotation,
			lang.language_name
		FROM 
			articles
		LEFT JOIN 
			themes ON articles.theme_id = themes.theme_id
		LEFT JOIN 
			article_tags ON articles.id = article_tags.article_id
		LEFT JOIN 
			tags ON article_tags.tag_id = tags.tag_id
		LEFT JOIN 
			languages lang ON lang.language_code = ?
		LEFT JOIN 
			annotations ON articles.id = annotations.article_id AND annotations.language_id = lang.language_id
		LEFT JOIN 
			titles ON articles.id = titles.article_id AND titles.language_id = lang.language_id
	`

	args := []interface{}{articleWebQuery.LanguageCode}

	if articleWebQuery.Category != "" {
		query += ` WHERE themes.theme_name = ? AND annotations.article_id IS NOT NULL`
		args = append(args, articleWebQuery.Category)
	} else {
		query += ` WHERE annotations.article_id IS NOT NULL`
	}

	if content != "" {
		query += `
		AND (to_tsvector('simple', COALESCE(titles.title, '')) @@ plainto_tsquery('simple', $2)
		OR to_tsvector('simple', COALESCE(annotations.annotation, '')) @@ plainto_tsquery('simple', ?))
		`
		args = append(args, content)

	}
	if len(tags) > 0 {
		query += `
		AND (articles.id, lower(tags.tag_name)) IN (SELECT articles.id, lower(unnest(?::text[])) AS tag_name FROM articles)
		`
		args = append(args, pq.Array(tags))
	}
	query += `
		GROUP BY articles.id, titles.title, themes.theme_name, annotations.annotation, lang.language_name
		LIMIT ? OFFSET ?;`

	args = append(args, articleWebQuery.Limit, articleWebQuery.Offset)

	err = models.DB.Raw(query, args...).Scan(&articleWebCollection).Error

	// log.Printf("articleWebCollection: %+v", articleWebCollection)

	if err != nil {
		return &[]models.ArticleWeb{}, err
	}

	for i := range articleWebCollection {
		articleWebCollection[i].ImageSource = fmt.Sprintf("/images/%s.png", articleWebCollection[i].ID)
		articleWebCollection[i].LanguageCode = articleWebQuery.LanguageCode
	}

	return &articleWebCollection, nil
}
