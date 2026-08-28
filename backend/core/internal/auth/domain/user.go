package domain

import (
	"regexp"
	"strings"
	"time"
)

var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)

type UserRole string

const (
	UserRoleAnonymous UserRole = "anonymous"
	UserRoleUser      UserRole = "user"
	UserRoleAdmin     UserRole = "admin"
)

type UserParams struct {
	ID           string
	Email        *string
	PasswordHash *string
	Name         *string
	Role         UserRole
}

type User struct {
	CreatedAt    time.Time
	Email        *string
	PasswordHash *string
	Name         *string
	ID           string
	Role         UserRole
}

func NewUser(params UserParams) (User, error) {
	var cleanEmail *string

	// 1. Validate the email, but only if one was provided
	if params.Email != nil {
		emailStr := strings.ToLower(strings.TrimSpace(*params.Email))

		if !emailRegex.MatchString(emailStr) {
			return User{}, ErrInvalidEmail
		}
		cleanEmail = &emailStr
	}

	// 1b. The display name is optional and has no format requirements —
	// just trim it, and treat a blank string as "not provided".
	var cleanName *string
	if params.Name != nil {
		nameStr := strings.TrimSpace(*params.Name)
		if nameStr != "" {
			cleanName = &nameStr
		}
	}

	// 2. Default role if an empty string was passed
	role := params.Role
	if role == "" {
		role = UserRoleAnonymous
	}

	// 3. Business validation: a regular user MUST have an email and a password
	if role == UserRoleUser || role == UserRoleAdmin {
		if cleanEmail == nil || params.PasswordHash == nil || *params.PasswordHash == "" {
			return User{}, ErrInvalidCreds
		}
	}

	return User{
		ID:           params.ID,
		Email:        cleanEmail,
		PasswordHash: params.PasswordHash,
		Name:         cleanName,
		Role:         role,
		CreatedAt:    time.Now().UTC(),
	}, nil
}
