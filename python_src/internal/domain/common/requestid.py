"""Request ID management utilities."""

import uuid
from contextvars import ContextVar

# Context variable to store request ID
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def new_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    """Set request ID in current context."""
    _request_id_var.set(request_id)


def get_request_id() -> str:
    """Get request ID from current context."""
    return _request_id_var.get()


def get_request_id_or_new() -> str:
    """Get request ID from context or generate a new one."""
    request_id = get_request_id()
    if not request_id:
        request_id = new_request_id()
        set_request_id(request_id)
    return request_id
