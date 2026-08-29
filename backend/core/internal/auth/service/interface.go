package service

import (
	"context"

	"github.com/0hJonny/langfuse-agents/internal/auth/domain"
)

type AuthService interface {
	Register(ctx context.Context, email, password, name, login, anonUserID string) (Token, error)
	// Login accepts either an email or a login/username as identifier.
	Login(ctx context.Context, identifier, password string) (Token, error)
	ValidateToken(ctx context.Context, tokenstring string) (string, error)
	CreateAnonymous(ctx context.Context) (Token, error)
	GetProfile(ctx context.Context, userID string) (domain.User, error)
	// CheckLoginAvailable is a read-only lookup for the registration form's
	// live availability check — see domain.UserRepository.IsLoginAvailable.
	CheckLoginAvailable(ctx context.Context, login string) (bool, error)
}
