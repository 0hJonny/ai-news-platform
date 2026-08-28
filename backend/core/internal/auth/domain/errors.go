package domain

import "errors"

var (
	ErrInvalidEmail       = errors.New("invalid email format")
	ErrUserAlreadyExists  = errors.New("user already exists")
	ErrInvalidCredentials = errors.New("invalid email or password")
	ErrNotFound           = errors.New("user not found")
	ErrInvalidCreds       = errors.New("invalid credentials")
	// ErrInvalidToken means the token is malformed, has a bad signature, or
	// otherwise was never something this server issued (e.g. hand-edited).
	ErrInvalidToken = errors.New("invalid token")
	// ErrExpiredToken means the token is well-formed and was validly issued,
	// but its exp claim has passed. Kept distinct from ErrInvalidToken so
	// callers can tell "please log in again" apart from "this token was tampered with".
	ErrExpiredToken = errors.New("expired token")
)
