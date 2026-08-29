package utils

import (
	"errors"

	"go-gin-postgresql-backend/src/models"

	"github.com/jackc/pgx/v5/pgconn"
)

const pgUniqueViolation = "23505"

// CreateArticleDraftDB reserves a row for sourceLink if one doesn't exist
// yet — parsing_status PENDING_PARSING, author/body left NULL for the
// parsing task to fill in later via UpdateParsingDB. The upfront SELECT is
// just so a re-discovered URL gets its existing ID back with a normal
// response instead of a DB error; source_link's UNIQUE constraint is what
// actually guarantees no duplicate row, and the unique-violation fallback
// below covers the race where two producer runs insert the same link at
// once.
func CreateArticleDraftDB(sourceLink, languageCode string) (models.ArticleDraftResponse, error) {
	language, err := GetLanguageIDByCode(&models.Language{Code: languageCode})
	if err != nil {
		return models.ArticleDraftResponse{}, err
	}
	if language.ID == 0 {
		return models.ArticleDraftResponse{}, errors.New("unknown language_code")
	}

	if existing, found, err := findArticleBySourceLink(sourceLink); err != nil {
		return models.ArticleDraftResponse{}, err
	} else if found {
		return models.ArticleDraftResponse{ID: existing.ID, ParsingStatus: existing.ParsingStatus, Existed: true}, nil
	}

	// parsing_status_id isn't set explicitly — it defaults to 1
	// (PENDING_PARSING, see news.parsing_statuses), so a freshly created
	// draft's status is known without reading it back.
	var created models.ArticleDraftResponse
	err = models.DB.Raw(
		`INSERT INTO articles (source_link, language_id)
		 VALUES (?, ?)
		 RETURNING id`,
		sourceLink, language.ID,
	).Scan(&created).Error
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == pgUniqueViolation {
			existing, found, findErr := findArticleBySourceLink(sourceLink)
			if findErr != nil {
				return models.ArticleDraftResponse{}, findErr
			}
			if found {
				return models.ArticleDraftResponse{ID: existing.ID, ParsingStatus: existing.ParsingStatus, Existed: true}, nil
			}
		}
		return models.ArticleDraftResponse{}, err
	}
	created.ParsingStatus = models.ArticleStatusPendingParsing
	created.Existed = false

	return created, nil
}

func findArticleBySourceLink(sourceLink string) (models.ArticleDraftResponse, bool, error) {
	var row models.ArticleDraftResponse
	err := models.DB.Raw(
		`SELECT a.id, ps.code AS parsing_status
		 FROM articles a
		 JOIN parsing_statuses ps ON ps.id = a.parsing_status_id
		 WHERE a.source_link = ?
		 LIMIT 1`,
		sourceLink,
	).Scan(&row).Error
	if err != nil {
		return models.ArticleDraftResponse{}, false, err
	}
	return row, row.ID != "", nil
}
