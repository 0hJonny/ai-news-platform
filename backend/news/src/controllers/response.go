package controllers

import "github.com/gin-gonic/gin"

// Response status values for every controller's JSON body.
const (
	statusSuccess  = "success"
	statusFailed   = "failed"
	statusConflict = "conflict"
)

// Response messages, named so nothing in a c.JSON call is a bare string
// literal. A message that varies at runtime (typically err.Error()) is
// passed straight through instead — only the fixed, repeated wording lives
// here.
const (
	msgMissingID            = "Missing id in url"
	msgArticleNotFound      = "Article not found"
	msgArticleAlreadyExists = "Article already exists"
	msgDraftCreated         = "Draft created"
	msgArticleUpdated       = "Article updated"
	msgArticleFetched       = "Article fetched successfully"
	msgArticleCreated       = "Article created successfully"
	msgArticlesFetched      = "Articles fetched successfully"
	msgInvalidPayload       = "Invalid request payload"
	msgUnableToGetArticles  = "Unable to get articles"
	msgUnableToGetArticle   = "Unable to get article"
	msgUnableToCheckArticle = "Unable to check article"
	msgStageLogged          = "Stage event logged"

	msgAnnotationJobCreated    = "Annotation job created"
	msgAnnotationAlreadyExists = "Annotation job already exists"
	msgAnnotationUpdated       = "Annotation job updated"
	msgAnnotationNotFound      = "Annotation job not found"
)

// apiResponse is the {status, message, data} shape every controller
// answers with — a typed struct instead of a gin.H literal per call site,
// so the field set can't drift between handlers.
type apiResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
	Data    any    `json:"data"`
}

func respondError(c *gin.Context, httpStatus int, message string) {
	c.JSON(httpStatus, apiResponse{Status: statusFailed, Message: message, Data: nil})
}

func respondData(c *gin.Context, httpStatus int, status, message string, data any) {
	c.JSON(httpStatus, apiResponse{Status: status, Message: message, Data: data})
}
