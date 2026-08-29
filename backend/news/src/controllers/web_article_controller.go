package controllers

import (
	"go-gin-postgresql-backend/src/models"
	"go-gin-postgresql-backend/src/utils"
	"net/http"

	"github.com/gin-gonic/gin"
)

func GetAnnotation(c *gin.Context) {
	var err error
	var article models.ArticleWebQuery
	err = c.ShouldBindQuery(&article)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgInvalidPayload)
		return
	}
	articles, err := utils.GetArticleWeb(&article)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgUnableToGetArticles)
		return
	}
	respondData(c, http.StatusOK, statusSuccess, msgArticlesFetched, articles)
}

func GetArticleWebCount(c *gin.Context) {
	var err error
	var article models.ArticleWebQuery
	err = c.ShouldBindQuery(&article)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgInvalidPayload)
		return
	}
	count, err := utils.GetArticleWebCount(&article)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgUnableToGetArticles)
		return
	}
	respondData(c, http.StatusOK, statusSuccess, msgArticlesFetched, count)
}

func GetArticleDetails(c *gin.Context) {
	var err error
	var article models.ArticleWebQuery
	err = c.ShouldBindQuery(&article)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgInvalidPayload)
		return
	}
	articleDetails, err := utils.GetArticleDetailsWeb(&article)

	if err != nil {
		respondError(c, http.StatusBadRequest, msgUnableToGetArticles)
		return
	}
	respondData(c, http.StatusOK, statusSuccess, msgArticlesFetched, articleDetails)
}

func GetArticleSearch(c *gin.Context) {
	var err error
	var article models.ArticleWebQuery
	err = c.ShouldBindQuery(&article)
	if err != nil {
		respondError(c, http.StatusBadRequest, msgInvalidPayload)
		return
	}
	articles, err := utils.GetArticleSearch(&article)

	if err != nil {
		respondError(c, http.StatusBadRequest, msgUnableToGetArticles)
		return
	}
	respondData(c, http.StatusOK, statusSuccess, msgArticlesFetched, articles)
}
