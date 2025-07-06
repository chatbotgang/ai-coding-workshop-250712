"""Error code definitions for domain errors."""

from http import HTTPStatus

from pydantic import BaseModel, ConfigDict


class ErrorCode(BaseModel):
    """Defines an error code with name and HTTP status."""

    model_config = ConfigDict(frozen=True)

    name: str
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR


# Common error codes
UNKNOWN_ERROR = ErrorCode(name="UNKNOWN_ERROR", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
VALIDATION_ERROR = ErrorCode(name="VALIDATION_ERROR", status_code=HTTPStatus.BAD_REQUEST)
NOT_FOUND = ErrorCode(name="NOT_FOUND", status_code=HTTPStatus.NOT_FOUND)
UNAUTHORIZED = ErrorCode(name="UNAUTHORIZED", status_code=HTTPStatus.UNAUTHORIZED)
FORBIDDEN = ErrorCode(name="FORBIDDEN", status_code=HTTPStatus.FORBIDDEN)
INTERNAL_ERROR = ErrorCode(name="INTERNAL_ERROR", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
