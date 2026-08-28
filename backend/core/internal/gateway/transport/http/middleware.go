package http

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/0hJonny/langfuse-agents/internal/gateway/upstream"
)

type contextKey string

const UserIDKey contextKey = "user_id"

type authErrorBody struct {
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}

// writeAuthError responds with a JSON body carrying a stable machine-readable
// code, so the frontend can tell an ordinary expiry (prompt to log back in)
// apart from a token that was never legitimately issued (tampered/malformed —
// treated as a harder failure that resets client-side auth state entirely).
func writeAuthError(w http.ResponseWriter, statusCode int, code, message string) {
	body := authErrorBody{}
	body.Error.Code = code
	body.Error.Message = message

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	_ = json.NewEncoder(w).Encode(body)
}

func AuthMiddleware(validator TokenValidator) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				writeAuthError(w, http.StatusUnauthorized, "TOKEN_MISSING", "Missing Authorization header")
				return
			}

			parts := strings.Split(authHeader, " ")
			if len(parts) != 2 || !strings.EqualFold(parts[0], "bearer") {
				writeAuthError(w, http.StatusUnauthorized, "TOKEN_INVALID", "Invalid Authorization header format")
				return
			}
			token := parts[1]

			// Call the validator we were given at initialization
			userID, err := validator.ValidateToken(r.Context(), token)
			if err != nil {
				switch {
				case errors.Is(err, upstream.ErrTokenExpired):
					writeAuthError(w, http.StatusUnauthorized, "TOKEN_EXPIRED", "Token expired, please log in again")
				case errors.Is(err, upstream.ErrTokenInvalid):
					// 403, not 401: distinguishes "this credential was never
					// valid" from an ordinary expiry so the client can react
					// differently (e.g. wipe local auth state instead of
					// just prompting to re-authenticate).
					writeAuthError(w, http.StatusForbidden, "TOKEN_INVALID", "Token is invalid")
				default:
					writeAuthError(w, http.StatusUnauthorized, "TOKEN_INVALID", "Invalid or expired token")
				}
				return
			}

			ctx := context.WithValue(r.Context(), UserIDKey, userID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func GetUserID(ctx context.Context) string {
	if id, ok := ctx.Value(UserIDKey).(string); ok {
		return id
	}
	return ""
}
