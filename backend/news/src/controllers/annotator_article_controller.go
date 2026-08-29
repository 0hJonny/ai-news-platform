package controllers

import (
	"go-gin-postgresql-backend/src/models"
	"go-gin-postgresql-backend/src/utils"
	"net/http"

	"github.com/gin-gonic/gin"
)

func GetAnnotationQueue(c *gin.Context) {

	articleQueue, err := utils.GetAnnotationQueue()

	if err != nil {
		respondError(c, http.StatusBadRequest, msgUnableToGetArticles)
		return
	}
	respondData(c, http.StatusOK, statusSuccess, msgArticlesFetched, articleQueue)
}

func GetArticleByID(c *gin.Context) {
	var err error
	var articleData models.ArticleAnnotation
	id := c.Param("id")
	if id == "" {
		respondError(c, http.StatusBadRequest, msgMissingID)
		return
	}
	articleData.ID = id

	articleData, err = utils.GetArticleByID(&articleData)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgUnableToGetArticle)
		return
	}
	respondData(c, http.StatusOK, statusSuccess, msgArticleFetched, articleData)
}

func CreateArticleAnnotation(c *gin.Context) {
	var err error
	var articleData models.ArticleAnnotation
	err = c.ShouldBindJSON(&articleData)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgInvalidPayload)
		return
	}

	articleData, err = utils.CreateArticleAnnotationDB(&articleData)
	if err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}
	respondData(c, http.StatusCreated, statusSuccess, msgArticleCreated, articleData)
}
