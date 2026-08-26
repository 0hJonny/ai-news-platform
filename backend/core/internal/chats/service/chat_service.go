package service

import (
	"context"
	"fmt"

	"github.com/0hJonny/langfuse-agents/internal/chats/domain"
	"github.com/0hJonny/langfuse-agents/pkg/postgres"
)

var _ ChatService = (*ChatServiceImpl)(nil)

type ChatServiceImpl struct {
	txManager postgres.TxManager
	repo      domain.ChatRepository
}

func NewChatService(txManager postgres.TxManager, repo domain.ChatRepository) *ChatServiceImpl {
	return &ChatServiceImpl{
		txManager: txManager,
		repo:      repo,
	}
}

// 1. Create a new chat (a transaction usually isn't needed here, but it'll come in handy if you later want to write the first system message right away)
func (s *ChatServiceImpl) CreateNewChat(ctx context.Context, userID, title string) (domain.Session, error) {
	if title == "" {
		title = "New diolog"
	}
	return s.repo.CreateSession(ctx, userID, title)
}

// 2. Get the list of chats for a specific user
func (s *ChatServiceImpl) GetUserChats(ctx context.Context, userID string) ([]domain.Session, error) {
	return s.repo.GetActiveSessionsByUserID(ctx, userID)
}

// 3. Rename a chat
func (s *ChatServiceImpl) RenameChat(ctx context.Context, userID, sessionID, newTitle string) error {
	session, err := s.repo.GetSessionByID(ctx, sessionID)
	if err != nil {
		return err
	}
	if session.UserID != userID {
		return domain.ErrUnauthorized
	}

	if newTitle == "" {
		newTitle = "Без названия"
	}

	return s.repo.UpdateSessionTitle(ctx, sessionID, newTitle)
}

// 4. Soft-delete a chat
func (s *ChatServiceImpl) DeleteChat(ctx context.Context, userID, sessionID string) error {
	session, err := s.repo.GetSessionByID(ctx, sessionID)
	if err != nil {
		return err
	}
	if session.UserID != userID {
		return domain.ErrUnauthorized
	}

	return s.repo.SoftDeleteSession(ctx, sessionID)
}

// 5. Fetch the message history
func (s *ChatServiceImpl) GetChatHistory(ctx context.Context, userID, sessionID string) ([]domain.Message, error) {
	session, err := s.repo.GetSessionByID(ctx, sessionID)
	if err != nil {
		return nil, err
	}
	if session.UserID != userID {
		return nil, domain.ErrUnauthorized
	}

	return s.repo.GetMessagesBySessionID(ctx, sessionID)
}

// 6. ATOMIC message save with a thread timestamp update
func (s *ChatServiceImpl) SaveMessage(ctx context.Context, userID string, dto *SendMessageDTO) (domain.Message, error) {
	// Begin the transaction
	tx, txCtx, err := s.txManager.Begin(ctx)
	if err != nil {
		return domain.Message{}, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer func() { _ = tx.Rollback(txCtx) }()

	// Do all checks and reads INSIDE the transaction (use txCtx)
	session, err := s.repo.GetSessionByID(txCtx, dto.SessionID)
	if err != nil {
		return domain.Message{}, err
	}
	if session.UserID != userID {
		return domain.Message{}, domain.ErrUnauthorized
	}

	msg, err := s.repo.AppendMessage(
		txCtx,
		dto.SessionID,
		dto.ParentID,
		dto.Role,
		dto.Content,
		dto.TraceID,
		dto.MetaData,
	)
	if err != nil {
		return domain.Message{}, err
	}

	// To do that we call the existing UpdateSessionTitle method, passing the current name (or write a separate UpdateSessionTimestamp method)
	if err := s.repo.UpdateSessionTitle(txCtx, dto.SessionID, session.Title); err != nil {
		return domain.Message{}, fmt.Errorf("failed to update session timestamp: %w", err)
	}

	// Commit the transaction
	if err := tx.Commit(txCtx); err != nil {
		return domain.Message{}, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return msg, nil
}

// 7. Save a like/dislike
func (s *ChatServiceImpl) SubmitFeedback(ctx context.Context, userID string, dto *SetFeedbackDTO) (domain.Feedback, error) {
	tx, txCtx, err := s.txManager.Begin(ctx)
	if err != nil {
		return domain.Feedback{}, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer func() { _ = tx.Rollback(txCtx) }()

	message, err := s.repo.GetMessageByID(txCtx, dto.MessageID)
	if err != nil {
		return domain.Feedback{}, err
	}

	session, err := s.repo.GetSessionByID(txCtx, message.SessionID)
	if err != nil {
		return domain.Feedback{}, err
	}
	if session.UserID != userID {
		return domain.Feedback{}, domain.ErrUnauthorized
	}

	feedback, err := s.repo.SetFeedback(txCtx, dto.MessageID, dto.Rating, dto.Comment)
	if err != nil {
		return domain.Feedback{}, err
	}

	if err := tx.Commit(txCtx); err != nil {
		return domain.Feedback{}, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return feedback, nil
}
