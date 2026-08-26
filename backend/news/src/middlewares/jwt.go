// go-gin-postgresql-backend/src/middlewares/jwt.go

package middlewares

import (
	"os"

	"github.com/dgrijalva/jwt-go"
)

var JWTSecret = []byte(os.Getenv("JWT_SECRET_KEY"))

type Claims struct {
	UserID int `json:"user_id"`
	jwt.StandardClaims
}

func VerifyToken(tokenString string) (*jwt.Token, error) {
	claims := Claims{}
	return jwt.ParseWithClaims(tokenString, &claims, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, jwt.ErrSignatureInvalid
		}
		return JWTSecret, nil
	})
}
