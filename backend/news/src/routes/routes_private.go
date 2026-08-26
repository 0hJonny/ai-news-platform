package routes

import (
	"go-gin-postgresql-backend/src/controllers"
	"go-gin-postgresql-backend/src/middlewares"

	"github.com/gin-gonic/gin"
)

func GroupRouterPrivate(baseRouter *gin.RouterGroup) {
	protected := baseRouter.Group("/p")
	protected.Use(middlewares.AuthMiddleware())
	protected.POST("/article", controllers.CreateParsedArticle)
	protected.POST("/annotation", controllers.CreateArticleAnnotation)
	protected.GET("/article/:id", controllers.GetArticleByID)
	protected.GET("/article/check", controllers.CheckForExistingParsedArticle)
	protected.GET("/annotation/queue", controllers.GetAnnotationQueue)
}
