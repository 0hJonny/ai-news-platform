package domain

import "context"

type UserRepository interface {
	CreateUser(ctx context.Context, user *User) (User, error)
	GetUserByEmail(ctx context.Context, email string) (User, error)
	GetUserByLogin(ctx context.Context, login string) (User, error)
	GetUserByID(ctx context.Context, id string) (User, error)
	UpdateUser(ctx context.Context, user *User) (User, error)
	// IsLoginAvailable is a plain read (indexed EXISTS check) — never a
	// write — so the frontend can call it on every debounced keystroke
	// without putting write load on the table. The UNIQUE constraint on
	// auth.users.login is still what actually prevents a collision; this is
	// only a best-effort UX hint and can race with a concurrent registration.
	IsLoginAvailable(ctx context.Context, login string) (bool, error)
}
