// The Celery pipeline's ingest surface. POST /p/articles creates
// a draft row; PATCH /p/articles/:id/parsed is parsing.scrape_source's
// only write path; POST /p/articles/:id/annotations reserves an
// annotation job (one per (article, language) pair) that
// annotation.annotate_article then owns via PATCH /p/annotations/:id.
// Split this way — instead of one generic update endpoint — because
// parsing and annotation are different tasks with different fields and
// different tables (see article_pipeline_response.go's package doc for
// the reasoning); it also means multiple annotation jobs per article
// (multi-language) need no further API change, just more POST calls.
// Deliberately not behind AuthMiddleware (see routes/routes_private.go) —
// news isn't published outside the docker network, so these are reachable
// only from other containers on platform-network, same as the Gateway's
// own internal-only routes.
package controllers

import (
	"errors"
	"net/http"

	"go-gin-postgresql-backend/src/models"
	"go-gin-postgresql-backend/src/utils"

	"github.com/gin-gonic/gin"
)

// parsingUpdateResult is UpdateParsedArticle's success payload.
type parsingUpdateResult struct {
	ID            string               `json:"id"`
	ParsingStatus models.ArticleStatus `json:"parsing_status"`
}

// annotationUpdateResult is UpdateAnnotation's success payload.
type annotationUpdateResult struct {
	ID     string                  `json:"id"`
	Status models.AnnotationStatus `json:"status"`
}

func CreateArticleDraft(c *gin.Context) {
	var req models.ArticleDraftRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}

	draft, err := utils.CreateArticleDraftDB(req.SourceLink, req.LanguageCode)
	if err != nil {
		respondError(c, http.StatusInternalServerError, err.Error())
		return
	}

	if draft.Existed {
		// 409, not 200: the producer's whole point in calling this is to
		// decide whether to enqueue parsing.scrape_source — Existed=true
		// in the body would be easy to miss, a non-2xx status isn't.
		respondData(c, http.StatusConflict, statusConflict, msgArticleAlreadyExists, draft)
		return
	}

	respondData(c, http.StatusCreated, statusSuccess, msgDraftCreated, draft)
}

func GetArticleDraft(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		respondError(c, http.StatusBadRequest, msgMissingID)
		return
	}

	article, found, err := utils.GetArticleDB(id)
	if err != nil {
		respondError(c, http.StatusInternalServerError, err.Error())
		return
	}
	if !found {
		respondError(c, http.StatusNotFound, msgArticleNotFound)
		return
	}

	respondData(c, http.StatusOK, statusSuccess, msgArticleFetched, article)
}

// UpdateParsedArticle is PATCH /p/articles/:id/parsed — parsing.scrape_source's
// only write path. Never touches annotations; see CreateAnnotationJob/
// UpdateAnnotation for that side.
func UpdateParsedArticle(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		respondError(c, http.StatusBadRequest, msgMissingID)
		return
	}

	var req models.ParsingUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}

	if err := utils.UpdateParsingDB(id, &req); err != nil {
		if errors.Is(err, utils.ErrArticleNotFound) {
			respondError(c, http.StatusNotFound, msgArticleNotFound)
			return
		}
		respondError(c, http.StatusInternalServerError, err.Error())
		return
	}

	respondData(c, http.StatusOK, statusSuccess, msgArticleUpdated, parsingUpdateResult{ID: id, ParsingStatus: req.ParsingStatus})
}

// CreateAnnotationJob is POST /p/articles/:id/annotations — reserves a
// PENDING annotation job for (article, language) if one doesn't already
// exist. Same create-or-hand-back-existing shape as CreateArticleDraft.
func CreateAnnotationJob(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		respondError(c, http.StatusBadRequest, msgMissingID)
		return
	}

	// Callers send a plain {} when they want the article's own language —
	// LanguageCode has no `binding:"required"`, so an absent/null field
	// just leaves it nil.
	var req models.AnnotationCreateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}

	job, err := utils.CreateAnnotationJobDB(id, &req)
	if err != nil {
		respondError(c, http.StatusInternalServerError, err.Error())
		return
	}

	if job.Existed {
		respondData(c, http.StatusConflict, statusConflict, msgAnnotationAlreadyExists, job)
		return
	}

	respondData(c, http.StatusCreated, statusSuccess, msgAnnotationJobCreated, job)
}

// UpdateAnnotation is PATCH /p/annotations/:id — annotation.annotate_article's
// only write path, addressing one job row directly by its own id.
func UpdateAnnotation(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		respondError(c, http.StatusBadRequest, msgMissingID)
		return
	}

	var req models.AnnotationUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}

	if err := utils.UpdateAnnotationDB(id, &req); err != nil {
		if errors.Is(err, utils.ErrAnnotationNotFound) {
			respondError(c, http.StatusNotFound, msgAnnotationNotFound)
			return
		}
		respondError(c, http.StatusInternalServerError, err.Error())
		return
	}

	respondData(c, http.StatusOK, statusSuccess, msgAnnotationUpdated, annotationUpdateResult{ID: id, Status: req.Status})
}

// LogPipelineStage records one stage-attempt event (started/succeeded/
// failed) for an article — see models.PipelineStageEvent. Separate from
// the PATCH endpoints on purpose: this is an append-only event log, not a
// current-state update, so it never overwrites anything.
func LogPipelineStage(c *gin.Context) {
	id := c.Param("id")
	if id == "" {
		respondError(c, http.StatusBadRequest, msgMissingID)
		return
	}

	var event models.PipelineStageEvent
	if err := c.ShouldBindJSON(&event); err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}

	if err := utils.LogPipelineStageDB(id, &event); err != nil {
		if errors.Is(err, utils.ErrUnknownPipelineStage) {
			respondError(c, http.StatusBadRequest, err.Error())
			return
		}
		respondError(c, http.StatusInternalServerError, err.Error())
		return
	}

	respondData(c, http.StatusCreated, statusSuccess, msgStageLogged, nil)
}
