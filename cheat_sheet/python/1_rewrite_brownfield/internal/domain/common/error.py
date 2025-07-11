"""Domain error handling classes and utilities."""

from typing import Any, Protocol

from internal.domain.common.error_code import ErrorCode


class Error(Protocol):
    """Protocol defining the interface for domain errors."""

    def __str__(self) -> str:
        """Return error message."""
        ...

    def name(self) -> str:
        """Return error name."""
        ...

    def client_msg(self) -> str:
        """Return client-facing message."""
        ...


class DomainError(Exception):
    """Domain error used for expressing errors occurring in application."""

    def __init__(
        self,
        code: ErrorCode,
        err: Exception | None = None,
        client_msg: str = "",
        remote_status: int = 0,
        detail: dict[str, Any] | None = None,
    ):
        self.code = code
        self.err = err
        self._client_msg = client_msg
        self.remote_status = remote_status
        self.detail = detail or {}
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        """Build error message from components."""
        msgs = []

        if self.remote_status != 0:
            msgs.append(str(self.remote_status))

        if self.err is not None:
            msgs.append(str(self.err))

        if self._client_msg:
            msgs.append(self._client_msg)

        return ": ".join(msgs)

    def name(self) -> str:
        """Return error name."""
        if not self.code.name:
            return "UNKNOWN_ERROR"
        return self.code.name

    def client_msg(self) -> str:
        """Return client-facing message."""
        return self._client_msg

    def http_status(self) -> int:
        """Return HTTP status code."""
        if self.code.status_code == 0:
            return 500
        return self.code.status_code

    def remote_http_status(self) -> int:
        """Return remote HTTP status code."""
        return self.remote_status

    def get_detail(self) -> dict[str, Any]:
        """Return error detail."""
        return self.detail


def new_error(
    code: ErrorCode,
    err: Exception | None = None,
    client_msg: str = "",
    remote_status: int = 0,
    detail: dict[str, Any] | None = None,
) -> DomainError:
    """Create a new domain error."""
    return DomainError(code=code, err=err, client_msg=client_msg, remote_status=remote_status, detail=detail)
