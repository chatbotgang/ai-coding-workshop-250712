package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/alecthomas/kingpin/v2"
	"github.com/rs/zerolog"

	"github.com/chatbotgang/workshop/internal/app"
)

var (
	AppName    = "workshop"
	AppVersion = "unknown_version"
	AppBuild   = "unknown_build"
)

const (
	defaultEnv      = "staging"
	defaultLogLevel = "info"
	defaultPort     = "8080"
)

type AppConfig struct {
	// General configuration
	Env      *string
	LogLevel *string

	// HTTP configuration
	Port *int
}

func initAppConfig() AppConfig {
	// Setup basic application information
	app := kingpin.New(AppName, "The HTTP server").
		Version(fmt.Sprintf("version: %s, build: %s", AppVersion, AppBuild))

	var config AppConfig

	config.Env = app.
		Flag("env", "The running environment").
		Envar("WORKSHOP_ENV").Default(defaultEnv).Enum("local", "staging", "production")

	config.LogLevel = app.
		Flag("log_level", "Log filtering level").
		Envar("WORKSHOP_LOG_LEVEL").Default(defaultLogLevel).Enum("error", "warn", "info", "debug", "disabled")

	config.Port = app.
		Flag("port", "The HTTP server port").
		Envar("WORKSHOP_PORT").Default(defaultPort).Int()

	kingpin.MustParse(app.Parse(os.Args[1:]))

	return config
}

func initRootLogger(levelStr, env string) zerolog.Logger {
	// Set global log level
	level, err := zerolog.ParseLevel(levelStr)
	if err != nil {
		level = zerolog.InfoLevel
	}
	zerolog.SetGlobalLevel(level)

	// Set logger time format
	const rfc3339Micro = "2006-01-02T15:04:05.000000Z07:00"
	zerolog.TimeFieldFormat = rfc3339Micro
	zerolog.DurationFieldUnit = time.Second

	rootLogger := zerolog.New(os.Stdout).With().
		Timestamp().
		Str("service", AppName).
		Str("env", env).
		Logger()

	return rootLogger
}

func main() {

	// Setup app configuration
	cfg := initAppConfig()

	// Create root logger
	rootLogger := initRootLogger(*cfg.LogLevel, *cfg.Env)

	// Create root context
	rootCtx, rootCtxCancelFunc := context.WithCancel(context.Background())
	rootCtx = rootLogger.WithContext(rootCtx)

	rootLogger.Info().
		Str("version", AppVersion).
		Str("build", AppBuild).
		Msgf("Launching %s", AppName)

	wg := sync.WaitGroup{}
	// Create application
	app := app.MustNewApplication(rootCtx, &wg, app.ApplicationParam{
		AppName: AppName,
		Env:     *cfg.Env,
	})

	// Run server
	wg.Add(1)
	runHTTPServer(rootCtx, &wg, *cfg.Port, app)

	// Listen to SIGTERM/SIGINT to close
	var gracefulStop = make(chan os.Signal, 1)
	signal.Notify(gracefulStop, syscall.SIGTERM, syscall.SIGINT)
	<-gracefulStop
	rootCtxCancelFunc()

	// Wait for all services to close with a specific timeout
	var waitUntilDone = make(chan struct{})
	go func() {
		wg.Wait()
		close(waitUntilDone)
	}()
	select {
	case <-waitUntilDone:
		rootLogger.Info().Msg("success to close all services")
	case <-time.After(10 * time.Second):
		rootLogger.Err(context.DeadlineExceeded).Msg("fail to close all services")
	}
}
