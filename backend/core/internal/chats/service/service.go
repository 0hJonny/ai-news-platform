package service

import (
	"context"

	"github.com/0hJonny/langfuse-agents/internal/chats/domain"
)

// Parameter-passing structs (DTOs) so method signatures don't balloon
type SendMessageDTO struct {
	ParentID  *string            `json:"parent_id"`
	TraceID   *string            `json:"trace_id"`
	SessionID string             `json:"session_id"`
	Role      domain.MessageRole `json:"role"`
	Content   string             `json:"content"`
	MetaData  domain.MessageMeta `json:"meta_data"`
}

type SetFeedbackDTO struct {
	Comment   *string               `json:"comment"`
	MessageID string                `json:"message_id"`
	Rating    domain.FeedbackRating `json:"rating"`
}

type ChatService interface {
	// Session (chat) management
	CreateNewChat(ctx context.Context, userID string, title string) (domain.Session, error)
	GetUserChats(ctx context.Context, userID string) ([]domain.Session, error)
	RenameChat(ctx context.Context, userID string, sessionID string, newTitle string) error
	DeleteChat(ctx context.Context, userID string, sessionID string) error

	// Message management (dialog history)
	// The method takes userID for permission validation (checks whether the chat belongs to this user)
	GetChatHistory(ctx context.Context, userID string, sessionID string) ([]domain.Message, error)

	// The main method the Python service will call for atomic message saving
	SaveMessage(ctx context.Context, userID string, dto *SendMessageDTO) (domain.Message, error)

	// Rating AI responses
	SubmitFeedback(ctx context.Context, userID string, dto *SetFeedbackDTO) (domain.Feedback, error)
}
