from .base import SaveStrategy
from .print_save import PrintSave
from .csv_save import CSVSave


def get_neo4j_save():
    try:
        from .neo4j_save import Neo4jSave
        return Neo4jSave
    except ImportError:
        raise ImportError(
            "Neo4j support requires the 'neo4j' package. "
            "Install with: pip install gh-graph-explorer[neo4j]"
        )


__all__ = ["SaveStrategy", "PrintSave", "CSVSave", "get_neo4j_save"]
