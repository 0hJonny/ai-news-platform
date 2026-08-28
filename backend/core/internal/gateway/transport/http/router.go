package http

import (
	"context"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
)

type TokenValidator interface {
	ValidateToken(ctx context.Context, token string) (string, error)
}

type Router struct {
	validator      TokenValidator
	authURL        *url.URL
	agentsURL      *url.URL
	chatsURL       *url.URL
	newsURL        *url.URL
	allowedOrigins []string
}

func NewRouter(v TokenValidator, authAddr, agentsAddr, chatsAddr, newsAddr, allowedOriginsStr string) (*Router, error) {
	parsedAuth, err := url.Parse(authAddr)
	if err != nil {
		return nil, err
	}
	parsedAgents, err := url.Parse(agentsAddr)
	if err != nil {
		return nil, err
	}
	parsedChats, err := url.Parse(chatsAddr)
	if err != nil {
		return nil, err
	}
	parsedNews, err := url.Parse(newsAddr)
	if err != nil {
		return nil, err
	}

	// Split the comma-separated config string into a clean slice of domains
	origins := strings.Split(allowedOriginsStr, ",")
	for i := range origins {
		origins[i] = strings.TrimSpace(origins[i])
	}

	return &Router{
		validator:      v,
		authURL:        parsedAuth,
		agentsURL:      parsedAgents,
		chatsURL:       parsedChats,
		newsURL:        parsedNews,
		allowedOrigins: origins,
	}, nil
}

func (rt *Router) RegisterRoutes() *chi.Mux {
	r := chi.NewRouter()

	// 1. CORS MIDDLEWARE SETUP (must come FIRST in the chain!)
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   rt.allowedOrigins,
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token", "X-Request-Id"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	r.Use(middleware.RequestID)
	r.Use(middleware.Recoverer)

	authProxy := httputil.NewSingleHostReverseProxy(rt.authURL)

	createSecureProxy := func(targetURL *url.URL) *httputil.ReverseProxy {
		return &httputil.ReverseProxy{
			FlushInterval: 100 * time.Millisecond, // Streaming for SSE
			Rewrite: func(pr *httputil.ProxyRequest) {
				pr.SetURL(targetURL)
				userID := GetUserID(pr.In.Context())
				if userID != "" {
					pr.Out.Header.Set("X-User-Id", userID)
				}
			},
		}
	}

	agentsProxy := createSecureProxy(rt.agentsURL)
	chatsProxy := createSecureProxy(rt.chatsURL)
	newsProxy := httputil.NewSingleHostReverseProxy(rt.newsURL)

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("OK"))
	})

	// Public routes
	r.Route("/api/v1/auth", func(r chi.Router) {
		r.Post("/register", authProxy.ServeHTTP)
		r.Post("/login", authProxy.ServeHTTP)
		r.Post("/anonimous", authProxy.ServeHTTP)
		r.Get("/login-available", authProxy.ServeHTTP)
		// Was missing entirely — GET /auth/user (fetchProfile on the
		// frontend) never had a route here, so profile fetches always 404'd
		// through the gateway. Unrelated to the login field, fixed in
		// passing since it sits right next to the route just added above.
		r.Get("/user", authProxy.ServeHTTP)
	})

	// Articles (news service, backend/news): public reads, no JWT gate at the gateway —
	// news itself exposes these routes through its own public /api/v1/g group.
	r.Route("/api/v1/g", func(r chi.Router) {
		r.HandleFunc("/*", newsProxy.ServeHTTP)
	})

	// Protected routes
	r.Group(func(r chi.Router) {
		r.Use(AuthMiddleware(rt.validator))

		r.Route("/api/v1/agents", func(r chi.Router) {
			r.HandleFunc("/*", agentsProxy.ServeHTTP)
		})

		r.Route("/api/v1/chats", func(r chi.Router) {
			r.Post("/sessions", chatsProxy.ServeHTTP)              // Create a new thread
			r.Get("/sessions", chatsProxy.ServeHTTP)               // Get the chat list for the sidebar
			r.Put("/sessions/{id}/title", chatsProxy.ServeHTTP)    // Rename a chat
			r.Delete("/sessions/{id}", chatsProxy.ServeHTTP)       // Delete a chat
			r.Get("/sessions/{id}/messages", chatsProxy.ServeHTTP) // Fetch the history for
		})
	})

	return r
}
