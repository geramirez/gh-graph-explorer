from typing import List, Dict, Any, Optional
import datetime
from .user_work_fetcher import UserWorkFetcher
from .edge_factory import EdgeFactory
from .save_strategies import SaveStrategy, PrintSave


class Collector:
    """
    Class to collect GitHub work data from multiple repositories for a user.
    """

    def __init__(
        self,
        since_iso: str = None,
        until_iso: str = None,
        save_strategy: Optional[SaveStrategy] = None,
    ):
        """
        Initialize the Collector with optional date range.

        Args:
            since_iso: DateTime string in ISO format for start date filtering (optional, defaults to 1 days ago)
            until_iso: DateTime string in ISO format for end date filtering (optional, defaults to now)
            save_strategy: Strategy to use for saving edges. If None, uses PrintSave by default.
        """
        # Set default since_iso to 1 days ago if not provided
        if since_iso is None:
            today = datetime.datetime.now(datetime.timezone.utc)
            since_date = today - datetime.timedelta(days=1)
            since_iso = since_date.isoformat()

        self.since_iso = since_iso
        self.until_iso = until_iso
        self.fetcher = UserWorkFetcher()
        self.save_strategy = save_strategy if save_strategy else PrintSave()

    async def get(self, repos: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Collect GitHub work data from multiple organizations.

        Args:
            repos: List of dictionaries, each containing 'username' and optionally 'org' keys.
                   If 'org' is not provided, performs a global search for the user.

        Returns:
            Dictionary with organization identifiers as keys and fetched data as values
        """
        if not repos:
            raise ValueError("No organizations provided")

        results = {}

        # Process each organization
        for repo_info in repos:
            # Validate required keys
            required_keys = ["username"]
            if not all(key in repo_info for key in required_keys):
                missing = [key for key in required_keys if key not in repo_info]
                raise ValueError(f"Missing required keys in organization info: {missing}")

            # Create a unique identifier for this organization (use username if org not provided)
            org_id = repo_info.get('org', f"global-{repo_info['username']}")

            # Fetch data for this organization
            try:
                result = await self.fetcher.get(
                    username=repo_info["username"],
                    org=repo_info.get("org"),
                    since_iso=self.since_iso,
                    until_iso=self.until_iso,
                )

                for edge in EdgeFactory(
                    data=result,
                    username=repo_info["username"],
                    since_iso=self.since_iso,
                    until_iso=self.until_iso,
                ).generate_edges():

                    self.save_strategy.save(edge)

                results[org_id] = {"success": True}

            except Exception as e:
                # Store the error for this organization but continue with others
                results[org_id] = {"error": str(e)}

        # Finalize the save strategy (e.g., close files)
        self.save_strategy.finalize()

        return results
