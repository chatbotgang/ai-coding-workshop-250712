package common

import "net/http"

type ErrorCode struct {
	Name       string
	StatusCode int
}

/*
	General error codes
*/

var ErrorCodeInternalProcess = ErrorCode{
	Name:       "INTERNAL_PROCESS",
	StatusCode: http.StatusInternalServerError,
}

/*
	Authentication and Authorization error codes
*/

var ErrorCodeAuthPermissionDenied = ErrorCode{
	Name:       "AUTH_PERMISSION_DENIED",
	StatusCode: http.StatusForbidden,
}

var ErrorCodeAuthNotAuthenticated = ErrorCode{
	Name:       "AUTH_NOT_AUTHENTICATED",
	StatusCode: http.StatusUnauthorized,
}

/*
	Resource-related error codes
*/

var ErrorCodeResourceNotFound = ErrorCode{
	Name:       "RESOURCE_NOT_FOUND",
	StatusCode: http.StatusNotFound,
}

/*
	Parameter-related error codes
*/

var ErrorCodeParameterInvalid = ErrorCode{
	Name:       "PARAMETER_INVALID",
	StatusCode: http.StatusBadRequest,
}

var ErrorCodeMessageContentInvalid = ErrorCode{
	Name:       "MESSAGE_CONTENT_INVALID",
	StatusCode: http.StatusBadRequest,
}

var ErrorCodeUnsupportedChannelType = ErrorCode{
	Name:       "UNSUPPORTED_CHANNEL_TYPE",
	StatusCode: http.StatusBadRequest,
}

/*
	Remote server-related error codes
*/

var ErrorCodeRemoteNetworkError = ErrorCode{
	Name:       "REMOTE_NETWORK_ERROR",
	StatusCode: http.StatusBadGateway,
}

var ErrorCodeRemoteNetworkErrorNoRetry = ErrorCode{
	Name:       "REMOTE_NETWORK_ERROR_NO_RETRY",
	StatusCode: http.StatusBadGateway,
}

var ErrorCodeRemoteClientError = ErrorCode{
	Name:       "REMOTE_CLIENT_ERROR",
	StatusCode: http.StatusBadRequest,
}

var ErrorCodeRemoteServerError = ErrorCode{
	Name:       "REMOTE_SERVER_ERROR",
	StatusCode: http.StatusBadGateway,
}
