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
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Unable to get articles", "data": nil})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Articles fetched successfully", "data": articleQueue})
}

func GetArticleByID(c *gin.Context) {
	var err error
	var articleData models.ArticleAnnotation
	id := c.Param("id")
	if id == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Missing id in url", "data": nil})
		return
	}
	articleData.ID = id

	articleData, err = utils.GetArticleByID(&articleData)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Unable to get article", "data": nil})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Article fetched successfully", "data": articleData})
}

func CreateArticleAnnotation(c *gin.Context) {
	var err error
	var articleData models.ArticleAnnotation
	err = c.ShouldBindJSON(&articleData)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Invalid request payload", "data": nil})
		return
	}

	articleData, err = utils.CreateArticleAnnotationDB(&articleData)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": err, "data": nil})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"status": "success", "message": "Article created successfully", "data": articleData})
}
