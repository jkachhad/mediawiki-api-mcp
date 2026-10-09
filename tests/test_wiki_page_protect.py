"""Tests for wiki page protect functionality."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mediawiki_api_mcp.client import MediaWikiClient
from mediawiki_api_mcp.client_modules.client_page import MediaWikiPageClient
from mediawiki_api_mcp.handlers.wiki_page_protect import handle_protect_page


@pytest.fixture
def mock_client():
    """Create a mock MediaWiki client."""
    client = AsyncMock(spec=MediaWikiClient)
    return client


@pytest.fixture
def mock_auth():
    """Create a mock auth client that already holds a CSRF token."""
    auth = MagicMock()
    auth.csrf_token = "token+\\"
    auth._make_request = AsyncMock(return_value={
        "protect": {
            "title": "Test Page",
            "reason": "Test protection",
            "protections": [
                {"edit": "sysop", "expiry": "infinite"},
                {"move": "sysop", "expiry": "infinite"}
            ]
        }
    })
    return auth


@pytest.mark.asyncio
async def test_handle_protect_page_success(mock_client):
    """Test successful page protection."""
    mock_client.protect_page.return_value = {
        "title": "Test Page",
        "reason": "Test protection",
        "protections": [
            {"edit": "sysop", "expiry": "infinite"},
            {"move": "sysop", "expiry": "infinite"}
        ]
    }

    arguments = {
        "title": "Test Page",
        "protections": ["edit=sysop", "move=sysop"],
        "expiry": ["infinite"],
        "reason": "Test protection"
    }

    result = await handle_protect_page(mock_client, arguments)

    assert len(result) == 1
    assert "Successfully changed protection for page 'Test Page'" in result[0].text
    assert "edit=sysop (expires infinite)" in result[0].text
    assert "move=sysop (expires infinite)" in result[0].text
    assert "Test protection" in result[0].text
    mock_client.protect_page.assert_called_once_with(
        title="Test Page",
        protections=["edit=sysop", "move=sysop"],
        expiry=["infinite"],
        reason="Test protection"
    )


@pytest.mark.asyncio
async def test_handle_protect_page_with_pageid(mock_client):
    """Test page protection by page ID."""
    mock_client.protect_page.return_value = {
        "title": "Test Page",
        "reason": "",
        "protections": [{"edit": "autoconfirmed", "expiry": "2026-01-01T00:00:00Z"}]
    }

    arguments = {
        "pageid": 123,
        "protections": ["edit=autoconfirmed"],
        "expiry": ["1 week"]
    }

    result = await handle_protect_page(mock_client, arguments)

    assert "edit=autoconfirmed (expires 2026-01-01T00:00:00Z)" in result[0].text
    mock_client.protect_page.assert_called_once_with(
        pageid=123,
        protections=["edit=autoconfirmed"],
        expiry=["1 week"]
    )


@pytest.mark.asyncio
async def test_handle_protect_page_unprotect(mock_client):
    """Test removing protection reports level 'all'."""
    mock_client.protect_page.return_value = {
        "title": "Test Page",
        "reason": "No longer needed",
        "protections": [{"edit": "", "expiry": "infinite"}]
    }

    arguments = {
        "title": "Test Page",
        "protections": ["edit=all"],
        "reason": "No longer needed"
    }

    result = await handle_protect_page(mock_client, arguments)

    assert "edit=all (expires infinite)" in result[0].text


@pytest.mark.asyncio
async def test_handle_protect_page_with_options(mock_client):
    """Test page protection with cascade, tags and watchlist options."""
    mock_client.protect_page.return_value = {
        "title": "Test Page",
        "reason": "Cascade",
        "cascade": "",
        "protections": [{"edit": "sysop", "expiry": "infinite"}]
    }

    arguments = {
        "title": "Test Page",
        "protections": ["edit=sysop"],
        "cascade": True,
        "tags": ["admin-action"],
        "watchlist": "watch",
        "watchlistexpiry": "2026-12-31T00:00:00Z"
    }

    result = await handle_protect_page(mock_client, arguments)

    assert "Cascading protection enabled." in result[0].text
    mock_client.protect_page.assert_called_once_with(
        title="Test Page",
        protections=["edit=sysop"],
        cascade=True,
        tags=["admin-action"],
        watchlist="watch",
        watchlistexpiry="2026-12-31T00:00:00Z"
    )


@pytest.mark.asyncio
async def test_handle_protect_page_missing_identifier(mock_client):
    """Test that a title or page ID is required."""
    result = await handle_protect_page(mock_client, {"protections": ["edit=sysop"]})

    assert "Either 'title' or 'pageid' must be provided" in result[0].text
    mock_client.protect_page.assert_not_called()


@pytest.mark.asyncio
async def test_handle_protect_page_both_identifiers(mock_client):
    """Test that title and page ID cannot be combined."""
    result = await handle_protect_page(
        mock_client, {"title": "Test Page", "pageid": 123, "protections": ["edit=sysop"]}
    )

    assert "Cannot specify both 'title' and 'pageid'" in result[0].text
    mock_client.protect_page.assert_not_called()


@pytest.mark.asyncio
async def test_handle_protect_page_missing_protections(mock_client):
    """Test that protections are required."""
    result = await handle_protect_page(mock_client, {"title": "Test Page"})

    assert "'protections' parameter is required" in result[0].text
    mock_client.protect_page.assert_not_called()


@pytest.mark.asyncio
async def test_handle_protect_page_failed(mock_client):
    """Test an API error response is reported."""
    mock_client.protect_page.return_value = {
        "error": {"code": "permissiondenied", "info": "You don't have permission to change protection levels."}
    }

    result = await handle_protect_page(
        mock_client, {"title": "Test Page", "protections": ["edit=sysop"]}
    )

    assert "Protect failed" in result[0].text
    assert "permissiondenied" in result[0].text


@pytest.mark.asyncio
async def test_handle_protect_page_exception(mock_client):
    """Test an exception from the client is reported."""
    mock_client.protect_page.side_effect = Exception("Network error")

    result = await handle_protect_page(
        mock_client, {"title": "Test Page", "protections": ["edit=sysop"]}
    )

    assert "Error protecting page: Network error" in result[0].text


@pytest.mark.asyncio
async def test_client_protect_page_request(mock_auth):
    """Test the client sends a correctly formed protect request."""
    page_client = MediaWikiPageClient(mock_auth)

    result = await page_client.protect_page(
        title="Test Page",
        protections=["edit=sysop", "move=sysop"],
        expiry=["infinite"],
        reason="Test protection",
        cascade=True
    )

    assert result["title"] == "Test Page"
    mock_auth._make_request.assert_called_once()
    call_args = mock_auth._make_request.call_args
    assert call_args[0][0] == "POST"
    data = call_args[1]["data"]
    assert data["action"] == "protect"
    assert data["title"] == "Test Page"
    assert data["protections"] == "edit=sysop|move=sysop"
    assert data["expiry"] == "infinite"
    assert data["reason"] == "Test protection"
    assert data["cascade"] == "1"
    assert data["token"] == "token+\\"
    assert "pageid" not in data
    assert "watchlist" not in data


@pytest.mark.asyncio
async def test_client_protect_page_validation(mock_auth):
    """Test the client rejects invalid argument combinations."""
    page_client = MediaWikiPageClient(mock_auth)

    with pytest.raises(ValueError, match="Either title or pageid"):
        await page_client.protect_page(protections=["edit=sysop"])
    with pytest.raises(ValueError, match="Cannot specify both"):
        await page_client.protect_page(title="Test Page", pageid=1, protections=["edit=sysop"])
    with pytest.raises(ValueError, match="At least one protection"):
        await page_client.protect_page(title="Test Page", protections=[])

    mock_auth._make_request.assert_not_called()
