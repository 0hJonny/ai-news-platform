package http

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"strings"

	"github.com/0hJonny/langfuse-agents/internal/auth/service"
)

type Handler struct {
	service service.AuthService
	log     *slog.Logger
}

func NewHandler(svc service.AuthService, log *slog.Logger) *Handler {
	return &Handler{
		service: svc,
		log:     log,
	}
}

func (h *Handler) respondWithError(w http.ResponseWriter, statusCode int, errCode string) {
	h.respondWithJSON(w, statusCode, ErrorResponse{Error: ErrorBody{Code: errCode, Message: messageForCode(errCode)}})
}

func (h *Handler) respondWithJSON(w http.ResponseWriter, code int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		h.log.Error("failed to encode json response", "error", err)
	}
}

// extractUserIDFromToken reads and validates the Authorization header,
// returning the subject of a valid token or "" if there isn't one. Used two
// ways: as an optional lookup during registration (upgrade an anonymous
// session instead of creating a fresh account) and as a mandatory one for
// the profile endpoint (caller checks for "" and rejects the request).
func (h *Handler) extractUserIDFromToken(r *http.Request) string {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return ""
	}

	// Split "Bearer <token>" on the space
	parts := strings.Split(authHeader, " ")
	if len(parts) != 2 || !strings.EqualFold(parts[0], "bearer") {
		return ""
	}

	// Validate the token via the service
	userID, err := h.service.ValidateToken(r.Context(), parts[1])
	if err != nil {
		return ""
	}

	return userID
}
