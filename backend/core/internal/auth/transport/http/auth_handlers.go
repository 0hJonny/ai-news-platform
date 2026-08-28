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
		h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to authenticate anonymously")
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
		h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_REQUEST", "invalid request payload")
		return
	}

	if req.Email == "" || req.Password == "" {
		h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_REQUEST", "email and password are required")
		return
	}

	// If the caller already holds a valid (anonymous) session token, this
	// upgrades that account instead of creating a brand new one.
	anonUserID := h.extractUserIDFromToken(r)

	token, err := h.service.Register(r.Context(), req.Email, req.Password, req.Name, anonUserID)
	if err != nil {
		switch {
		case errors.Is(err, domain.ErrInvalidEmail):
			h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_EMAIL", "invalid email format")

		case errors.Is(err, domain.ErrUserAlreadyExists):
			h.respondWithError(w, http.StatusConflict, "AUTH_EMAIL_TAKEN", "email already registered")

		default:
			h.log.Error("registration failed", "email", req.Email, "error", err)
			h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to register user")
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
		h.respondWithError(w, http.StatusBadRequest, "AUTH_INVALID_REQUEST", "invalid request payload")
		return
	}

	token, err := h.service.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidCreds) {
			h.respondWithError(w, http.StatusUnauthorized, "AUTH_INVALID_CREDENTIALS", "invalid email or password")
			return
		}
		h.log.Error("login failed", "email", req.Email, "error", err)
		h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "internal server error")
		return
	}

	h.respondWithJSON(w, http.StatusOK, TokenResponse{Token: token.Value, ExpiresAt: token.ExpiresAt})
}

func (h *Handler) HandleGetProfile(w http.ResponseWriter, r *http.Request) {
	userID := h.extractUserIDFromToken(r)
	if userID == "" {
		h.respondWithError(w, http.StatusUnauthorized, "TOKEN_MISSING", "missing or invalid token")
		return
	}

	user, err := h.service.GetProfile(r.Context(), userID)
	if err != nil {
		if errors.Is(err, domain.ErrNotFound) {
			h.respondWithError(w, http.StatusNotFound, "AUTH_ACCOUNT_NOT_FOUND", "user not found")
			return
		}
		h.log.Error("failed to fetch profile", "userID", userID, "error", err)
		h.respondWithError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "failed to fetch profile")
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

	h.respondWithJSON(w, http.StatusOK, UserResponse{
		ID:    user.ID,
		Email: email,
		Name:  name,
		Role:  string(user.Role),
	})
}
