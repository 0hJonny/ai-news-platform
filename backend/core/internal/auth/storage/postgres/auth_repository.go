package postgres

import (
	"context"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgtype"

	"github.com/0hJonny/langfuse-agents/internal/auth/domain"
	"github.com/0hJonny/langfuse-agents/pkg/postgres"
)

var _ domain.UserRepository = (*PostgresRepository)(nil)

type PostgresRepository struct {
	queries *Queries
}

func NewPostgresRepository(queries *Queries) *PostgresRepository {
	return &PostgresRepository{queries: queries}
}

func (r *PostgresRepository) getQueries(ctx context.Context) *Queries {
	if tx := postgres.GetTxFromContext(ctx); tx != nil {
		return r.queries.WithTx(tx)
	}
	return r.queries
}

func (r *PostgresRepository) CreateUser(ctx context.Context, user *domain.User) (domain.User, error) {
	q := r.getQueries(ctx)

	// If no role is set in the domain, default to anonymous
	dbRole := domain.UserRoleAnonymous
	if user.Role != "" {
		dbRole = user.Role // Direct assignment, no casts needed!
	}

	dbUser, err := q.CreateUser(ctx, CreateUserParams{
		Email:        user.Email,
		PasswordHash: user.PasswordHash,
		Role:         dbRole, // Pass the plain domain.UserRole type
		Name:         user.Name,
	})
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == postgres.CodeUniqueViolation {
			return domain.User{}, domain.ErrUserAlreadyExists
		}
		return domain.User{}, err
	}

	return domain.User{
		ID:           dbUser.ID.String(),
		Email:        dbUser.Email,
		PasswordHash: dbUser.PasswordHash,
		Role:         dbUser.Role, // Maps one-to-one cleanly
		Name:         dbUser.Name,
		CreatedAt:    dbUser.CreatedAt.Time,
	}, nil
}

func (r *PostgresRepository) GetUserByEmail(ctx context.Context, email string) (domain.User, error) {
	q := r.getQueries(ctx)

	dbUser, err := q.GetUserByEmail(ctx, &email)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return domain.User{}, domain.ErrNotFound
		}
		return domain.User{}, err
	}

	return domain.User{
		ID:           dbUser.ID.String(),
		Email:        dbUser.Email,
		PasswordHash: dbUser.PasswordHash,
		Role:         dbUser.Role,
		Name:         dbUser.Name,
		CreatedAt:    dbUser.CreatedAt.Time,
	}, nil
}

func (r *PostgresRepository) GetUserByID(ctx context.Context, id string) (domain.User, error) {
	q := r.getQueries(ctx)

	var dbID pgtype.UUID
	if err := dbID.Scan(id); err != nil {
		return domain.User{}, fmt.Errorf("failed to parse user uuid: %w", err)
	}

	dbUser, err := q.GetUserById(ctx, dbID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return domain.User{}, domain.ErrNotFound
		}
		return domain.User{}, err
	}

	return domain.User{
		ID:           dbUser.ID.String(),
		Email:        dbUser.Email,
		PasswordHash: dbUser.PasswordHash,
		Role:         dbUser.Role,
		Name:         dbUser.Name,
		CreatedAt:    dbUser.CreatedAt.Time,
	}, nil
}

func (r *PostgresRepository) UpdateUser(ctx context.Context, user *domain.User) (domain.User, error) {
	q := r.getQueries(ctx)

	// Parse the string ID from the domain into the pgtype.UUID type sqlc expects
	var dbID pgtype.UUID
	if err := dbID.Scan(user.ID); err != nil {
		return domain.User{}, fmt.Errorf("failed to parse user uuid: %w", err)
	}

	// Call the sqlc-generated method to upgrade the user
	dbUser, err := q.UpdateUserToRegistered(ctx, UpdateUserToRegisteredParams{
		Email:        user.Email,
		PasswordHash: user.PasswordHash,
		Name:         user.Name,
		ID:           dbID,
	})
	if err != nil {
		var pgErr *pgconn.PgError
		// If the email the anonymous user entered is already taken by another account
		if errors.As(err, &pgErr) && pgErr.Code == postgres.CodeUniqueViolation {
			return domain.User{}, domain.ErrUserAlreadyExists
		}
		return domain.User{}, err
	}

	// Return the updated user back to the service
	return domain.User{
		ID:           dbUser.ID.String(),
		Email:        dbUser.Email,
		PasswordHash: dbUser.PasswordHash,
		Role:         dbUser.Role, // Will already be UserRoleUser here
		Name:         dbUser.Name,
		CreatedAt:    dbUser.CreatedAt.Time,
	}, nil
}
