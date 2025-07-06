package router

import (
	"github.com/gin-gonic/gin"

	"github.com/chatbotgang/workshop/internal/domain/common"
)

const headerXRequestID = "X-Request-ID"

// RequestIDMiddleware initializes the RequestID middleware.
func RequestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get id from request
		rid := c.GetHeader(headerXRequestID)
		if rid == "" {
			rid = common.NewRequestID()
			// Set the id to ensure that the requestid is in the request header
			c.Request.Header.Add(headerXRequestID, rid)
		}

		// Set the id to ensure that the requestid is in the request context
		ctx := common.SetRequestID(c.Request.Context(), rid)
		c.Request = c.Request.WithContext(ctx)

		// Set the id to ensure that the requestid is in the response
		c.Header(headerXRequestID, rid)
		c.Next()
	}
}
