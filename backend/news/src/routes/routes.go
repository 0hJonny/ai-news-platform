// go-gin-postgresql-backend/src/routes/startup.go

package routes

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func GroupRouter(baseRouter *gin.RouterGroup) {
	GroupRouterPrivate(baseRouter)
	GroupRouterPublic(baseRouter)
}

func SetupRoutes() *gin.Engine {

	router := gin.Default()

	// Liveness only (matches backend/core's auth/chats/gateway /health —
	// same "process is up" contract, not a DB/MinIO dependency check) so
	// docker-compose can gate depends_on: condition: service_healthy on it.
	router.GET("/health", func(c *gin.Context) {
		c.String(http.StatusOK, "OK")
	})

	// CORS is not configured here: news is not reachable from outside directly
	// (no port published in docker-compose) — all external requests go through
	// the Gateway (backend/core/internal/gateway), which is solely responsible for CORS.
	routerVersion := router.Group("/api/v1")
	GroupRouter(routerVersion)

	return router
}
