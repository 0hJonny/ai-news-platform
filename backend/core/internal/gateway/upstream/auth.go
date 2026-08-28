package upstream

import (
	"context"
	"errors"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"github.com/0hJonny/langfuse-agents/pkg/authclient/pb"
)

// ErrTokenExpired and ErrTokenInvalid let the HTTP layer tell "please log in
// again" apart from "this token was never legitimately issued" without
// depending on the auth service's internal domain package.
var (
	ErrTokenExpired = errors.New("token expired")
	ErrTokenInvalid = errors.New("token invalid")
)

type AuthServiceClientAdapter struct {
	client pb.AuthServiceClient
	// redisClient *redis.Client will be added here in the future
}

func NewAuthServiceClientAdapter(client pb.AuthServiceClient) *AuthServiceClientAdapter {
	return &AuthServiceClientAdapter{client: client}
}

// ValidateToken implements the http.TokenValidator interface
func (a *AuthServiceClientAdapter) ValidateToken(ctx context.Context, token string) (string, error) {
	// Future Redis blacklist logic:
	// isBlacklisted, _ := a.redis.Exists(ctx, "blacklist:"+token).Result()
	// if isBlacklisted { return "", errors.New("token blacklisted") }

	resp, err := a.client.ValidateToken(ctx, &pb.ValidateTokenRequest{Token: token})
	if err != nil {
		switch status.Code(err) {
		case codes.Unauthenticated:
			return "", ErrTokenExpired
		case codes.PermissionDenied:
			return "", ErrTokenInvalid
		default:
			return "", err
		}
	}

	return resp.GetUserId(), nil
}
