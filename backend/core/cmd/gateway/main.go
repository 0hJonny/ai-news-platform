package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/0hJonny/langfuse-agents/internal/gateway/config"
	gatewayHttp "github.com/0hJonny/langfuse-agents/internal/gateway/transport/http"
	"github.com/0hJonny/langfuse-agents/internal/gateway/upstream"
	"github.com/0hJonny/langfuse-agents/pkg/authclient"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	logger.Info("Starting API Gateway initialization...")

	cfg := config.Load()

	// 1. Initialize the base gRPC client
	rawClient, err := authclient.NewAuthClient(cfg.AuthGRPCAddr)
	if err != nil {
		logger.Error("Failed to connect to Auth gRPC service", slog.String("addr", cfg.AuthGRPCAddr), slog.String("error", err.Error()))
		os.Exit(1)
	}
	logger.Info("Connected to Auth gRPC Service successfully")

	// 2. Wrap the client in an adapter (ready for Redis to be added later)
	authAdapter := upstream.NewAuthServiceClientAdapter(rawClient)

	// 3. Build the router, passing the adapter as a TokenValidator
	router, err := gatewayHttp.NewRouter(authAdapter, cfg.AuthHTTPAddr, cfg.AgentsHTTPAddr, cfg.ChatsHTTPAddr, cfg.NewsHTTPAddr, cfg.AllowedOrigins)
	if err != nil {
		logger.Error("Failed to initialize router", slog.String("error", err.Error()))
		os.Exit(1)
	}
	chiRouter := router.RegisterRoutes()

	srv := &http.Server{
		Addr:              ":" + cfg.ServerPort,
		Handler:           chiRouter,
		ReadHeaderTimeout: 3 * time.Second,
	}

	// 4. Start the gateway's HTTP server
	go func() {
		logger.Info("API Gateway is listening", slog.String("port", cfg.ServerPort))
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("API Gateway crashed", slog.String("error", err.Error()))
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	<-quit
	logger.Info("Received shutdown signal, shutting down Gateway gracefully...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Error("Gateway forced to shutdown", slog.String("error", err.Error()))
	}

	logger.Info("API Gateway stopped successfully")

}
