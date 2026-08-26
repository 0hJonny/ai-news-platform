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
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	articleData, err = utils.CreateParsedArticleDB(&articleData)

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": err, "data": nil})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"status": "success", "message": "Article created successfully", "data": articleData.PostHref})
}

func CheckForExistingParsedArticle(c *gin.Context) {
	var err error
	var articleData models.CheckForExistingParsedArticle
	err = c.ShouldBindJSON(&articleData)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Invalid request payload", "data": nil})
		return
	}
	articleData, err = utils.GetCheckArticleDB(&articleData)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Unable to check article", "data": nil})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Article fetched successfully", "data": articleData})
}
