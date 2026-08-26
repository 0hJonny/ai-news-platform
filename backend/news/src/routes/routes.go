// go-gin-postgresql-backend/src/routes/startup.go

package routes

import (
	"github.com/gin-gonic/gin"
)

func GroupRouter(baseRouter *gin.RouterGroup) {
	GroupRouterPrivate(baseRouter)
	GroupRouterPublic(baseRouter)
}

func SetupRoutes() *gin.Engine {

	router := gin.Default()

	// CORS is not configured here: news is not reachable from outside directly
	// (no port published in docker-compose) — all external requests go through
	// the Gateway (backend/core/internal/gateway), which is solely responsible for CORS.
	routerVersion := router.Group("/api/v1")
	GroupRouter(routerVersion)

	return router
}
