package http

type AuthRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	Name     string `json:"name,omitempty"`
	Login    string `json:"login,omitempty"`
}

type LoginAvailabilityResponse struct {
	Available bool `json:"available"`
}

// CheckUsernameResponse is the Username Suggestion Engine's response:
// Suggestions is only populated (and only meaningful) when Available is
// false — omitted from the JSON body entirely when there's nothing to
// suggest.
type CheckUsernameResponse struct {
	Suggestions []string `json:"suggestions,omitempty"`
	Available   bool     `json:"available"`
}

type TokenResponse struct {
	Token     string `json:"token"`
	ExpiresAt int64  `json:"expires_at"`
}

type UserResponse struct {
	ID    string `json:"id"`
	Email string `json:"email"`
	Name  string `json:"name"`
	Login string `json:"login"`
	Role  string `json:"role"`
}

// ErrorResponse mirrors the gateway's authErrorBody shape ({"error":
// {"code","message"}}) so the frontend has one consistent contract for
// reading a machine-readable error code, whether the request was rejected
// by the gateway's AuthMiddleware or by this service directly.
type ErrorResponse struct {
	Error ErrorBody `json:"error"`
}

type ErrorBody struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}
