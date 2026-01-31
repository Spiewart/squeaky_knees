"""Tests for health check endpoint."""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self):
        """Health check endpoint should return 200 when healthy."""
        client = Client()
        response = client.get(reverse("health"))
        assert response.status_code == 200

    def test_health_check_returns_json(self):
        """Health check should return JSON response."""
        client = Client()
        response = client.get(reverse("health"))
        assert response["Content-Type"] == "application/json"

    def test_health_check_has_status_ok(self):
        """Health check should indicate status ok."""
        client = Client()
        response = client.get(reverse("health"))
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_has_database_connected(self):
        """Health check should confirm database is connected."""
        client = Client()
        response = client.get(reverse("health"))
        data = response.json()
        assert data["database"] == "connected"

    def test_health_check_url_exists(self):
        """Health check endpoint should be accessible at /health/."""
        client = Client()
        response = client.get("/health/")
        assert response.status_code == 200

    def test_health_check_no_authentication_required(self):
        """Health check should not require authentication."""
        client = Client()
        response = client.get(reverse("health"))
        # Not a 403 or 302 redirect
        assert response.status_code == 200
