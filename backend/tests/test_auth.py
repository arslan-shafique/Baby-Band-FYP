"""
Auth Tests — Test authentication and user profile endpoints.

TODO: Implement tests in Phase 2
"""

import pytest


class TestAuthEndpoints:
    """Tests for /api/auth/* endpoints."""

    def test_health_check(self):
        """Verify the API health check returns ok."""
        # TODO: Use FastAPI TestClient
        pass

    def test_get_profile_without_token(self):
        """Verify 401 when no auth token is provided."""
        # TODO: Implement
        pass

    def test_get_profile_with_valid_token(self):
        """Verify user profile is returned with valid token."""
        # TODO: Implement with mock Firebase token
        pass

    def test_update_settings(self):
        """Verify settings are updated correctly."""
        # TODO: Implement
        pass
