import networkx as nx
from networkx.algorithms import bipartite
from typing import Optional, Dict, List, Set, Any
from .load_strategies import Loader


class GraphAnalyzer:
    """
    Class responsible for creating and analyzing a networkx MultiGraph using a loader strategy.

    This class takes a loader implementation and uses it to create a networkx MultiGraph
    representing relationships between entities in a GitHub social network.
    """

    def __init__(self, load_strategy: Loader):
        """
        Initialize the GraphAnalyzer with a loader strategy.

        Args:
            load_strategy: A concrete implementation of the Loader abstract class
        """
        self.load_strategy = load_strategy
        self.graph = None

    def create(self) -> "GraphAnalyzer":
        """
        Create a networkx MultiGraph using the configured loader strategy and store it in memory.

        Returns:
            Self reference for method chaining
        """
        self.graph = self.load_strategy.create_graph()
        return self

    def _is_username(self, node: str) -> bool:
        """
        Determine if a node represents a GitHub username.

        For now, this is a simple heuristic that assumes nodes without slashes or dots
        that don't end with common file extensions are usernames.

        Args:
            node: Node identifier to check

        Returns:
            Boolean indicating if the node is likely a username
        """
        # This is a very simple heuristic and might need refinement based on your data
        if isinstance(node, str):
            if "/" not in node and not node.endswith(
                (".js", ".py", ".md", ".txt", ".html", ".css")
            ):
                return True
        return False

    def _is_resource(self, node: str) -> bool:
        """
        Determine if a node represents a GitHub resource (repo, file, etc).

        Args:
            node: Node identifier to check

        Returns:
            Boolean indicating if the node is likely a resource
        """
        return not self._is_username(node)

    def get_edges(self) -> List[Dict[str, Any]]:
        """
        Extract edge data from the graph in a format optimized for LLM parsing.

        Returns:
            List of dictionaries with source, target, type and properties for each edge
        """
        if self.graph is None:
            return {"error": "No graph has been created yet. Call create() first."}
        return [e for e in nx.generate_edgelist(self.graph)]

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the graph and return structured information including:
        - Basic stats (nodes, edges)
        - Degree statistics
        - Centrality measures
        - Connected components
        - Clustering information
        - Path analysis
        - GitHub-specific analysis
        - Connectivity analysis
        - Disconnected nodes analysis

        Returns:
            Dictionary containing the analysis results
        """
        if self.graph is None:
            return {"error": "No graph has been created yet. Call create() first."}

        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()

        # Skip analysis for empty graphs
        if num_nodes == 0:
            return {"message": "Graph is empty. No further analysis available."}

        # Count users vs resources
        users = [n for n in self.graph.nodes() if self._is_username(n)]
        resources = [n for n in self.graph.nodes() if self._is_resource(n)]

        # Basic degree statistics
        degrees = [d for _, d in self.graph.degree()]
        avg_degree = sum(degrees) / num_nodes if degrees else 0
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0

        # Centrality measures

        # Degree centrality - fraction of nodes a node is connected to
        degree_centrality = nx.degree_centrality(self.graph)

        # Get top users by centrality
        top_users_by_degree = [
            (n, c) for n, c in degree_centrality.items() if self._is_username(n)
        ]
        top_users_by_degree = sorted(
            top_users_by_degree, key=lambda x: x[1], reverse=True
        )[:5]

        # Get top resources by centrality
        top_resources_by_degree = [
            (n, c) for n, c in degree_centrality.items() if self._is_resource(n)
        ]
        top_resources_by_degree = sorted(
            top_resources_by_degree, key=lambda x: x[1], reverse=True
        )[:5]

        # Connectivity analysis
        components = list(nx.connected_components(self.graph))
        largest_component = len(max(components, key=len)) if components else 0
        giant_ratio = largest_component / num_nodes if num_nodes > 0 else 0

        # Get nodes that are not part of the largest connected component
        if components:
            largest_component = max(components, key=len)
            disconnected_nodes = [
                n for n in self.graph.nodes() if n not in largest_component
            ]

        else:
            disconnected_nodes = []

        # Categorize disconnected nodes
        disconnected_users = [n for n in disconnected_nodes if self._is_username(n)]
        disconnected_resources = [n for n in disconnected_nodes if self._is_resource(n)]
        connectivity_metrics = {}

        largest_component_graph = self.graph.subgraph(max(components, key=len))
        # Find key users whose removal would disconnect the network
        min_cut = nx.minimum_node_cut(largest_component_graph)
        connectivity_metrics["minimum_node_cut"] = list(min_cut)
        connectivity_metrics["min_cut_size"] = len(min_cut)

        # Bipartite analysis
        top_nodes = {n for n, d in largest_component_graph.nodes(data=True) if d["bipartite"] == 0}
        bottom_nodes = set(largest_component_graph) - top_nodes

        people_graph = bipartite.projected_graph(nx.Graph(largest_component_graph), bottom_nodes)
        people_betweeness = nx.betweenness_centrality(people_graph, k=10, endpoints=True)

        top_people_by_betweeness = [
            (n, c) for n, c in people_betweeness.items()
        ]
        top_people_by_betweeness = sorted(
            top_people_by_betweeness, key=lambda x: x[1], reverse=True
        )[:5]

        # Relationship types distribution
        rel_types = {}
        for _, _, attr in self.graph.edges(data=True):
            rel_type = attr.get("type", "unknown")
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        # Build and return the results dictionary
        return {
            "basic_stats": {
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "users_count": len(users),
                "resources_count": len(resources),
                "users_percentage": (
                    (len(users) / num_nodes * 100) if num_nodes > 0 else 0
                ),
                "resources_percentage": (
                    (len(resources) / num_nodes * 100) if num_nodes > 0 else 0
                ),
            },
            "degree_stats": {
                "avg_degree": avg_degree,
                "max_degree": max_degree,
                "min_degree": min_degree,
            },
            "top_users_by_centrality": [
                {"user": user, "centrality": centrality}
                for user, centrality in top_users_by_degree
            ],
            "top_resources_by_centrality": [
                {"resource": resource, "centrality": centrality}
                for resource, centrality in top_resources_by_degree
            ],
            "connectivity": {"giant_component_ratio": giant_ratio},
            "disconnected_nodes": {
                "total": len(disconnected_nodes),
                "percentage": (
                    (len(disconnected_nodes) / num_nodes * 100) if num_nodes > 0 else 0
                ),
                "users_count": len(disconnected_users),
                "resources_count": len(disconnected_resources),
                "sample_users": disconnected_users[:5] if disconnected_users else [],
            },
            "connectivity_metrics": connectivity_metrics,
            "relationship_types_distribution": rel_types,
            "top_people_by_betweeness":  [
                {"user": user, "centrality": centrality}
                for user, centrality in top_people_by_betweeness
            ],
        }
