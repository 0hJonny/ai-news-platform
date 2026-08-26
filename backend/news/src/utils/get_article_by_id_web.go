package utils

import (
	"fmt"
	"go-gin-postgresql-backend/src/models"
)

func GetArticleDetailsWeb(article *models.ArticleWebQuery) (*models.ArticleWeb, error) {
	var articleData models.ArticleWeb

	query := `
	SELECT 
		articles.id, 
		COALESCE(titles.title, '') AS title,
		articles.source_link,
		articles.created_at, 
		themes.theme_name,
		json_agg(tags.tag_name) AS tags,
		annotations.annotation,
		lang.language_code,
		jsonb_object_agg(
			'translator',
			COALESCE(titles.neural_network::text, '')
		) || jsonb_object_agg(
			'annotator',
			COALESCE(annotations.neural_network::text, '')
		) AS neural_networks
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

	WHERE annotations.article_id IS NOT NULL AND articles.id = ?

	GROUP BY articles.id, titles.title, themes.theme_name, annotations.annotation, lang.language_code
`

	if err := models.DB.Raw(query, article.LanguageCode, article.ArticleID).Scan(&articleData).Error; err != nil {
		return &models.ArticleWeb{}, err
	}

	articleData.ImageSource = fmt.Sprintf("/images/%s.png", articleData.ID)

	return &articleData, nil
}
