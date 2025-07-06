package router

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog"

	"github.com/chatbotgang/workshop/internal/domain/common"
)

var sensitiveAPIs = map[string]bool{}

// filterSensitiveAPI only returns `email` field for sensitive APIs
func filterSensitiveAPI(path string, data []byte) []byte {
	type email struct {
		Email string `json:"email"`
	}

	_, ok := sensitiveAPIs[path]
	if ok {
		var e email
		err := json.Unmarshal(data, &e)
		if err != nil || e.Email == "" {
			return []byte{}
		}

		ret, err := json.Marshal(e)
		if err != nil {
			return []byte{}
		}

		return ret
	}

	return data
}

type loggerParams struct {
	clientIP     string
	statusCode   int
	bodySize     int
	userAgent    string
	errorMessage string
	fullPath     string
}

func buildLoggerParam(c *gin.Context) loggerParams {
	params := loggerParams{
		clientIP:   c.ClientIP(),
		statusCode: c.Writer.Status(),
		bodySize:   c.Writer.Size(),
		userAgent:  c.Request.Header.Get("User-Agent"),
	}

	// collect error message
	if err := c.Errors.Last(); err != nil {
		params.errorMessage = err.Error()
	}

	// collect full path
	path := c.Request.URL.Path
	raw := c.Request.URL.RawQuery
	if raw != "" {
		path = path + "?" + raw
	}
	params.fullPath = path

	return params
}

// LoggerMiddleware is referenced from gin's logger implementation with additional capabilities:
// 1. use zerolog to do structure log
// 2. add requestID into context logger
func LoggerMiddleware(rootCtx context.Context) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Start timer
		start := time.Now()

		// Ignore health-check to avoid polluting API logs
		path := c.Request.URL.Path
		if path == "/api/v1/health" {
			c.Next()
			return
		}

		// Add RequestID into the logger of the request context
		requestID := common.GetRequestID(c.Request.Context())
		zlog := zerolog.Ctx(rootCtx).With().
			Str("requestID", requestID).
			Str("path", c.FullPath()).
			Str("method", c.Request.Method).
			Logger()
		c.Request = c.Request.WithContext(zlog.WithContext(context.WithoutCancel(c.Request.Context())))

		// Use TeeReader to duplicate the request body to an internal buffer, so
		// that we could use it for logging
		var buf bytes.Buffer
		tee := io.TeeReader(c.Request.Body, &buf)
		c.Request.Body = io.NopCloser(tee)

		// Process request
		c.Next()

		// Build all information that we want to log
		params := buildLoggerParam(c)

		// Build logger with proper severity
		var l *zerolog.Event
		if params.statusCode >= 300 || len(params.errorMessage) != 0 {
			l = zerolog.Ctx(c.Request.Context()).Error()
		} else {
			l = zerolog.Ctx(c.Request.Context()).Info()
		}

		l = l.Time("callTime", start).
			Int("status", params.statusCode).
			Dur("latency", time.Since(start)).
			Str("clientIP", params.clientIP).
			Str("fullPath", params.fullPath).
			Str("component", "router").
			Str("userAgent", params.userAgent)

		if params.errorMessage != "" {
			l = l.Err(errors.New(params.errorMessage))
		}
		if buf.Len() > 0 {
			data := buf.Bytes()

			// Try to filter request body if it's a sensitive API
			data = filterSensitiveAPI(params.fullPath, data)

			var jsonBuf bytes.Buffer
			if err := json.Compact(&jsonBuf, data); err == nil {
				l = l.RawJSON("request", jsonBuf.Bytes())
			}
		}

		l.Send()
	}
}
