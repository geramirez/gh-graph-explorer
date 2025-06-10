from typing import Optional
import os
import datetime
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


# Define the GraphQL query as a string
USER_WORK_QUERY = """
query getUserWork($username:String!, $issuesCreatedQuery:String!, $prsCreatedQuery:String!, $prContributionsQuery:String!, $issueCommentsQuery:String!, $discussionsCreatedQuery:String!, $discussionsInvolvedQuery:String!) {
  issuesCreated:search(type: ISSUE, query: $issuesCreatedQuery, first: 20) {
    edges {
      node {
        ... on Issue {
          createdAt
          bodyText
          title
          url
        }
      }
    }
    pageInfo {
      endCursor
      startCursor
      hasNextPage
      hasPreviousPage
    }
  }
  prsCreated:search(type: ISSUE, query: $prsCreatedQuery, first: 20) {
    edges {
      node {
        ... on PullRequest {
          title
          createdAt
          url
          bodyText
        }
      }
    }
  }
  prReviewsAndCommits:search(type: ISSUE, query: $prContributionsQuery, first: 20) {
    edges {
      node {
        ... on PullRequest {
          createdAt
          title
          url
          author {
            login
          }
          bodyText
          reviews(first: 20, author:$username) {
            nodes {
              state
              createdAt
              url
              bodyText
            }
          }
        }
      }
    }
  }
  issueComments:search(type: ISSUE, query: $issueCommentsQuery, first: 20) {
    nodes {
      ... on Issue {
        title
        url
        comments(first: 20) {
          nodes {
            createdAt
            bodyText
            author {
              login
            }
            url
          }
        }
      }
    }
  }
  discussionsCreated:search(type: DISCUSSION, query: $discussionsCreatedQuery, first: 20) {
    nodes {
      ... on Discussion {
        author {
          login
        }
        title
        createdAt
        number
        url
        bodyText
        repository {
          nameWithOwner
        }
      }
    }
  }
  discussionComments:search(type: DISCUSSION, query: $discussionsInvolvedQuery, first: 20) {
    nodes {
      ... on Discussion {
        title
        url
        comments(first: 20) {
          nodes {
              author {
              login
            }
            bodyText
            createdAt
            url
          }
        }
        repository {
          nameWithOwner
        }
      }
    }
  }
}
"""


class UserWorkFetcher:
    def __init__(self, github_token: str = None):
        """
        Initialize the UserWorkFetcher with a GitHub token.

        Args:
            github_token: GitHub personal access token with appropriate permissions.
                          If None, will try to use GITHUB_TOKEN from environment variables.
        """
        if github_token is None:
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token is None:
                raise ValueError(
                    "GitHub token not provided and GITHUB_TOKEN environment variable not set"
                )

        # Set up the transport with the GitHub GraphQL API endpoint
        transport = AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {github_token}"},
        )

        # Create the client
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        self.query = gql(USER_WORK_QUERY)

    def _build_prs_created_query(
        self,
        username: str,
        since_date: datetime.datetime,
        until_date: datetime.datetime,
    ) -> str:
        """Build query for PRs created by the user"""
        query = f"author:{username} is:pr updated:{since_date.strftime('%Y-%m-%d')}..{until_date.strftime('%Y-%m-%d')}"
        return query

    def _build_issues_created_query(
        self,
        username: str,
        since_date: datetime.datetime,
        until_date: datetime.datetime,
    ) -> str:
        """Build query for Issues created by the user"""
        query = f"author:{username} is:issue updated:{since_date.strftime('%Y-%m-%d')}..{until_date.strftime('%Y-%m-%d')}"
        return query

    def _build_pr_contributions_query(
        self,
        username: str,
        since_date: datetime.datetime,
        until_date: datetime.datetime,
    ) -> str:
        """Build query for PRs the user contributed to but didn't author"""
        query = f"involves:{username} is:pr updated:{since_date.strftime('%Y-%m-%d')}..{until_date.strftime('%Y-%m-%d')}"
        return query

    def _build_issue_comments_query(
        self,
        username: str,
        since_date: datetime.datetime,
        until_date: datetime.datetime,
    ) -> str:
        """Build query for issues with user comments"""
        query = f"commenter:{username} is:issue updated:{since_date.strftime('%Y-%m-%d')}..{until_date.strftime('%Y-%m-%d')}"
        return query

    def _build_discussions_created_query(
        self,
        username: str,
        since_date: datetime.datetime,
        until_date: datetime.datetime,
    ) -> str:
        """Build query for discussions created by the user"""
        query = f"author:{username} is:discussion updated:{since_date.strftime('%Y-%m-%d')}..{until_date.strftime('%Y-%m-%d')}"
        return query

    def _build_discussions_involved_query(
        self,
        username: str,
        since_date: datetime.datetime,
        until_date: datetime.datetime,
    ) -> str:
        """Build query for discussions the user is involved in but didn't create"""
        query = f"involves:{username} is:discussion updated:{since_date.strftime('%Y-%m-%d')}..{until_date.strftime('%Y-%m-%d')}"
        return query

    async def get(
        self,
        username: str,
        owner: str,
        repo: str,
        since_iso: str = None,
        until_iso: str = None,
    ) -> dict:
        """
        Simplified method to get user's GitHub work data.

        Args:
            username: GitHub username
            owner: Repository owner
            repo: Repository name
            since_iso: DateTime string in ISO format for filtering by date
                      (if None, will default to 1 days ago)
            until_iso: DateTime string in ISO format for filtering by date
                      (if None, will default to now)

        Returns:
            The GraphQL query results as a dictionary
        """
        # Calculate since_date if since_iso is not provided (default to 1 days ago)
        if since_iso is None:
            today = datetime.datetime.now(datetime.timezone.utc)
            since_date = today - datetime.timedelta(days=1)
            since_iso = since_date.isoformat()
        else:
            # Parse the ISO string to a datetime object for building queries
            since_date = datetime.datetime.fromisoformat(
                since_iso.replace("Z", "+00:00")
            )

        # Calculate until_date if until_iso is not provided (default to now)
        if until_iso is None:
            until_date = datetime.datetime.now(datetime.timezone.utc)
            until_iso = until_date.isoformat()
        else:
            # Parse the ISO string to a datetime object for building queries
            until_date = datetime.datetime.fromisoformat(
                until_iso.replace("Z", "+00:00")
            )

        # Build all query strings
        name_with_owner_query = f"repo:{owner}/{repo} "
        prs_created_query = name_with_owner_query + self._build_prs_created_query(
            username, since_date, until_date
        )

        issues_created_query = name_with_owner_query + self._build_issues_created_query(
            username, since_date, until_date
        )

        pr_contributions_query = (
            name_with_owner_query
            + self._build_pr_contributions_query(username, since_date, until_date)
        )
        issue_comments_query = name_with_owner_query + self._build_issue_comments_query(
            username, since_date, until_date
        )
        discussions_created_query = (
            name_with_owner_query
            + self._build_discussions_created_query(username, since_date, until_date)
        )
        discussions_involved_query = (
            name_with_owner_query
            + self._build_discussions_involved_query(username, since_date, until_date)
        )

        # Execute the query with built parameters
        return await self.execute_query(
            username=username,
            issues_created_query=issues_created_query,
            prs_created_query=prs_created_query,
            pr_contributions_query=pr_contributions_query,
            issue_comments_query=issue_comments_query,
            discussions_created_query=discussions_created_query,
            discussions_involved_query=discussions_involved_query,
        )

    async def execute_query(
        self,
        username: str,
        issues_created_query: str,
        prs_created_query: str,
        pr_contributions_query: str,
        issue_comments_query: str,
        discussions_created_query: str,
        discussions_involved_query: str,
    ) -> dict:
        """
        Execute the getUserWork GraphQL query with the provided parameters.

        Args:
            username: GitHub username
            repo: Repository name
            since_iso: DateTime string in ISO format for filtering by date
            issues_created_query: Search query for issues created by user
            prs_created_query: Search query for PRs created by user
            pr_contributions_query: Search query for PRs the user contributed to
            issue_comments_query: Search query for issues with user comments
            discussions_created_query: Search query for discussions created by user
            discussions_involved_query: Search query for discussions the user is involved in

        Returns:
            The GraphQL query results as a dictionary
        """
        variables = {
            "username": username,
            "issuesCreatedQuery": issues_created_query,
            "prsCreatedQuery": prs_created_query,
            "prContributionsQuery": pr_contributions_query,  # Add missing parameter
            "issueCommentsQuery": issue_comments_query,
            "discussionsCreatedQuery": discussions_created_query,
            "discussionsInvolvedQuery": discussions_involved_query,
        }

        # Execute the query
        result = await self.client.execute_async(self.query, variable_values=variables)
        return result
