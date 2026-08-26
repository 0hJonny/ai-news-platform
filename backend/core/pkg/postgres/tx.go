package postgres

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

const (
	CodeUniqueViolation = "23505"
)

// Context key (unexported so nothing outside this package can overwrite it)
type txKey struct{}

// Tx describes the common transaction methods
type Tx interface {
	Commit(ctx context.Context) error
	Rollback(ctx context.Context) error
}

// TxManager is responsible for managing transactions
type TxManager interface {
	Begin(ctx context.Context) (Tx, context.Context, error)
}

// PostgresTxManager implements TxManager for pgx
type PostgresTxManager struct {
	pool *pgxpool.Pool
}

func NewPostgresTxManager(pool *pgxpool.Pool) *PostgresTxManager {
	return &PostgresTxManager{pool: pool}
}

func (m *PostgresTxManager) Begin(ctx context.Context) (Tx, context.Context, error) {
	pgxTx, err := m.pool.Begin(ctx)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to begin pgx tx: %w", err)
	}

	customTx := &pgxTxWrapper{tx: pgxTx}
	txCtx := context.WithValue(ctx, txKey{}, pgxTx)

	return customTx, txCtx, nil
}

// pgxTxWrapper adapts pgx.Tx to our common interface
type pgxTxWrapper struct {
	tx pgx.Tx
}

func (w *pgxTxWrapper) Commit(ctx context.Context) error   { return w.tx.Commit(ctx) }
func (w *pgxTxWrapper) Rollback(ctx context.Context) error { return w.tx.Rollback(ctx) }

// GetTxFromContext is a public helper. It pulls the active pgx.Tx out of the context.
// Returns nil if there is no transaction in the context.
func GetTxFromContext(ctx context.Context) pgx.Tx {
	if tx, ok := ctx.Value(txKey{}).(pgx.Tx); ok {
		return tx
	}
	return nil
}
