package common

import (
	"context"

	"github.com/google/uuid"
)

type ctxKey struct{}

// New returns the new uuid
func NewRequestID() string {
	return uuid.New().String()
}

// Set sets the requestid in the context
func SetRequestID(ctx context.Context, requestID string) context.Context {
	return context.WithValue(ctx, ctxKey{}, requestID)
}

// Get returns the request id
func GetRequestID(ctx context.Context) string {
	if rid, ok := ctx.Value(ctxKey{}).(string); ok {
		return rid
	}
	return ""
}
