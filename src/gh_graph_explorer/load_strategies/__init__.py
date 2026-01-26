from .base import Loader
from .csv_loader import CSVLoader


def get_neo4j_loader():
    try:
        from .neo4j_loader import Neo4jLoader
        return Neo4jLoader
    except ImportError:
        raise ImportError(
            "Neo4j support requires the 'neo4j' package. "
            "Install with: pip install gh-graph-explorer[neo4j]"
        )


__all__ = ["Loader", "CSVLoader", "get_neo4j_loader"]
