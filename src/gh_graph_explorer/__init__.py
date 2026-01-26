from .load_strategies import Loader, CSVLoader, get_neo4j_loader
from .graph_analyzer import GraphAnalyzer
from .edge import Edge
from .edge_factory import EdgeFactory
from .save_strategies import SaveStrategy, PrintSave, CSVSave, get_neo4j_save
from .collector import Collector
from .user_work_fetcher import UserWorkFetcher
from .api import collect, collect_sync, analyze, get_edges, bipartite_collapse

__version__ = "0.1.0"


def get_mcp_server():
    """
    Get the MCP server instance.

    Returns:
        The FastMCP server instance.

    Raises:
        ImportError: If fastmcp is not installed.
    """
    try:
        from .mcp_server import mcp
        return mcp
    except ImportError:
        raise ImportError(
            "MCP support requires the 'fastmcp' package. "
            "Install with: pip install gh-graph-explorer[mcp]"
        )


__all__ = [
    "Loader",
    "CSVLoader",
    "get_neo4j_loader",
    "GraphAnalyzer",
    "Edge",
    "EdgeFactory",
    "SaveStrategy",
    "PrintSave",
    "CSVSave",
    "get_neo4j_save",
    "Collector",
    "UserWorkFetcher",
    "collect",
    "collect_sync",
    "analyze",
    "get_edges",
    "bipartite_collapse",
    "get_mcp_server",
    "__version__",
]
