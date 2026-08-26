package config

import (
	"log"

	"github.com/ilyakaznacheev/cleanenv"
	"github.com/joho/godotenv"
)

func LoadEnvAndParse(envPath string, target any) {
	// Try to load the .env file at the given path (e.g. "internal/auth/.env")
	if err := godotenv.Load(envPath); err != nil {
		log.Printf("Info: No .env file found at %s, reading directly from system env\n", envPath)
	}

	// Read environment variables straight into the struct via tags
	if err := cleanenv.ReadEnv(target); err != nil {
		log.Fatalf("Critical: failed to parse environment variables: %v", err)
	}
}
