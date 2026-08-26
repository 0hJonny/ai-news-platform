package utils

import "go-gin-postgresql-backend/src/models"

func GetArticleByID(article *models.ArticleAnnotation) (models.ArticleAnnotation, error) {
	query := `
	SELECT 
		a.id AS article_id,
		t.title,
		a.body,
	CASE 
		WHEN EXISTS (
			SELECT 1 
			FROM annotations an 
			WHERE a.id = an.article_id
		) 
		THEN TRUE 
		ELSE FALSE 
	END AS has_annotation
	FROM 
		articles a
	LEFT JOIN 
		titles t ON a.id = t.article_id AND t.language_id = a.language_id
	WHERE 
		a.id = ?
	LIMIT 1;`

	if err := models.DB.Raw(query, article.ID).Scan(&article).Error; err != nil {
		return models.ArticleAnnotation{}, err
	}
	return *article, nil
}
