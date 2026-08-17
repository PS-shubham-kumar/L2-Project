"""Tests for Gmail FastMCP tool server (email_tools.py)."""
from mcp_tools.email_tools import send_email_briefing, send_itinerary_email


def test_send_email_briefing_validation():
    result = send_email_briefing(to_email="invalid_email", subject="Test", body_html="<p>Test</p>")
    assert result["status"] == "error"
    assert result["delivered"] is False


def test_send_email_briefing_simulation():
    result = send_email_briefing(to_email="test@example.com", subject="Hello", body_html="<p>World</p>")
    assert result["delivered"] is True
    assert result["to"] == "test@example.com"


def test_send_itinerary_email():
    result = send_itinerary_email(
        to_email="traveler@example.com",
        location="Paris",
        itinerary_summary="Day 1: Louvre Museum\nDay 2: Eiffel Tower",
    )
    assert result["delivered"] is True
    assert result["to"] == "traveler@example.com"
