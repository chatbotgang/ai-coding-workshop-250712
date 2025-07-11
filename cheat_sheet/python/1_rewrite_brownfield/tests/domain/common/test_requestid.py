"""Tests for request ID management functionality."""

import asyncio
import uuid

from internal.domain.common.requestid import (
    _request_id_var,
    get_request_id,
    get_request_id_or_new,
    new_request_id,
    set_request_id,
)


class TestRequestIdFunctions:
    """Test request ID management functions."""

    def test_new_request_id_format(self):
        """Test that new_request_id generates valid UUIDs."""
        request_id = new_request_id()

        # Should be a string
        assert isinstance(request_id, str)

        # Should be a valid UUID format
        uuid_obj = uuid.UUID(request_id)
        assert str(uuid_obj) == request_id

        # Should be version 4 UUID
        assert uuid_obj.version == 4

    def test_new_request_id_uniqueness(self):
        """Test that new_request_id generates unique IDs."""
        ids = [new_request_id() for _ in range(100)]

        # All should be unique
        assert len(set(ids)) == 100

    def test_set_and_get_request_id(self):
        """Test setting and getting request ID."""
        test_id = "test-request-id-123"

        # Set the request ID
        set_request_id(test_id)

        # Get the request ID
        retrieved_id = get_request_id()

        assert retrieved_id == test_id

    def test_get_request_id_empty_default(self):
        """Test that get_request_id returns empty string when not set."""
        # Clear any existing request ID
        _request_id_var.set("")

        # Should return empty string
        assert get_request_id() == ""

    def test_get_request_id_or_new_with_existing(self):
        """Test get_request_id_or_new when request ID already exists."""
        existing_id = "existing-request-id"
        set_request_id(existing_id)

        # Should return the existing ID
        result = get_request_id_or_new()
        assert result == existing_id

    def test_get_request_id_or_new_without_existing(self):
        """Test get_request_id_or_new when no request ID exists."""
        # Clear any existing request ID
        _request_id_var.set("")

        # Should generate and set a new ID
        result = get_request_id_or_new()

        # Should be a valid UUID
        uuid.UUID(result)  # Will raise if not valid

        # Should be set in context
        assert get_request_id() == result

    def test_request_id_context_isolation(self):
        """Test that request IDs are isolated per context."""
        results = []

        async def set_and_get_id(test_id: str):
            set_request_id(test_id)
            # Yield control to allow other tasks to run
            await asyncio.sleep(0.001)
            results.append(get_request_id())

        async def test_isolation():
            # Run multiple tasks concurrently
            await asyncio.gather(set_and_get_id("id-1"), set_and_get_id("id-2"), set_and_get_id("id-3"))

        # Run the test
        asyncio.run(test_isolation())

        # Each task should have maintained its own request ID
        assert len(results) == 3
        assert "id-1" in results
        assert "id-2" in results
        assert "id-3" in results

    def test_request_id_inheritance_in_tasks(self):
        """Test that request IDs are inherited by child tasks."""
        parent_id = "parent-request-id"
        child_results = []

        async def child_task():
            # Child should inherit parent's request ID
            child_results.append(get_request_id())

        async def parent_task():
            # Set request ID in parent
            set_request_id(parent_id)

            # Create child task
            await asyncio.create_task(child_task())

        # Run the test
        asyncio.run(parent_task())

        # Child should have inherited parent's request ID
        assert len(child_results) == 1
        assert child_results[0] == parent_id

    def test_request_id_modification_in_child_task(self):
        """Test that child task modifications don't affect parent context."""
        parent_id = "parent-id"
        child_id = "child-id"
        final_parent_id = None

        async def child_task():
            # Child modifies request ID
            set_request_id(child_id)
            return get_request_id()

        async def parent_task():
            nonlocal final_parent_id

            # Set request ID in parent
            set_request_id(parent_id)

            # Create child task that modifies request ID
            child_result = await asyncio.create_task(child_task())

            # Check that child modification doesn't affect parent
            final_parent_id = get_request_id()

            return child_result

        # Run the test
        child_result = asyncio.run(parent_task())

        # Child should have its own modified ID
        assert child_result == child_id

        # Parent should retain its original ID
        assert final_parent_id == parent_id

    def test_context_var_direct_access(self):
        """Test direct access to the context variable."""
        # This tests the internal implementation
        test_id = "direct-access-test"

        # Set via direct context var access
        _request_id_var.set(test_id)

        # Should be retrievable via our function
        assert get_request_id() == test_id

        # Should also be retrievable via direct access
        assert _request_id_var.get() == test_id

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        # Set empty string
        set_request_id("")

        # get_request_id should return empty string
        assert get_request_id() == ""

        # get_request_id_or_new should generate new ID
        new_id = get_request_id_or_new()
        assert new_id != ""
        uuid.UUID(new_id)  # Should be valid UUID

        # Should now return the generated ID
        assert get_request_id() == new_id

    def test_whitespace_handling(self):
        """Test handling of whitespace-only strings."""
        whitespace_id = "   "
        set_request_id(whitespace_id)

        # Should preserve whitespace
        assert get_request_id() == whitespace_id

        # get_request_id_or_new should treat it as existing
        result = get_request_id_or_new()
        assert result == whitespace_id


class TestRequestIdIntegration:
    """Integration tests for request ID functionality."""

    def test_typical_request_flow(self):
        """Test a typical request processing flow."""
        # Simulate incoming request without request ID
        _request_id_var.set("")

        # Middleware generates request ID
        request_id = get_request_id_or_new()
        assert request_id != ""

        # Request processing uses the same ID
        processing_id = get_request_id()
        assert processing_id == request_id

        # Logging uses the same ID
        logging_id = get_request_id()
        assert logging_id == request_id

    def test_request_with_existing_id(self):
        """Test processing request that already has an ID."""
        incoming_id = "incoming-request-id"

        # Simulate incoming request with existing ID
        set_request_id(incoming_id)

        # Middleware should use existing ID
        middleware_id = get_request_id_or_new()
        assert middleware_id == incoming_id

        # All subsequent operations use the same ID
        assert get_request_id() == incoming_id

    def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        results = []

        async def process_request(request_num: int):
            # Clear any existing request ID to simulate new request
            _request_id_var.set("")

            # Each request gets its own ID
            request_id = get_request_id_or_new()

            # Simulate some async work
            await asyncio.sleep(0.001)

            # Verify ID is still correct
            final_id = get_request_id()
            results.append((request_num, request_id, final_id))

        async def test_concurrent():
            # Process multiple requests concurrently
            await asyncio.gather(*[process_request(i) for i in range(10)])

        # Run the test
        asyncio.run(test_concurrent())

        # Verify results
        assert len(results) == 10

        # Each request should have consistent ID throughout
        for _, initial_id, final_id in results:
            assert initial_id == final_id
            # Should be valid UUID
            uuid.UUID(initial_id)

        # All request IDs should be unique
        all_ids = [initial_id for _, initial_id, _ in results]
        assert len(set(all_ids)) == 10

    def test_nested_operation_context(self):
        """Test request ID in nested operations."""
        main_request_id = "main-request"
        nested_results = []

        async def nested_operation(level: int):
            # Should inherit request ID from parent context
            current_id = get_request_id()
            nested_results.append((level, current_id))

            if level > 0:
                # Create deeper nesting
                await asyncio.create_task(nested_operation(level - 1))

        async def main_operation():
            # Set main request ID
            set_request_id(main_request_id)

            # Perform nested operations
            await nested_operation(3)

        # Run the test
        asyncio.run(main_operation())

        # All nested operations should have the same request ID
        assert len(nested_results) == 4  # Levels 3, 2, 1, 0
        for _, request_id in nested_results:
            assert request_id == main_request_id
