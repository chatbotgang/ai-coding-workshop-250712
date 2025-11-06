package app

import (
	"context"
	"log"
	"sync"

	"github.com/chatbotgang/workshop/internal/adapter/repository"
	"github.com/chatbotgang/workshop/internal/app/service"
)

type Application struct {
	Param ApplicationParam

	// Repository
	AutoReplyRepository *repository.AutoReplyMemoryRepository

	// Service
	AutoReplyService *service.AutoReplyService
}

type ApplicationParam struct {
	// General configuration
	AppName string
	Env     string
}

func MustNewApplication(ctx context.Context, wg *sync.WaitGroup, params ApplicationParam) *Application {
	app, err := NewApplication(ctx, wg, params)
	if err != nil {
		log.Panicf("fail to new application, err: %s", err.Error())
	}
	return app
}

func NewApplication(ctx context.Context, wg *sync.WaitGroup, param ApplicationParam) (*Application, error) {
	// Create repositories
	autoReplyRepo := repository.NewAutoReplyMemoryRepository()

	// Create services
	autoReplySvc := service.NewAutoReplyService(service.AutoReplyServiceParam{
		// 可注入 repository, logger, event 等
		AutoReplyRepository: autoReplyRepo,
	})

	// Create servers
	// TODO: ex: httpServer := server.NewHTTPServer(...)

	// Create event brokers
	// TODO: ex: eventBroker := eventbroker.New(...)

	// Create application
	app := &Application{
		Param:               param,
		AutoReplyRepository: autoReplyRepo,
		AutoReplyService:    autoReplySvc,
	}

	return app, nil
}
