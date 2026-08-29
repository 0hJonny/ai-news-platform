package service

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"strconv"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"

	"github.com/0hJonny/langfuse-agents/internal/auth/domain"
	"github.com/0hJonny/langfuse-agents/pkg/postgres"
)

var _ AuthService = (*AuthServiceImpl)(nil)

type AuthServiceImpl struct {
	txManager postgres.TxManager
	repo      domain.UserRepository
	secret    []byte
}

func NewAuthService(txManager postgres.TxManager, repo domain.UserRepository, secret string) *AuthServiceImpl {
	return &AuthServiceImpl{
		txManager: txManager,
		repo:      repo,
		secret:    []byte(secret),
	}
}

// Signature changed: name, login, and anonUserID were added
func (s *AuthServiceImpl) Register(ctx context.Context, email, password, name, login, anonUserID string) (Token, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return Token{}, fmt.Errorf("failed to hash password: %w", err)
	}
	hashStr := string(hash)

	var namePtr *string
	if trimmed := strings.TrimSpace(name); trimmed != "" {
		namePtr = &trimmed
	}

	tx, txCtx, err := s.txManager.Begin(ctx)
	if err != nil {
		return Token{}, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer func() {
		_ = tx.Rollback(txCtx)
	}()

	var user domain.User

	if anonUserID != "" {
		// Scenario 1: upgrade an existing anonymous user
		domainUser, err := domain.NewUser(domain.UserParams{
			ID:           anonUserID,
			Email:        &email,
			PasswordHash: &hashStr,
			Name:         namePtr,
			Login:        &login,
			Role:         domain.UserRoleUser,
		})
		if err != nil {
			return Token{}, err
		}

		user, err = s.repo.UpdateUser(txCtx, &domainUser)
		if err != nil {
			return Token{}, err
		}
	} else {
		// Scenario 2: fresh registration from scratch
		domainUser, err := domain.NewUser(domain.UserParams{
			Email:        &email,
			PasswordHash: &hashStr,
			Name:         namePtr,
			Login:        &login,
			Role:         domain.UserRoleUser,
		})
		if err != nil {
			return Token{}, err
		}

		user, err = s.repo.CreateUser(txCtx, &domainUser)
		if err != nil {
			return Token{}, err
		}
	}

	if err := tx.Commit(txCtx); err != nil {
		return Token{}, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return s.generateToken(user.ID, user.Role)
}

// New method for generating an anonymous profile
func (s *AuthServiceImpl) CreateAnonymous(ctx context.Context) (Token, error) {
	tx, txCtx, err := s.txManager.Begin(ctx)
	if err != nil {
		return Token{}, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer func() {
		_ = tx.Rollback(txCtx)
	}()

	// The domain will set the UserRoleAnonymous role and zero out the fields itself
	domainUser, err := domain.NewUser(domain.UserParams{})
	if err != nil {
		return Token{}, err
	}

	user, err := s.repo.CreateUser(txCtx, &domainUser)
	if err != nil {
		return Token{}, fmt.Errorf("failed to create anonymous user: %w", err)
	}

	if err := tx.Commit(txCtx); err != nil {
		return Token{}, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return s.generateToken(user.ID, user.Role)
}

// Login accepts either an email or a login/username as identifier and
// looks the user up by whichever format it matches.
func (s *AuthServiceImpl) Login(ctx context.Context, identifier, password string) (Token, error) {
	normalized := strings.ToLower(strings.TrimSpace(identifier))

	var user domain.User
	var err error
	if domain.ValidEmailFormat(normalized) {
		user, err = s.repo.GetUserByEmail(ctx, normalized)
	} else {
		user, err = s.repo.GetUserByLogin(ctx, normalized)
	}
	if err != nil {
		return Token{}, domain.ErrInvalidCreds
	}

	// Security: anonymous users without a password won't pass
	if user.PasswordHash == nil {
		return Token{}, domain.ErrInvalidCreds
	}

	if err := bcrypt.CompareHashAndPassword([]byte(*user.PasswordHash), []byte(password)); err != nil {
		return Token{}, domain.ErrInvalidCreds
	}

	return s.generateToken(user.ID, user.Role)
}

func (s *AuthServiceImpl) GetProfile(ctx context.Context, userID string) (domain.User, error) {
	return s.repo.GetUserByID(ctx, userID)
}

// CheckLoginAvailable is a plain read: it never writes, so calling it on
// every debounced keystroke while the user edits the login field doesn't
// put write load on the table. It is only a UX hint — the UNIQUE
// constraint (enforced in Register via uniqueViolationToDomainErr) is what
// actually guarantees no collision, since a race is still possible between
// this check and the real INSERT/UPDATE.
func (s *AuthServiceImpl) CheckLoginAvailable(ctx context.Context, login string) (bool, error) {
	normalized := strings.ToLower(strings.TrimSpace(login))
	if !domain.ValidLoginFormat(normalized) {
		return false, domain.ErrInvalidLogin
	}
	return s.repo.IsLoginAvailable(ctx, normalized)
}

// UsernameCheckResult is CheckUsername's result: whether the requested
// handle is free, and — only when it isn't — a handful of alternatives
// that were each individually verified against the database.
type UsernameCheckResult struct {
	Suggestions []string
	Available   bool
}

const suggestionCount = 3

// maxSuggestionAttempts bounds the retry loop below. Each attempt tries a
// fresh randomly-suffixed candidate, so with suggestionCount=3 this gives
// plenty of headroom even if several candidates in a row happen to already
// be taken; it exists purely so a pathological run can't loop forever.
const maxSuggestionAttempts = 25

// wordSuggestionSuffixes mirrors the frontend's numeric-suffix suggestions
// (see loginValidator.ts's suggestLoginAlternatives) with a few word-based
// alternatives thrown in, closer to what GitHub/Google-style signup
// suggestion engines offer alongside plain numbers.
var wordSuggestionSuffixes = []string{"_ai", "_dev", "_pro", "_hq"}

// randomSuggestionSuffix picks a suffix for the given attempt index —
// two-digit numbers first (matches the frontend's own heuristic), then
// three-digit, then a couple of word suffixes, then wider random numbers
// for any attempts beyond that. math/rand, not crypto/rand, on purpose:
// this only picks cosmetic username suggestions, nothing security-sensitive
// (not a token, not a credential) — predictability here has no impact.
func randomSuggestionSuffix(attempt int) string {
	switch {
	case attempt < 2:
		return strconv.Itoa(10 + rand.Intn(90)) //nolint:gosec // G404: cosmetic suggestion, not security-sensitive
	case attempt < 4:
		return strconv.Itoa(100 + rand.Intn(900)) //nolint:gosec // G404: cosmetic suggestion, not security-sensitive
	case attempt < 4+len(wordSuggestionSuffixes):
		return wordSuggestionSuffixes[attempt-4]
	default:
		return strconv.Itoa(rand.Intn(10000)) //nolint:gosec // G404: cosmetic suggestion, not security-sensitive
	}
}

// CheckUsername is CheckLoginAvailable's richer sibling for the
// registration form's "Username Suggestion Engine": a free handle just
// reports available, but a taken one comes back with real, DB-verified
// alternatives instead of leaving the frontend to guess-and-check on its
// own. Like CheckLoginAvailable, this is only a UX hint — the UNIQUE
// constraint enforced in Register is what actually guarantees no
// collision, since a race is still possible between this check and the
// real INSERT.
func (s *AuthServiceImpl) CheckUsername(ctx context.Context, username string) (UsernameCheckResult, error) {
	normalized := strings.ToLower(strings.TrimSpace(username))
	if !domain.ValidLoginFormat(normalized) {
		return UsernameCheckResult{}, domain.ErrInvalidLogin
	}

	available, err := s.repo.IsLoginAvailable(ctx, normalized)
	if err != nil {
		return UsernameCheckResult{}, err
	}
	if available {
		return UsernameCheckResult{Available: true}, nil
	}

	suggestions, err := s.generateAvailableSuggestions(ctx, normalized)
	if err != nil {
		return UsernameCheckResult{}, err
	}
	return UsernameCheckResult{Available: false, Suggestions: suggestions}, nil
}

func (s *AuthServiceImpl) generateAvailableSuggestions(ctx context.Context, base string) ([]string, error) {
	// Leave room for up to a 4-char suffix (the longest word suffix, e.g.
	// "_dev") within the shared login-rules max length.
	trimmedBase := base
	if maxLen := domain.LoginMaxLength(); len(trimmedBase) > maxLen-4 {
		trimmedBase = trimmedBase[:maxLen-4]
	}

	suggestions := make([]string, 0, suggestionCount)
	seen := map[string]bool{base: true}

	for attempt := 0; attempt < maxSuggestionAttempts && len(suggestions) < suggestionCount; attempt++ {
		candidate := trimmedBase + randomSuggestionSuffix(attempt)
		if seen[candidate] || !domain.ValidLoginFormat(candidate) {
			continue
		}
		seen[candidate] = true

		available, err := s.repo.IsLoginAvailable(ctx, candidate)
		if err != nil {
			return nil, err
		}
		if available {
			suggestions = append(suggestions, candidate)
		}
	}

	return suggestions, nil
}

func (s *AuthServiceImpl) ValidateToken(ctx context.Context, tokenString string) (string, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return s.secret, nil
	})

	if err != nil {
		// A well-formed, correctly-signed token that simply passed its exp
		// claim is a normal "please log in again" case. Anything else
		// (bad signature, malformed structure, wrong alg, hand-edited
		// payload) means the token was never legitimately issued.
		if errors.Is(err, jwt.ErrTokenExpired) {
			return "", domain.ErrExpiredToken
		}
		return "", domain.ErrInvalidToken
	}

	if token == nil || !token.Valid {
		return "", domain.ErrInvalidToken
	}

	userID, err := token.Claims.GetSubject()
	if err != nil || userID == "" {
		return "", domain.ErrInvalidToken
	}

	return userID, nil
}

// Takes the strict domain.UserRole type instead of a string
func (s *AuthServiceImpl) generateToken(userID string, role domain.UserRole) (Token, error) {
	now := time.Now().UTC()
	expirationTime := now.Add(24 * time.Hour)

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub":  userID,
		"role": string(role),
		"exp":  expirationTime.Unix(),
		"iat":  now.Unix(),
	})

	tokenString, err := token.SignedString(s.secret)
	if err != nil {
		return Token{}, err
	}

	return Token{
		Value:     tokenString,
		ExpiresAt: expirationTime.Unix(),
	}, nil
}
