"""Tests for domain error functionality."""

from http import HTTPStatus

import pytest

from internal.domain.common.error import DomainError, new_error
from internal.domain.common.error_code import NOT_FOUND, VALIDATION_ERROR, ErrorCode


class TestDomainError:
    """Test DomainError class."""

    def test_create_domain_error_minimal(self):
        """Test creating DomainError with minimal parameters."""
        code = ErrorCode(name="TEST_ERROR", status_code=HTTPStatus.BAD_REQUEST)
        error = DomainError(code=code)

        assert error.code == code
        assert error.err is None
        assert error._client_msg == ""
        assert error.remote_status == 0
        assert error.detail == {}

    def test_create_domain_error_full(self):
        """Test creating DomainError with all parameters."""
        code = ErrorCode(name="FULL_ERROR", status_code=HTTPStatus.NOT_FOUND)
        original_error = ValueError("Original error")
        client_msg = "User-friendly message"
        remote_status = 503
        detail = {"field": "value", "count": 42}

        error = DomainError(
            code=code, err=original_error, client_msg=client_msg, remote_status=remote_status, detail=detail
        )

        assert error.code == code
        assert error.err == original_error
        assert error._client_msg == client_msg
        assert error.remote_status == remote_status
        assert error.detail == detail

    def test_domain_error_message_building(self):
        """Test DomainError message building logic."""
        code = ErrorCode(name="MESSAGE_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        # Test with only client message
        error1 = DomainError(code=code, client_msg="Client message")
        assert str(error1) == "Client message"

        # Test with remote status and client message
        error2 = DomainError(code=code, client_msg="Client message", remote_status=404)
        assert str(error2) == "404: Client message"

        # Test with original error and client message
        original_error = ValueError("Original error")
        error3 = DomainError(code=code, err=original_error, client_msg="Client message")
        assert str(error3) == "Original error: Client message"

        # Test with all components
        error4 = DomainError(code=code, err=original_error, client_msg="Client message", remote_status=503)
        assert str(error4) == "503: Original error: Client message"

    def test_domain_error_name_method(self):
        """Test DomainError name() method."""
        code = ErrorCode(name="NAMED_ERROR", status_code=HTTPStatus.BAD_REQUEST)
        error = DomainError(code=code)

        assert error.name() == "NAMED_ERROR"

        # Test with empty name
        empty_code = ErrorCode(name="", status_code=HTTPStatus.BAD_REQUEST)
        empty_error = DomainError(code=empty_code)
        assert empty_error.name() == "UNKNOWN_ERROR"

    def test_domain_error_client_msg_method(self):
        """Test DomainError client_msg() method."""
        code = ErrorCode(name="CLIENT_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        # Test with client message
        error1 = DomainError(code=code, client_msg="User message")
        assert error1.client_msg() == "User message"

        # Test without client message
        error2 = DomainError(code=code)
        assert error2.client_msg() == ""

    def test_domain_error_http_status_method(self):
        """Test DomainError http_status() method."""
        code = ErrorCode(name="HTTP_ERROR", status_code=HTTPStatus.NOT_FOUND)
        error = DomainError(code=code)

        assert error.http_status() == 404

        # Test with zero status code
        zero_code = ErrorCode(name="ZERO_ERROR", status_code=0)
        zero_error = DomainError(code=zero_code)
        assert zero_error.http_status() == 500

    def test_domain_error_remote_http_status_method(self):
        """Test DomainError remote_http_status() method."""
        code = ErrorCode(name="REMOTE_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        # Test with remote status
        error1 = DomainError(code=code, remote_status=503)
        assert error1.remote_http_status() == 503

        # Test without remote status
        error2 = DomainError(code=code)
        assert error2.remote_http_status() == 0

    def test_domain_error_get_detail_method(self):
        """Test DomainError get_detail() method."""
        code = ErrorCode(name="DETAIL_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        # Test with detail
        detail = {"key": "value", "number": 123}
        error1 = DomainError(code=code, detail=detail)
        assert error1.get_detail() == detail

        # Test without detail (should default to empty dict)
        error2 = DomainError(code=code)
        assert error2.get_detail() == {}

        # Test with None detail (should convert to empty dict)
        error3 = DomainError(code=code, detail=None)
        assert error3.get_detail() == {}

    def test_domain_error_inheritance(self):
        """Test that DomainError properly inherits from Exception."""
        code = ErrorCode(name="INHERITANCE_ERROR", status_code=HTTPStatus.BAD_REQUEST)
        error = DomainError(code=code, client_msg="Test message")

        assert isinstance(error, Exception)
        assert isinstance(error, DomainError)

        # Test raising and catching
        with pytest.raises(DomainError) as exc_info:
            raise error

        caught_error = exc_info.value
        assert caught_error.code == code
        assert caught_error.client_msg() == "Test message"

    def test_domain_error_with_predefined_codes(self):
        """Test DomainError with predefined error codes."""
        # Test with VALIDATION_ERROR
        validation_error = DomainError(code=VALIDATION_ERROR, client_msg="Invalid input")
        assert validation_error.name() == "VALIDATION_ERROR"
        assert validation_error.http_status() == 400

        # Test with NOT_FOUND
        not_found_error = DomainError(code=NOT_FOUND, client_msg="Resource not found")
        assert not_found_error.name() == "NOT_FOUND"
        assert not_found_error.http_status() == 404


class TestNewErrorFunction:
    """Test new_error() convenience function."""

    def test_new_error_minimal(self):
        """Test new_error with minimal parameters."""
        code = ErrorCode(name="NEW_ERROR", status_code=HTTPStatus.BAD_REQUEST)
        error = new_error(code=code)

        assert isinstance(error, DomainError)
        assert error.code == code
        assert error.err is None
        assert error._client_msg == ""
        assert error.remote_status == 0
        assert error.detail == {}

    def test_new_error_full(self):
        """Test new_error with all parameters."""
        code = ErrorCode(name="NEW_FULL_ERROR", status_code=HTTPStatus.FORBIDDEN)
        original_error = RuntimeError("Runtime issue")
        client_msg = "Access denied"
        remote_status = 403
        detail = {"user_id": "123", "resource": "secret"}

        error = new_error(
            code=code, err=original_error, client_msg=client_msg, remote_status=remote_status, detail=detail
        )

        assert isinstance(error, DomainError)
        assert error.code == code
        assert error.err == original_error
        assert error._client_msg == client_msg
        assert error.remote_status == remote_status
        assert error.detail == detail

    def test_new_error_with_predefined_codes(self):
        """Test new_error with predefined error codes."""
        # Test with VALIDATION_ERROR
        validation_error = new_error(
            code=VALIDATION_ERROR, client_msg="Invalid email format", detail={"field": "email"}
        )

        assert validation_error.name() == "VALIDATION_ERROR"
        assert validation_error.http_status() == 400
        assert validation_error.client_msg() == "Invalid email format"
        assert validation_error.get_detail() == {"field": "email"}

    def test_new_error_convenience(self):
        """Test that new_error is more convenient than direct DomainError construction."""
        code = ErrorCode(name="CONVENIENCE_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        # Using new_error
        error1 = new_error(code, client_msg="Easy to use")

        # Using DomainError directly
        error2 = DomainError(code=code, client_msg="Easy to use")

        # Both should be equivalent
        assert error1.code == error2.code
        assert error1.client_msg() == error2.client_msg()
        assert error1.name() == error2.name()
        assert error1.http_status() == error2.http_status()


class TestErrorIntegration:
    """Integration tests for error components."""

    def test_error_workflow(self):
        """Test a complete error handling workflow."""
        # Create a custom error code
        custom_code = ErrorCode(name="WORKFLOW_ERROR", status_code=HTTPStatus.UNPROCESSABLE_ENTITY)

        # Create an error with context
        original_exception = ValueError("Database connection failed")
        error = new_error(
            code=custom_code,
            err=original_exception,
            client_msg="Unable to process request",
            remote_status=503,
            detail={"service": "database", "retry_after": 30},
        )

        # Verify all properties
        assert error.name() == "WORKFLOW_ERROR"
        assert error.http_status() == 422
        assert error.remote_http_status() == 503
        assert error.client_msg() == "Unable to process request"
        assert error.get_detail()["service"] == "database"
        assert "Database connection failed" in str(error)

    def test_error_chaining(self):
        """Test error chaining scenarios."""
        # Simulate nested error handling
        try:
            # Simulate a low-level error
            raise ConnectionError("Network timeout")
        except ConnectionError as e:
            # Wrap in domain error
            domain_error = new_error(
                code=NOT_FOUND, err=e, client_msg="Service temporarily unavailable", remote_status=503
            )

            # Verify the chain
            assert isinstance(domain_error.err, ConnectionError)
            assert "Network timeout" in str(domain_error)
            assert domain_error.client_msg() == "Service temporarily unavailable"
