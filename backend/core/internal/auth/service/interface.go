package service

import (
	"context"

	"github.com/0hJonny/langfuse-agents/internal/auth/domain"
)

type AuthService interface {
	Register(ctx context.Context, email, password, name, anonUserID string) (Token, error)
	Login(ctx context.Context, email, password string) (Token, error)
	ValidateToken(ctx context.Context, tokenstring string) (string, error)
	CreateAnonymous(ctx context.Context) (Token, error)
	GetProfile(ctx context.Context, userID string) (domain.User, error)
}
