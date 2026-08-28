package http

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/0hJonny/langfuse-agents/internal/auth/domain"
)

func (h *Handler) HandleAnonymousAuth(w http.ResponseWriter, r *http.Request) {
	token, err := h.service.CreateAnonymous(r.Context())
	if err != nil {
		h.log.Error("failed to create anonymous user", "error", err)
		h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR")
		return
	}

	h.respondWithJSON(w, http.StatusCreated, TokenResponse{
		Token:     token.Value,
		ExpiresAt: token.ExpiresAt,
	})
}

func (h *Handler) HandleRegister(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_REQUEST")
		return
	}

	if req.Email == "" || req.Password == "" || req.Login == "" {
		h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_REQUEST")
		return
	}

	// If the caller already holds a valid (anonymous) session token, this
	// upgrades that account instead of creating a brand new one.
	anonUserID := h.extractUserIDFromToken(r)

	token, err := h.service.Register(r.Context(), req.Email, req.Password, req.Name, req.Login, anonUserID)
	if err != nil {
		switch {
		case errors.Is(err, domain.ErrInvalidEmail):
			h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_EMAIL")

		case errors.Is(err, domain.ErrInvalidLogin):
			h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_LOGIN")

		case errors.Is(err, domain.ErrLoginTaken):
			h.respondWithError(w, http.StatusConflict, "AUTH_LOGIN_TAKEN")

		case errors.Is(err, domain.ErrUserAlreadyExists):
			h.respondWithError(w, http.StatusConflict, "AUTH_EMAIL_TAKEN")

		default:
			h.log.Error("registration failed", "email", req.Email, "error", err)
			h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR")
		}
		return
	}

	h.respondWithJSON(w, http.StatusCreated, TokenResponse{
		Token:     token.Value,
		ExpiresAt: token.ExpiresAt,
	})
}

func (h *Handler) HandleLogin(w http.ResponseWriter, r *http.Request) {
	var req AuthRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_REQUEST")
		return
	}

	token, err := h.service.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidCreds) {
			h.respondWithError(w, http.StatusUnauthorized, "AUTH_INVALID_CREDENTIALS")
			return
		}
		h.log.Error("login failed", "email", req.Email, "error", err)
		h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR")
		return
	}

	h.respondWithJSON(w, http.StatusOK, TokenResponse{Token: token.Value, ExpiresAt: token.ExpiresAt})
}

// HandleCheckLoginAvailable is a public, read-only endpoint the register
// form calls (debounced) while the user edits the login field. A malformed
// login just comes back unavailable instead of erroring — the frontend
// already runs the same regex before ever calling this, so this branch only
// matters for a caller that skipped that check.
func (h *Handler) HandleCheckLoginAvailable(w http.ResponseWriter, r *http.Request) {
	login := r.URL.Query().Get("login")
	if login == "" {
		h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_REQUEST")
		return
	}

	available, err := h.service.CheckLoginAvailable(r.Context(), login)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidLogin) {
			h.respondWithJSON(w, http.StatusOK, LoginAvailabilityResponse{Available: false})
			return
		}
		h.log.Error("failed to check login availability", "login", login, "error", err)
		h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR")
		return
	}

	h.respondWithJSON(w, http.StatusOK, LoginAvailabilityResponse{Available: available})
}

func (h *Handler) HandleGetProfile(w http.ResponseWriter, r *http.Request) {
	userID := h.extractUserIDFromToken(r)
	if userID == "" {
		h.respondWithError(w, http.StatusUnauthorized, "TOKEN_MISSING")
		return
	}

	user, err := h.service.GetProfile(r.Context(), userID)
	if err != nil {
		if errors.Is(err, domain.ErrNotFound) {
			h.respondWithError(w, http.StatusNotFound, "AUTH_ACCOUNT_NOT_FOUND")
			return
		}
		h.log.Error("failed to fetch profile", "userID", userID, "error", err)
		h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR")
		return
	}

	email := ""
	if user.Email != nil {
		email = *user.Email
	}
	name := ""
	if user.Name != nil {
		name = *user.Name
	}
	login := ""
	if user.Login != nil {
		login = *user.Login
	}

	h.respondWithJSON(w, http.StatusOK, UserResponse{
		ID:    user.ID,
		Email: email,
		Name:  name,
		Login: login,
		Role:  string(user.Role),
	})
}
