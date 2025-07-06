package router

import (
	"github.com/gin-gonic/gin"

	"github.com/chatbotgang/workshop/internal/app"
)

// @title workshop API Document
// @version 1.0

func RegisterHandlers(router *gin.Engine, app *app.Application) {
	registerAPIHandlers(router, app)
}

func registerAPIHandlers(router *gin.Engine, app *app.Application) {
	// Build middlewares
	// SimpleToken := NewAuthMiddlewareSimple(app)

	// We mount all handlers under /api path
	r := router.Group("/api")
	v1 := r.Group("/v1")

	// Add health-check
	v1.GET("/health", handlerHealthCheck())

}
