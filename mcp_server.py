import json
import os
import asyncio
from datetime import datetime
from typing import List, Optional

from gh_graph_explorer.collector import Collector
from gh_graph_explorer.save_strategies import get_neo4j_save
from gh_graph_explorer.graph_analyzer import GraphAnalyzer
from gh_graph_explorer.load_strategies import get_neo4j_loader

from fastmcp import FastMCP

mcp = FastMCP(name="GitHub Graph Explorer", version="1.0.0")


# Default Neo4j connection settings
DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USER = "neo4j"
DEFAULT_NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

# Valid relationship types that can be filtered by
VALID_RELATIONSHIP_TYPES = [
    "DISCUSSION_COMMENT",
    "DISCUSSION_CREATED",
    "ISSUE_COMMENT",
    "ISSUE_CREATED",
    "PR_COMMENT",
    "PR_CREATED",
    "PR_REVIEW_APPROVED",
    "PR_REVIEW_COMMENTED",
    "ISSUE_COMMENT_MENTIONED",
    "ISSUE_COMMENT",
    "PR_CREATED",
    "PR_REVIEW_APPROVED",
    "PR_REVIEW_COMMENTED",
    "DISCUSSION_COMMENT",
    "ISSUE_CREATED",
    "PR_REVIEW_DISMISSED",
    "PR_COMMENT_MENTIONED",
    "DISCUSSION_CREATED",
    "ISSUE_COMMENT_MENTIONED",
]


def _get_neo4j_credentials():
    """
    Helper function to get Neo4j credentials from environment variables or defaults.

    Returns:
        Tuple of (uri, username, password)
    """
    return (
        os.environ.get("NEO4J_URI", DEFAULT_NEO4J_URI),
        os.environ.get("NEO4J_USER", DEFAULT_NEO4J_USER),
        os.environ.get("NEO4J_PASSWORD", DEFAULT_NEO4J_PASSWORD),
    )


def _validate_relationship_types(relationship_types):
    """
    Helper function to validate relationship types.

    Args:
        relationship_types: List of relationship types to validate

    Returns:
        Tuple of (is_valid, error_message) where error_message is None if valid
    """
    if not relationship_types:
        return True, None

    invalid_types = [t for t in relationship_types if t not in VALID_RELATIONSHIP_TYPES]
    if invalid_types:
        return False, {
            "error": f"Invalid relationship types: {', '.join(invalid_types)}",
            "valid_types": VALID_RELATIONSHIP_TYPES,
        }
    return True, None


@mcp.tool("collect")
async def collect(
    user: str,
    org: str,
    since_iso: Optional[str] = None,
    until_iso: Optional[str] = None,
) -> dict:
    """
    Collect GitHub data for specified users, organizations and time period.

    Request parameters:
        - user: GitHub username (required)
        - org: GitHub organization (required)
        - since_iso: Start date in ISO format (optional, defaults to 7 days ago)
        - until_iso: End date in ISO format (optional, defaults to now)
    """
    # Validate required parameters
    if not all([user, org]):
        return {}

    # Create the orgs config
    orgs_config = [{"username": user, "org": org}]

    uri, username, password = _get_neo4j_credentials()

    # Create Neo4j save strategy (default for MCP server)
    Neo4jSave = get_neo4j_save()
    save_strategy = Neo4jSave(uri=uri, username=username, password=password)

    # Create collector with Neo4j save strategy
    collector = Collector(
        since_iso=since_iso,
        until_iso=until_iso,
        save_strategy=save_strategy,
    )

    # Collect data
    results = await collector.get(orgs_config)

    return {
        "message": f"Successfully processed organization {org} for user {user}",
        "results": results,
    }


@mcp.tool("analyze")
async def analyze(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    relationship_types: Optional[List[str]] = None,
) -> dict:
    """
    Analyze GitHub data with optional date filtering and relationship type filtering.

    Request parameters:
        - start_date: Start date in ISO format, e.g. "2024-01-01" (optional)
        - end_date: End date in ISO format, e.g. "2024-01-31" (optional)
        - relationship_types: List of relationship types to filter by (optional)
    """

    # Validate relationship types if provided
    is_valid, error = _validate_relationship_types(relationship_types)
    if not is_valid:
        return error

    # Build Neo4j query based on filters
    query = _build_neo4j_query(start_date, end_date, relationship_types)

    uri, username, password = _get_neo4j_credentials()

    # Create Neo4j loader with custom query
    Neo4jLoader = get_neo4j_loader()
    loader = Neo4jLoader(uri=uri, username=username, password=password, query=query)

    # Create and run analyzer
    analyzer = GraphAnalyzer(load_strategy=loader)
    analyzer.create()

    # Use the analyze method to get analysis results
    analysis_results = analyzer.analyze()

    return {
        "message": "Analysis completed successfully",
        "analysis_results": analysis_results,
        "filters": {"start_date": start_date, "end_date": end_date, "relationship_types": relationship_types},
    }


@mcp.tool("get_network")
async def get_network(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    relationship_types: Optional[List[str]] = None,
) -> dict:
    """
    Get network data as an edge list optimized for LLM parsing.

    Request parameters:
        - start_date: Start date in ISO format, e.g. "2024-01-01" (optional)
        - end_date: End date in ISO format, e.g. "2024-01-31" (optional)
        - relationship_types: List of relationship types to filter by (optional)
    """

    # Validate relationship types if provided
    is_valid, error = _validate_relationship_types(relationship_types)
    if not is_valid:
        return error

    # Build Neo4j query for edge list
    query = _build_neo4j_query(start_date, end_date, relationship_types)

    uri, username, password = _get_neo4j_credentials()

    # Create Neo4j loader with custom query
    Neo4jLoader = get_neo4j_loader()
    loader = Neo4jLoader(uri=uri, username=username, password=password, query=query)

    # Create graph analyzer and get the edge list directly from it
    analyzer = GraphAnalyzer(load_strategy=loader)
    analyzer.create()
    edges = analyzer.get_edges()

    return {
        "message": "Network edge list generated successfully",
        "edge_count": len(edges),
        "edge_list": json.dumps(edges, default=str),
        "filters": {"start_date": start_date, "end_date": end_date, "relationship_types": relationship_types},
    }


def _build_neo4j_query(
    start_date: Optional[str], end_date: Optional[str], relationship_types: List[str]
) -> str:
    """
    Build a Neo4j query based on filters.

    Args:
        start_date: Start date in ISO format (e.g. "2024-01-01")
        end_date: End date in ISO format (e.g. "2024-01-31")
        relationship_types: List of relationship types to filter by

    Returns:
        A Cypher query string
    """
    # Start with the base query
    query = "MATCH (source)-[rel]->(target)\n"
    conditions = []

    # Add date range filters if provided
    if start_date:
        conditions.append(f'rel.created_at >= "{start_date}"')
    if end_date:
        conditions.append(f'rel.created_at <= "{end_date}"')

    # Add relationship type filters if provided
    if relationship_types:
        type_conditions = []
        for rel_type in relationship_types:
            type_conditions.append(f'TYPE(rel) = "{rel_type}"')

        if type_conditions:
            conditions.append(f'({" OR ".join(type_conditions)})')

    # Add WHERE clause if there are conditions
    if conditions:
        query += f'WHERE {" AND ".join(conditions)}\n'

    # Complete the query
    query += "RETURN source.name AS source, target.url AS target, \n"
    query += "       TYPE(rel) AS type, properties(rel) AS properties"

    return query


# Main entry point
if __name__ == "__main__":
    if os.environ.get("MCP_TRANSPORT") == "http":
        asyncio.run(mcp.run(transport="http", host="0.0.0.0", port=8888))
    else:
        asyncio.run(mcp.run(transport="stdio"))
