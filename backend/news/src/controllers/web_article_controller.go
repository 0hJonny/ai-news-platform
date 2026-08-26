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
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Invalid request payload", "data": nil})
		return
	}
	articles, err := utils.GetArticleWeb(&article)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Unable to get articles", "data": nil})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Articles fetched successfully", "data": articles})
}

func GetArticleWebCount(c *gin.Context) {
	var err error
	var article models.ArticleWebQuery
	err = c.ShouldBindQuery(&article)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Invalid request payload", "data": nil})
		return
	}
	count, err := utils.GetArticleWebCount(&article)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Unable to get articles", "data": nil})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Articles fetched successfully", "data": count})
}

func GetArticleDetails(c *gin.Context) {
	var err error
	var article models.ArticleWebQuery
	err = c.ShouldBindQuery(&article)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Invalid request payload", "data": nil})
		return
	}
	articleDetails, err := utils.GetArticleDetailsWeb(&article)

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Unable to get articles", "data": nil})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Articles fetched successfully", "data": articleDetails})
}

func GetArticleSearch(c *gin.Context) {
	var err error
	var article models.ArticleWebQuery
	err = c.ShouldBindQuery(&article)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Invalid request payload", "data": nil})
		return
	}
	articles, err := utils.GetArticleSearch(&article)

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "failed", "message": "Unable to get articles", "data": nil})
		return
	}
	// c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Articles fetched successfully", "data": articleDetails})
	c.JSON(http.StatusOK, gin.H{"status": "success", "message": "Articles fetched successfully", "data": articles})

}
