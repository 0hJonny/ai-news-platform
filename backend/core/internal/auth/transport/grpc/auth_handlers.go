package grpc

import (
	"context"
	"errors"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"github.com/0hJonny/langfuse-agents/internal/auth/domain"
	"github.com/0hJonny/langfuse-agents/pkg/authclient/pb"
)

type TokenValidator interface {
	ValidateToken(ctx context.Context, tokenString string) (string, error)
}

var (
	errTokenExpired = status.Error(codes.Unauthenticated, "token expired")
	errTokenInvalid = status.Error(codes.PermissionDenied, "token invalid")
	errInternal     = status.Error(codes.Internal, "internal server error")
)

type GRPCHandler struct {
	pb.UnimplementedAuthServiceServer
	service TokenValidator
}

func NewGRPCHandler(service TokenValidator) *GRPCHandler {
	return &GRPCHandler{
		service: service,
	}
}

func (h *GRPCHandler) ValidateToken(ctx context.Context, req *pb.ValidateTokenRequest) (*pb.ValidateTokenResponse, error) {
	userID, err := h.service.ValidateToken(ctx, req.GetToken())
	if err != nil {
		if errors.Is(err, domain.ErrExpiredToken) {
			return nil, errTokenExpired
		}
		if errors.Is(err, domain.ErrInvalidToken) {
			// Distinct code from the expired case: this token was never
			// legitimately issued (bad signature, malformed, hand-edited).
			return nil, errTokenInvalid
		}

		return nil, errInternal
	}

	return &pb.ValidateTokenResponse{
		UserId: userID,
	}, nil
}
