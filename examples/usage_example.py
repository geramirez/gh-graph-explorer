"""
Usage example for organization-scoped GitHub work fetcher.

This example demonstrates how to use the UserWorkFetcher with organization-level scoping.
Organization scoping is preferable because it provides:
- Broader visibility of user activity across all repos in the org
- Reduced need to enumerate each individual repository
- Simpler configuration (just username + org instead of username + owner + repo)
"""

import asyncio
from src.user_work_fetcher import UserWorkFetcher


async def example_org_scoped_fetch():
    """
    Example: Fetch user work scoped to a specific organization.
    """
    fetcher = UserWorkFetcher()
    
    # Fetch alice's work in the 'acme' organization
    result = await fetcher.get(
        username="alice",
        org="acme"
    )
    
    print("Issues created:", len(result.get("issuesCreated", {}).get("edges", [])))
    print("PRs created:", len(result.get("prsCreated", {}).get("edges", [])))
    print("PR contributions:", len(result.get("prReviewsAndCommits", {}).get("edges", [])))
    
    return result


async def example_global_search():
    """
    Example: Fetch user work globally (no org constraint).
    """
    fetcher = UserWorkFetcher()
    
    # Fetch bob's work across all accessible repositories
    result = await fetcher.get(
        username="bob",
        org=None  # None means global search
    )
    
    print("Issues created:", len(result.get("issuesCreated", {}).get("edges", [])))
    print("PRs created:", len(result.get("prsCreated", {}).get("edges", [])))
    
    return result


async def example_with_date_range():
    """
    Example: Fetch user work with custom date range.
    """
    fetcher = UserWorkFetcher()
    
    # Fetch charlie's work in 'widgets-inc' org from last 7 days
    result = await fetcher.get(
        username="charlie",
        org="widgets-inc",
        since_iso="2024-01-01T00:00:00Z",
        until_iso="2024-01-07T23:59:59Z"
    )
    
    print("Issues created:", len(result.get("issuesCreated", {}).get("edges", [])))
    
    return result


if __name__ == "__main__":
    print("Example 1: Organization-scoped search")
    print("=" * 50)
    # asyncio.run(example_org_scoped_fetch())
    
    print("\nExample 2: Global search (no org constraint)")
    print("=" * 50)
    # asyncio.run(example_global_search())
    
    print("\nExample 3: With date range")
    print("=" * 50)
    # asyncio.run(example_with_date_range())
    
    print("\nNote: Uncomment the asyncio.run() calls above to actually execute the examples.")
    print("Make sure GITHUB_TOKEN environment variable is set with appropriate permissions.")
