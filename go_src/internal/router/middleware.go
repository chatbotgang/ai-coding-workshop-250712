package router

import (
	"context"

	"github.com/gin-gonic/gin"
)

// SetGeneralMiddlewares add general-purpose middlewares
func SetGeneralMiddlewares(ctx context.Context, ginRouter *gin.Engine) {
	ginRouter.Use(gin.Recovery())
	ginRouter.Use(RequestIDMiddleware())
	ginRouter.Use(RemoveZWSPMiddleware())

	// LoggerMiddleware needs to be after TraceMiddleware, so that it could
	// get traceID from the request context
	ginRouter.Use(LoggerMiddleware(ctx))
}
