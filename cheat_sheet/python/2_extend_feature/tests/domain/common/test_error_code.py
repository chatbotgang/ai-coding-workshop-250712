"""Tests for error code functionality."""

from http import HTTPStatus

import pytest
from pydantic import ValidationError

from internal.domain.common.error_code import (
    FORBIDDEN,
    INTERNAL_ERROR,
    NOT_FOUND,
    UNAUTHORIZED,
    UNKNOWN_ERROR,
    VALIDATION_ERROR,
    ErrorCode,
)


class TestErrorCode:
    """Test ErrorCode pydantic model."""

    def test_create_error_code_with_explicit_status(self):
        """Test creating ErrorCode with explicit status code."""
        error = ErrorCode(name="TEST_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        assert error.name == "TEST_ERROR"
        assert error.status_code == HTTPStatus.BAD_REQUEST
        assert error.status_code == 400

    def test_create_error_code_with_default_status(self):
        """Test creating ErrorCode with default status code."""
        error = ErrorCode(name="DEFAULT_ERROR")

        assert error.name == "DEFAULT_ERROR"
        assert error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert error.status_code == 500

    def test_error_code_immutability(self):
        """Test that ErrorCode is immutable (frozen)."""
        error = ErrorCode(name="IMMUTABLE_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        with pytest.raises(ValidationError):
            error.name = "CHANGED_NAME"

        with pytest.raises(ValidationError):
            error.status_code = HTTPStatus.NOT_FOUND

    def test_error_code_equality(self):
        """Test ErrorCode equality comparison."""
        error1 = ErrorCode(name="TEST_ERROR", status_code=HTTPStatus.BAD_REQUEST)
        error2 = ErrorCode(name="TEST_ERROR", status_code=HTTPStatus.BAD_REQUEST)
        error3 = ErrorCode(name="DIFFERENT_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        assert error1 == error2
        assert error1 != error3

    def test_error_code_string_representation(self):
        """Test ErrorCode string representation."""
        error = ErrorCode(name="TEST_ERROR", status_code=HTTPStatus.BAD_REQUEST)

        str_repr = str(error)
        assert "TEST_ERROR" in str_repr
        assert "400" in str_repr

    def test_error_code_validation(self):
        """Test ErrorCode validation."""
        # Valid name
        ErrorCode(name="VALID_NAME", status_code=HTTPStatus.OK)

        # Empty name should work
        ErrorCode(name="", status_code=HTTPStatus.OK)

        # Invalid status code type should raise ValidationError
        with pytest.raises(ValidationError):
            ErrorCode(name="TEST_ERROR", status_code="invalid")  # type: ignore[arg-type]

    def test_error_code_serialization(self):
        """Test ErrorCode serialization to dict."""
        error = ErrorCode(name="SERIALIZE_ERROR", status_code=HTTPStatus.NOT_FOUND)

        data = error.model_dump()
        assert data == {"name": "SERIALIZE_ERROR", "status_code": 404}

    def test_error_code_deserialization(self):
        """Test ErrorCode deserialization from dict."""
        data = {"name": "DESERIALIZE_ERROR", "status_code": 403}

        error = ErrorCode.model_validate(data)
        assert error.name == "DESERIALIZE_ERROR"
        assert error.status_code == HTTPStatus.FORBIDDEN


class TestPredefinedErrorCodes:
    """Test predefined error code constants."""

    def test_unknown_error(self):
        """Test UNKNOWN_ERROR constant."""
        assert UNKNOWN_ERROR.name == "UNKNOWN_ERROR"
        assert UNKNOWN_ERROR.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_validation_error(self):
        """Test VALIDATION_ERROR constant."""
        assert VALIDATION_ERROR.name == "VALIDATION_ERROR"
        assert VALIDATION_ERROR.status_code == HTTPStatus.BAD_REQUEST

    def test_not_found_error(self):
        """Test NOT_FOUND constant."""
        assert NOT_FOUND.name == "NOT_FOUND"
        assert NOT_FOUND.status_code == HTTPStatus.NOT_FOUND

    def test_unauthorized_error(self):
        """Test UNAUTHORIZED constant."""
        assert UNAUTHORIZED.name == "UNAUTHORIZED"
        assert UNAUTHORIZED.status_code == HTTPStatus.UNAUTHORIZED

    def test_forbidden_error(self):
        """Test FORBIDDEN constant."""
        assert FORBIDDEN.name == "FORBIDDEN"
        assert FORBIDDEN.status_code == HTTPStatus.FORBIDDEN

    def test_internal_error(self):
        """Test INTERNAL_ERROR constant."""
        assert INTERNAL_ERROR.name == "INTERNAL_ERROR"
        assert INTERNAL_ERROR.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_predefined_errors_are_immutable(self):
        """Test that predefined error codes are immutable."""
        with pytest.raises(ValidationError):
            VALIDATION_ERROR.name = "CHANGED_NAME"

        with pytest.raises(ValidationError):
            NOT_FOUND.status_code = HTTPStatus.OK

    def test_all_predefined_errors_exist(self):
        """Test that all expected predefined errors exist and have correct types."""
        predefined_errors = [UNKNOWN_ERROR, VALIDATION_ERROR, NOT_FOUND, UNAUTHORIZED, FORBIDDEN, INTERNAL_ERROR]

        for error in predefined_errors:
            assert isinstance(error, ErrorCode)
            assert isinstance(error.name, str)
            assert isinstance(error.status_code, int)
            assert error.name  # Not empty
            assert 100 <= error.status_code <= 599  # Valid HTTP status code range
