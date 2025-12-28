import os
import asyncio
from typing import List, Dict, Any, Optional

from .edge import Edge
from .collector import Collector
from .save_strategies import PrintSave, CSVSave, Neo4jSave
from .graph_analyzer import GraphAnalyzer
from .load_strategies import CSVLoader, Neo4jLoader
from .transformations.bipartite_collapser import BipartiteCollapser


# -------- Public Library API --------

async def collect(
    orgs: List[Dict[str, str]],
    *,
    since_iso: Optional[str] = None,
    until_iso: Optional[str] = None,
    output: str = "print",
    output_file: Optional[str] = None,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Collect GitHub work data for users, optionally scoped to organizations.

    Returns a dictionary keyed by org identifier with success/error details.
    """
    if neo4j_password is None:
        neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")

    if output == "csv":
        save_strategy = CSVSave(filename=output_file)
    elif output == "neo4j":
        save_strategy = Neo4jSave(uri=neo4j_uri, username=neo4j_user, password=neo4j_password)
    else:
        save_strategy = PrintSave()

    collector = Collector(
        since_iso=since_iso,
        until_iso=until_iso,
        save_strategy=save_strategy,
    )

    return await collector.get(orgs)


def analyze(
    *,
    source: str,
    file: Optional[str] = None,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: Optional[str] = None,
    neo4j_query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze the graph and return metrics and summaries.
    """
    if neo4j_password is None:
        neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")

    if source == "csv":
        if not file:
            raise ValueError("file must be provided for csv source")
        loader = CSVLoader(filepath=file)
    elif source == "neo4j":
        loader = Neo4jLoader(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
            query=neo4j_query,
        )
    else:
        raise ValueError("source must be 'csv' or 'neo4j'")

    analyzer = GraphAnalyzer(load_strategy=loader).create()
    return analyzer.analyze()


def get_edges(
    *,
    source: str,
    file: Optional[str] = None,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: Optional[str] = None,
    neo4j_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return edges as a list of dictionaries with source, target and attributes.
    """
    if neo4j_password is None:
        neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")

    if source == "csv":
        if not file:
            raise ValueError("file must be provided for csv source")
        loader = CSVLoader(filepath=file)
    elif source == "neo4j":
        loader = Neo4jLoader(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
            query=neo4j_query,
        )
    else:
        raise ValueError("source must be 'csv' or 'neo4j'")

    analyzer = GraphAnalyzer(load_strategy=loader).create()

    for source, target, data in analyzer.graph.edges(data=True):
        yield Edge(
            edge_type=data["type"],
            title=data["title"], 
            created_at=data["created_at"], 
            login=source,
            url=data["url"],
            parent_url=target,
        )

def bipartite_collapse(
    *,
    source: str,
    file: str,
    output_file: str,
) -> None:
    """
    Perform bipartite collapse transformation; currently supports CSV input.
    """
    if source != "csv":
        raise ValueError("Currently only csv source is supported for bipartite_collapse")

    loader = CSVLoader(filepath=file)
    collapser = BipartiteCollapser(load_strategy=loader)
    collapser.run(output_file=output_file)


# Convenience runner for async collect in non-async contexts

def collect_sync(*args, **kwargs):
    return asyncio.run(collect(*args, **kwargs))
