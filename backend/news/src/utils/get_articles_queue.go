package utils

import (
	"go-gin-postgresql-backend/src/models"
)

func GetAnnotationQueue() (*[]models.ArticleQueryID, error) {
	var articleQueue []models.ArticleQueryID

	query := `
	SELECT 
		a.id AS article_id, 
		ln.language_code AS native_language,
		l.language_code,
		l.language_name
	FROM 
		articles a
	CROSS JOIN 
		languages l
	LEFT JOIN 
		languages ln ON a.language_id = ln.language_id
	LEFT JOIN 
		annotations an ON a.id = an.article_id AND l.language_id = an.language_id
	WHERE 
		an.article_id IS NULL
	ORDER BY a.post_date DESC;`

	err := models.DB.Raw(query).Scan(&articleQueue).Error

	if err != nil {
		return &[]models.ArticleQueryID{}, err
	}

	return &articleQueue, nil
}
