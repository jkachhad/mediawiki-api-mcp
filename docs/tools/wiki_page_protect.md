### wiki_page_protect

Change the protection level of a MediaWiki page: restrict who can edit, move or (for pages that don't exist yet) create it, for a limited time or indefinitely. The same tool removes protection. This tool provides access to MediaWiki's protect API.

**Page Identification Parameters:**
- `title` (string): Title of the page to (un)protect. Cannot be used together with `pageid`
- `pageid` (integer): Page ID of the page to (un)protect. Cannot be used together with `title`

**Protection Parameters:**
- `protections` (string, required): Pipe-separated list of protections in the form `action=level`
  - Actions: `edit`, `move`, and `create` (only for pages that don't exist). Wikis with extensions may offer more, such as `upload` for files
  - Levels: `all` (no restriction; use it to remove protection), `autoconfirmed`, `sysop`, or any custom level configured on the wiki
  - Example: `"edit=sysop|move=sysop"`
- `expiry` (string): Pipe-separated expiry for each protection, in the same order as `protections`, or a single value applied to all (default: `"infinite"`). Accepts `infinite`, relative times such as `"1 week"`, or ISO 8601 timestamps
- `cascade` (boolean): Also protect templates and pages transcluded on this page (default: false). MediaWiki only allows cascading with `edit=sysop`

**Reason Parameters:**
- `reason` (string): Reason for the change (default: empty). Appears in the protection log

**Change Tracking Parameters:**
- `tags` (string): Pipe-separated list of change tags to apply to the entry in the protection log

**Watchlist Management Parameters:**
- `watchlist` (string): Watchlist behavior for the page (default: "preferences")
  - `"nochange"`: Don't change current watchlist status
  - `"preferences"`: Use user preferences (typically ignored for bot users)
  - `"unwatch"`: Remove from watchlist
  - `"watch"`: Add to watchlist
- `watchlistexpiry` (string): Watchlist expiry timestamp in ISO 8601 format. Omit to leave current expiry unchanged

**Response Information:**
The tool returns the protections now applied to the page, each with its expiry, plus the reason and whether cascading is on.

**Important Notes:**
- Protecting requires the `protect` right (normally administrators). With a bot password, the "Protect, block and unblock users" grant must also be enabled on Special:BotPasswords
- Each call sets the page's whole protection state, so list every action you want protected. Actions left out of `protections` may be cleared
- Changes are recorded in the protection log with the reason and tags provided

**Usage Examples:**
- Admin-only editing and moving, indefinitely: `{"title": "Example Page", "protections": "edit=sysop|move=sysop", "reason": "High-traffic page"}`
- Block new and anonymous editors for one week: `{"title": "Example Page", "protections": "edit=autoconfirmed", "expiry": "1 week", "reason": "Vandalism"}`
- Different expiry per action: `{"title": "Example Page", "protections": "edit=sysop|move=sysop", "expiry": "1 month|infinite"}`
- Remove all protection: `{"title": "Example Page", "protections": "edit=all|move=all", "reason": "No longer needed"}`
- Prevent a page from being created: `{"title": "Unwanted Page", "protections": "create=sysop"}`
