package routes

import (
	"go-gin-postgresql-backend/src/controllers"

	"github.com/gin-gonic/gin"
)

func GroupRouterPublic(baseRouter *gin.RouterGroup) {
	public := baseRouter.Group("/g")
	public.GET("/articles", controllers.GetAnnotation)
	public.GET("/articles/count", controllers.GetArticleWebCount)
	public.GET("/article/detailed", controllers.GetArticleDetails)
	public.GET("/article/search", controllers.GetArticleSearch)
}
