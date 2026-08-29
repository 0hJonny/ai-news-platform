package domain

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)

// ValidEmailFormat reports whether s matches emailRegex once
// lowercased/trimmed. Exported so the service layer's login flow can tell
// whether the identifier a user typed is an email or a login/username
// without duplicating the pattern.
func ValidEmailFormat(s string) bool {
	return emailRegex.MatchString(strings.ToLower(strings.TrimSpace(s)))
}

// loginRulesPath resolves ai_news_platform/shared/auth/login-rules.json —
// the single canonical copy of the login/username format contract. The
// frontend reads this exact same file (frontend/src/vite.config.ts's
// "@shared" alias, used from frontend/src/src/utils/loginValidator.ts); the
// "users_login_format" CHECK constraint in
// sql/auth/migrations/00003_add_user_login.sql mirrors the same pattern and
// is what actually guarantees the database never ends up with a malformed
// value — this is the fail-fast/UX layer on top of that guarantee.
//
// It can't be go:embed'd: embed patterns can't cross the Go module boundary
// (backend/core is its own module, and shared/ sits outside it), so this is
// a plain file read at package init instead — still zero network calls,
// just resolved once at process startup rather than compiled into the
// binary. The default assumes the process's working directory is the
// backend/core module root, which is how both `go run ./cmd/auth` (run
// from backend/core) and the auth service's Docker Compose entry invoke it.
// LOGIN_RULES_PATH overrides that for any other layout.
func loginRulesPath() string {
	if p := os.Getenv("LOGIN_RULES_PATH"); p != "" {
		return p
	}
	return filepath.Join("..", "..", "shared", "auth", "login-rules.json")
}

type loginRulesSpec struct {
	Pattern     string `json:"pattern"`
	MinLength   int    `json:"minLength"`
	MaxLength   int    `json:"maxLength"`
	Description string `json:"description"`
}

var loginRules = func() loginRulesSpec {
	path := loginRulesPath()

	raw, err := os.ReadFile(path)
	if err != nil {
		panic(fmt.Sprintf(
			"domain: failed to read login rules at %q (set LOGIN_RULES_PATH if the process isn't started from the backend/core module root): %v",
			path, err,
		))
	}

	var spec loginRulesSpec
	if err := json.Unmarshal(raw, &spec); err != nil {
		panic(fmt.Sprintf("domain: invalid login rules JSON at %q: %v", path, err))
	}
	return spec
}()

var loginRegex = regexp.MustCompile(loginRules.Pattern)

// ValidLoginFormat reports whether login matches loginRegex once
// lowercased/trimmed. Exported so the service layer's availability-check
// endpoint can reject an obviously malformed query before ever touching the
// database.
func ValidLoginFormat(login string) bool {
	return loginRegex.MatchString(strings.ToLower(strings.TrimSpace(login)))
}

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
	Login        *string
	Role         UserRole
}

type User struct {
	CreatedAt    time.Time
	Email        *string
	PasswordHash *string
	Name         *string
	Login        *string
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

	// 1c. The login, if provided, must match loginRegex. Stored lowercase so
	// "Ivan" and "ivan" can't both be taken.
	var cleanLogin *string
	if params.Login != nil {
		loginStr := strings.ToLower(strings.TrimSpace(*params.Login))
		if loginStr != "" {
			if !loginRegex.MatchString(loginStr) {
				return User{}, ErrInvalidLogin
			}
			cleanLogin = &loginStr
		}
	}

	// 2. Default role if an empty string was passed
	role := params.Role
	if role == "" {
		role = UserRoleAnonymous
	}

	// 3. Business validation: a regular user MUST have an email, a password,
	// and a unique login.
	if role == UserRoleUser || role == UserRoleAdmin {
		if cleanEmail == nil || params.PasswordHash == nil || *params.PasswordHash == "" {
			return User{}, ErrInvalidCreds
		}
		if cleanLogin == nil {
			return User{}, ErrInvalidLogin
		}
	}

	return User{
		ID:           params.ID,
		Email:        cleanEmail,
		PasswordHash: params.PasswordHash,
		Name:         cleanName,
		Login:        cleanLogin,
		Role:         role,
		CreatedAt:    time.Now().UTC(),
	}, nil
}
