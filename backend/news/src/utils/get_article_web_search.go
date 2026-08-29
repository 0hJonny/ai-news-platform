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
			themes.name AS theme_name,
			json_agg(tags.name) AS tags,
			annotations.annotation,
			lang.name AS language_name
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
			annotation_statuses ans ON ans.id = annotations.status_id
		LEFT JOIN
			titles ON articles.id = titles.article_id AND titles.language_id = lang.id
	`

	args := []interface{}{articleWebQuery.LanguageCode}

	// Sprintf, not a bind param, on purpose: this file already has a
	// hand-numbered $2 further down (in the content-match OR clause) —
	// inserting a new ? here would shift every later positional arg out
	// from under it. models.AnnotationStatusAnnotated is a fixed internal
	// constant, never request input, so this isn't an injection risk.
	if articleWebQuery.Category != "" {
		query += fmt.Sprintf(` WHERE themes.name = ? AND ans.code = '%s'`, models.AnnotationStatusAnnotated)
		args = append(args, articleWebQuery.Category)
	} else {
		query += fmt.Sprintf(` WHERE ans.code = '%s'`, models.AnnotationStatusAnnotated)
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
		AND (articles.id, lower(tags.name)) IN (SELECT articles.id, lower(unnest(?::text[])) AS tag_name FROM articles)
		`
		args = append(args, pq.Array(tags))
	}
	query += `
		GROUP BY articles.id, titles.title, themes.name, annotations.annotation, lang.name
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
