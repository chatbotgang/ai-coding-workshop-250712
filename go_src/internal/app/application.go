package app

import (
	"context"
	"log"
	"sync"
)

type Application struct {
	Param ApplicationParam
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

	// Create servers

	// Create event brokers

	// Create application
	app := &Application{
		Param: param,
	}

	return app, nil
}
