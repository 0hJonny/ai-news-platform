// go-gin-postgresql-backend/src/middlewares/middlewares.go

package middlewares

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		token := c.GetHeader("Authorization")
		if token == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"status":  "failed",
				"message": "Unauthorized to access this resource",
			})
			return
		}

		token = strings.Split(token, " ")[1]
		_, err := VerifyToken(token)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"status":  "failed",
				"message": "Unauthorized to access this resource",
			})
			return
		}
		c.Next()
	}
}

func RegisterMiddleware(router *gin.Engine) {
	router.Use(AuthMiddleware())
}
