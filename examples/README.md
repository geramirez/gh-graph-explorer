# Examples

## repos.json

This file contains example configurations for collecting GitHub user work data.

### Format

Each entry in the JSON array should have:
- `username` (required): The GitHub username to fetch work data for
- `org` (optional): The organization to scope the search to

### Examples

1. **Organization-scoped search**: Fetches user work only within a specific organization
   ```json
   {
     "username": "user1",
     "org": "organization1"
   }
   ```

2. **Global search**: Omit the `org` field to perform a global search across all accessible repositories
   ```json
   {
     "username": "global-user"
   }
   ```

### Why organization scoping is preferable

Organization-level scoping provides several benefits:
- **Broader visibility**: See all user activity across all repos in the organization
- **Simpler configuration**: No need to list each repository individually
- **Reduced API calls**: Single query instead of multiple per-repository queries
- **Better insights**: Complete view of cross-repository collaboration within the org

## usage_example.py

See `usage_example.py` for programmatic usage examples of the UserWorkFetcher API.
