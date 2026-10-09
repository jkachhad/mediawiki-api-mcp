"""MediaWiki protect handlers for MCP server."""

import logging
from collections.abc import Sequence
from typing import Any

import mcp.types as types

from ..client import MediaWikiClient

logger = logging.getLogger(__name__)


async def handle_protect_page(
    client: MediaWikiClient,
    arguments: dict[str, Any]
) -> Sequence[types.TextContent]:
    """Handle wiki_page_protect tool calls."""
    title = arguments.get("title")
    pageid = arguments.get("pageid")
    protections = arguments.get("protections")

    if not title and not pageid:
        return [types.TextContent(
            type="text",
            text="Error: Either 'title' or 'pageid' must be provided"
        )]

    if title and pageid:
        return [types.TextContent(
            type="text",
            text="Error: Cannot specify both 'title' and 'pageid'"
        )]

    if not protections:
        return [types.TextContent(
            type="text",
            text="Error: 'protections' parameter is required (e.g. 'edit=sysop|move=sysop', or 'all' to unprotect)"
        )]

    # Extract protect parameters
    protect_params: dict[str, Any] = {
        "protections": protections,
    }

    if title:
        protect_params["title"] = title
    else:
        protect_params["pageid"] = pageid

    # Add optional parameters only if they're provided and not defaults
    if arguments.get("expiry"):
        protect_params["expiry"] = arguments["expiry"]
    if arguments.get("reason"):
        protect_params["reason"] = arguments["reason"]
    if arguments.get("tags"):
        protect_params["tags"] = arguments["tags"]
    if arguments.get("cascade", False):
        protect_params["cascade"] = arguments["cascade"]
    if arguments.get("watchlist") and arguments["watchlist"] != "preferences":
        protect_params["watchlist"] = arguments["watchlist"]
    if arguments.get("watchlistexpiry"):
        protect_params["watchlistexpiry"] = arguments["watchlistexpiry"]

    try:
        result = await client.protect_page(**protect_params)

        if "title" in result:
            page_title = result.get("title", title or pageid)
            reason_used = result.get("reason", "No reason provided")

            applied = []
            for protection in result.get("protections", []):
                expiry = protection.get("expiry", "infinite")
                for action, level in protection.items():
                    if action != "expiry":
                        applied.append(f"{action}={level or 'all'} (expires {expiry})")

            response_text = f"Successfully changed protection for page '{page_title}'. "
            response_text += f"Protections: {', '.join(applied) if applied else 'none'}. "
            response_text += f"Reason: {reason_used}."
            if "cascade" in result:
                response_text += " Cascading protection enabled."

            return [types.TextContent(
                type="text",
                text=response_text
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Protect failed: {result}"
            )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error protecting page: {str(e)}"
        )]
