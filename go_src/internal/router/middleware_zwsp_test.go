package router

import (
	"bytes"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestRemoveZWSPMiddleware(t *testing.T) {
	t.Parallel()

	// Test cases
	testCases := []struct {
		Name   string
		Test   string
		Expect string
	}{
		{
			Name:   "has-zwsp",
			Test:   "HERE>\u200B\u200C\u200D\uFEFF<HERE",
			Expect: "HERE><HERE",
		},
		{
			Name:   "has-utf8-nul",
			Test:   "HERE>\u0000<HERE",
			Expect: "HERE><HERE",
		}, {
			Name:   "has-utf8-nul-string",
			Test:   "HERE>\\u0000<HERE",
			Expect: "HERE><HERE",
		},
		{
			Name:   "no-zwsp",
			Test:   "HERE><HERE",
			Expect: "HERE><HERE",
		},
		{
			Name:   "empty",
			Test:   "",
			Expect: "",
		},
		{
			Name:   "emoji-with-zero-width-joiner",
			Test:   "🐈‍⬛",
			Expect: "🐈‍⬛",
		},
	}

	gin.SetMode(gin.ReleaseMode)
	for i := range testCases {
		c := testCases[i]
		t.Run(c.Name, func(t *testing.T) {
			r := gin.New()
			r.Use(RemoveZWSPMiddleware())
			r.POST("/echo", func(c *gin.Context) {
				d, _ := io.ReadAll(c.Request.Body)
				c.String(200, string(d))
			})

			res := httptest.NewRecorder()
			req, _ := http.NewRequest("POST", "/echo", bytes.NewBufferString(c.Test))

			r.ServeHTTP(res, req)

			assert.EqualValues(t, c.Expect, res.Body.String())
		})
	}
}
