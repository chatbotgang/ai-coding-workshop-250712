package validator

import (
	"github.com/gin-gonic/gin/binding"
	"github.com/go-playground/validator/v10"
)

func RegisteValidator() {
	// inject tag text and corresponding function here
	validators := map[string]validator.Func{}

	for funcName, function := range validators {
		if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
			// i think we need to define a error here
			_ = v.RegisterValidation(funcName, function)
		}
	}
}
