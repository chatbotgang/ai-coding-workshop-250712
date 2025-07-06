package router

import (
	"bytes"
	"io"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

// ref: https://github.com/trubitsyn/go-zero-width
const (
	// ZWSP represents zero-width space.
	ZWSP = string('\u200B')

	// ZWNBSP represents zero-width no-break space.
	ZWNBSP = string('\uFEFF')

	// ZWJ represents zero-width joiner.
	ZWJ = string('\u200D')

	// ZWNJ represents zero-width non-joiner.
	ZWNJ = string('\u200C')

	// UTF8NUL represents invalid byte sequence for encoding 0x00, which is not supported by some DBs.
	// ref: https://stackoverflow.com/questions/1347646/postgres-error-on-insert-error-invalid-byte-sequence-for-encoding-utf8-0x0
	UTF8NUL    = string('\u0000')
	UTF8NULStr = "\\u0000"

	empty = ""
)

var replacer = strings.NewReplacer(
	ZWSP, empty,
	ZWNBSP, empty,
	ZWJ, empty,
	ZWNJ, empty,
	UTF8NUL, empty,
	UTF8NULStr, empty)

func RemoveZWSPMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		data, err := io.ReadAll(c.Request.Body)
		if err != nil {
			_ = c.AbortWithError(http.StatusInternalServerError, err)
			return
		}

		if len(data) > 0 && hasZWSP(data) {
			s := replacer.Replace(string(data))
			c.Request.Body = io.NopCloser(bytes.NewBufferString(s))
		} else {
			c.Request.Body = io.NopCloser(bytes.NewBuffer(data))
		}

		c.Next()
	}
}

func hasZWSP(data []byte) bool {
	return bytes.ContainsAny(data, ZWSP) ||
		bytes.ContainsAny(data, ZWNBSP) ||
		bytes.ContainsAny(data, ZWNJ) ||
		bytes.ContainsAny(data, UTF8NUL) ||
		bytes.ContainsAny(data, UTF8NULStr)
}
