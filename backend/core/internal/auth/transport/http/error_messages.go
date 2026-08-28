package http

// errorMessages is the single source of truth for the text that accompanies
// each error code in an API response body. One code, one message — call
// sites pass only the code (see respondWithError in handlers.go) so the
// text can't drift between call sites the way it did when every handler
// wrote its own copy inline.
//
// This is NOT what end users see: the frontend keys its own localized copy
// off the code (frontend/src/src/locales/{ru-RU,en-US}.json,
// errors.api.<CODE>) and never renders this field. It exists for API
// consumers that log or display the raw response. Situational detail for
// developers belongs in the handler's h.log.Error call, not here.
var errorMessages = map[string]string{
	"AUTH_INVALID_REQUEST":     "invalid request",
	"AUTH_INVALID_EMAIL":       "invalid email format",
	"AUTH_INVALID_LOGIN":       "invalid login format",
	"AUTH_EMAIL_TAKEN":         "email already registered",
	"AUTH_LOGIN_TAKEN":         "login already taken",
	"AUTH_INVALID_CREDENTIALS": "invalid email or password",
	"AUTH_ACCOUNT_NOT_FOUND":   "user not found",
	"TOKEN_MISSING":            "missing or invalid token",
	"INTERNAL_ERROR":           "internal server error",
}

func messageForCode(code string) string {
	if msg, ok := errorMessages[code]; ok {
		return msg
	}
	return "an error occurred"
}
