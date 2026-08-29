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

	// The Celery pipeline's ingest surface (producer + parsing +
	// annotation tasks). Deliberately not behind AuthMiddleware — see the
	// package doc comment on article_ingest_controller.go for why that's
	// safe here (news has no published port; only reachable from other
	// containers on platform-network).
	ingest := baseRouter.Group("/p/articles")
	ingest.POST("", controllers.CreateArticleDraft)
	ingest.GET("/:id", controllers.GetArticleDraft)
	ingest.PATCH("/:id/parsed", controllers.UpdateParsedArticle)
	ingest.POST("/:id/annotations", controllers.CreateAnnotationJob)
	ingest.POST("/:id/events", controllers.LogPipelineStage)

	// Annotation jobs are their own resource (one row per (article,
	// language), addressed by its own id) rather than nested under
	// articles — annotation.annotate_article gets the id straight from
	// CreateAnnotationJob's response, no article-scoped lookup needed.
	annotations := baseRouter.Group("/p/annotations")
	annotations.PATCH("/:id", controllers.UpdateAnnotation)
}
