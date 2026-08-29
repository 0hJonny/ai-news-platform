package controllers

import (
	"go-gin-postgresql-backend/src/models"
	"go-gin-postgresql-backend/src/utils"
	"net/http"

	"github.com/gin-gonic/gin"
)

func CreateParsedArticle(c *gin.Context) {

	var err error
	var articleData models.ParsedArticle
	err = c.ShouldBindJSON(&articleData)

	if err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}

	articleData, err = utils.CreateParsedArticleDB(&articleData)

	if err != nil {
		respondError(c, http.StatusBadRequest, err.Error())
		return
	}

	respondData(c, http.StatusCreated, statusSuccess, msgArticleCreated, articleData.PostHref)
}

func CheckForExistingParsedArticle(c *gin.Context) {
	var err error
	var articleData models.CheckForExistingParsedArticle
	err = c.ShouldBindJSON(&articleData)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgInvalidPayload)
		return
	}
	articleData, err = utils.GetCheckArticleDB(&articleData)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgUnableToCheckArticle)
		return
	}
	respondData(c, http.StatusOK, statusSuccess, msgArticleFetched, articleData)
}
