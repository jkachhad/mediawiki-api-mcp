"""Wiki page protect tool for MediaWiki API MCP integration."""

import logging
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..client import MediaWikiClient
from ..config import MediaWikiConfig

logger = logging.getLogger(__name__)


def register_wiki_page_protect_tool(mcp: FastMCP, get_config: Callable[[], MediaWikiConfig]) -> None:
    """Register the wiki_page_protect tool with the MCP server."""

    @mcp.tool()
    async def wiki_page_protect(
        protections: str,
        title: str = "",
        pageid: int = 0,
        expiry: str = "infinite",
        reason: str = "",
        tags: str = "",
        cascade: bool = False,
        watchlist: str = "preferences",
        watchlistexpiry: str = "",
    ) -> str:
        """Change the protection level of a page.

        Args:
            protections: Pipe-separated protection levels in the form action=level, e.g. "edit=sysop|move=sysop". Use level "all" (e.g. "edit=all|move=all") to remove protection. Non-existent pages only accept "create=level".
            title: Title of the page to (un)protect. Cannot be used together with pageid.
            pageid: Page ID of the page to (un)protect. Cannot be used together with title.
            expiry: Pipe-separated expiry timestamps, one per protection, or a single value for all. Use "infinite" (default) for no expiry, a relative time like "1 week", or an ISO 8601 timestamp.
            reason: Reason for (un)protecting.
            tags: Change tags to apply to the entry in the protection log (separate with |).
            cascade: Also protect templates and pages transcluded on this page. Only works with edit=sysop.
            watchlist: Unconditionally add or remove the page from the current user's watchlist, use preferences (ignored for bot users) or do not change watch.
            watchlistexpiry: Watchlist expiry timestamp. Omit this parameter entirely to leave the current expiry unchanged.
        """
        try:
            config = get_config()
            async with MediaWikiClient(config) as client:
                # Import here to avoid circular imports
                from ..handlers import handle_protect_page

                # Convert FastMCP parameters to handler arguments
                arguments = {
                    "title": title if title else None,
                    "pageid": pageid if pageid > 0 else None,
                    "protections": protections.split("|") if protections else None,
                    "expiry": expiry.split("|") if expiry else None,
                    "reason": reason if reason else None,
                    "tags": tags.split("|") if tags else None,
                    "cascade": cascade,
                    "watchlist": watchlist if watchlist != "preferences" else None,
                    "watchlistexpiry": watchlistexpiry if watchlistexpiry else None,
                }

                result = await handle_protect_page(client, arguments)
                # Return the formatted text from the handler
                return result[0].text if result else "No results"
        except Exception as e:
            logger.error(f"Wiki page protect failed: {e}")
            return f"Error: {str(e)}"
