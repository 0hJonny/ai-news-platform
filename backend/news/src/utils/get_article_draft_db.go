package utils

import "go-gin-postgresql-backend/src/models"

// ArticleDetail is GET /p/articles/:id's response shape: the raw
// news.articles row plus its native-language title (news.titles has no
// row yet if the parsing task hasn't reached this article, hence the
// pointer) — the annotation task needs both Title and Body to build its
// LLM prompt, and Title isn't a column on articles itself.
type ArticleDetail struct {
	models.Article
	Title *string `json:"title,omitempty"`
}

// GetArticleDB fetches the raw news.articles row (plus its own-language
// title, if any) by ID — used by GET /p/articles/:id, which the
// annotation task reads Title/Body from before running the article
// through the LLM. Distinct from GetArticleByID (models.ArticleAnnotation),
// which serves the older /p/article/:id endpoint and doesn't carry
// ParsingStatus.
func GetArticleDB(articleID string) (ArticleDetail, bool, error) {
	var article ArticleDetail
	err := models.DB.Raw(
		`SELECT a.id, a.author, a.source_link, a.body, a.theme_id, a.language_id,
		        ps.code AS parsing_status, a.post_date, a.created_at, t.title
		 FROM articles a
		 JOIN parsing_statuses ps ON ps.id = a.parsing_status_id
		 LEFT JOIN titles t ON t.article_id = a.id AND t.language_id = a.language_id
		 WHERE a.id = ?
		 LIMIT 1`,
		articleID,
	).Scan(&article).Error
	if err != nil {
		return ArticleDetail{}, false, err
	}
	return article, article.ID != "", nil
}
