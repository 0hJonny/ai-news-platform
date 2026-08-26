package upstream

import (
	"context"

	"github.com/0hJonny/langfuse-agents/pkg/authclient/pb"
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
		return "", err
	}

	return resp.GetUserId(), nil
}
