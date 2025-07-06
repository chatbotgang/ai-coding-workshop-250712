package common

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestRequestID(t *testing.T) {
	t.Parallel()
	rid := NewRequestID()

	ctx := SetRequestID(context.Background(), rid)
	assert.EqualValues(t, rid, GetRequestID(ctx))
}
