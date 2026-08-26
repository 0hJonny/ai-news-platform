package domain

import (
	"errors"
	"time"
)

var (
	ErrSessionNotFound = errors.New("chat session not found")
	ErrMessageNotFound = errors.New("message not found")
	ErrUnauthorized    = errors.New("access denied: user does not own this session")
)

// Custom types for the database ENUMs
type MessageRole string

const (
	RoleUser      MessageRole = "user"
	RoleAssistant MessageRole = "assistant"
	RoleSystem    MessageRole = "system"
)

type FeedbackRating string

const (
	RatingLike    FeedbackRating = "like"
	RatingDislike FeedbackRating = "dislike"
)

// Chat session entity (thread)
type Session struct {
	CreatedAt time.Time  `json:"created_at"`
    UpdatedAt time.Time  `json:"updated_at"`
    DeletedAt *time.Time `json:"deleted_at"`
    ID        string     `json:"id"`
    UserID    string     `json:"user_id"`
    Title     string     `json:"title"`
}

type MessageMeta struct {
	Temperature  *float64 `json:"temperature,omitempty"`
	Model        string   `json:"model,omitempty"`
	FinishReason string   `json:"finish_reason,omitempty"`
	PromptTokens int32    `json:"prompt_tokens,omitempty"`
	ComplTokens  int32    `json:"compl_tokens,omitempty"`
}

type Message struct {
	CreatedAt time.Time	  `json:"created_at"`
	ParentID  *string     `json:"parent_id,omitempty"`
	TraceID   *string     `json:"trace_id,omitempty"`
	ID        string      `json:"id"`
	SessionID string      `json:"session_id"`
	Role      MessageRole `json:"role"`
	Content   string      `json:"content"`
	MetaData  MessageMeta `json:"meta_data,omitempty"`
}

// Message feedback entity
type Feedback struct {
	CreatedAt time.Time
	Comment   *string
	ID        string
	MessageID string
	Rating    FeedbackRating
}
