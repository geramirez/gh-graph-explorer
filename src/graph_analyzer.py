import networkx as nx
from typing import Optional, Dict, List, Set, Any
from .load_strategies import Loader
from collections import Counter

class GraphAnalyzer:
    """
    Class responsible for creating and analyzing a networkx DiGraph using a loader strategy.
    
    This class takes a loader implementation and uses it to create a networkx DiGraph
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
    
    def create(self) -> 'GraphAnalyzer':
        """
        Create a networkx DiGraph using the configured loader strategy and store it in memory.
        
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
            if '/' not in node and not node.endswith(('.js', '.py', '.md', '.txt', '.html', '.css')):
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
        top_users_by_degree = [(n, c) for n, c in degree_centrality.items() 
                              if self._is_username(n)]
        top_users_by_degree = sorted(top_users_by_degree, key=lambda x: x[1], reverse=True)[:5]
        
        # Get top resources by centrality
        top_resources_by_degree = [(n, c) for n, c in degree_centrality.items() 
                                  if self._is_resource(n)]
        top_resources_by_degree = sorted(top_resources_by_degree, key=lambda x: x[1], reverse=True)[:5]
        
        # Connectivity analysis
        
        # For directed graphs, we analyze weakly and strongly connected components
        if nx.is_directed(self.graph):
            weak_components = list(nx.weakly_connected_components(self.graph))
            strong_components = list(nx.strongly_connected_components(self.graph))
            
            num_weak_components = len(weak_components)
            num_strong_components = len(strong_components)
            largest_weak_component = len(max(weak_components, key=len)) if weak_components else 0
            largest_strong_component = len(max(strong_components, key=len)) if strong_components else 0
            giant_ratio = largest_weak_component / num_nodes if num_nodes > 0 else 0
            
            # Get nodes that are not part of the largest connected component
            if weak_components:
                largest_component = max(weak_components, key=len)
                disconnected_nodes = [n for n in self.graph.nodes() if n not in largest_component]
            else:
                disconnected_nodes = []
        else:
            # For undirected graphs
            components = list(nx.connected_components(self.graph))
            num_components = len(components)
            largest_component = len(max(components, key=len)) if components else 0
            giant_ratio = largest_component / num_nodes if num_nodes > 0 else 0
            
            # For compatibility with the directed graph case
            num_weak_components = num_components
            num_strong_components = 0
            largest_weak_component = largest_component
            largest_strong_component = 0
            
            # Get nodes that are not part of the largest connected component
            if components:
                largest_component = max(components, key=len)
                disconnected_nodes = [n for n in self.graph.nodes() if n not in largest_component]
            else:
                disconnected_nodes = []
        
        # Categorize disconnected nodes
        disconnected_users = [n for n in disconnected_nodes if self._is_username(n)]
        disconnected_resources = [n for n in disconnected_nodes if self._is_resource(n)]
        
        # Check for completely isolated nodes (degree 0)
        isolated_nodes = list(nx.isolates(self.graph))
        
        # Find nodes with only incoming or only outgoing connections
        if nx.is_directed(self.graph):
            only_incoming = [n for n in self.graph.nodes() 
                            if self.graph.in_degree(n) > 0 and self.graph.out_degree(n) == 0]
            only_outgoing = [n for n in self.graph.nodes() 
                            if self.graph.in_degree(n) == 0 and self.graph.out_degree(n) > 0]
            
            num_only_incoming = len(only_incoming)
            num_only_outgoing = len(only_outgoing)
        else:
            only_incoming = only_outgoing = []
            num_only_incoming = num_only_outgoing = 0
        
        # Clustering coefficient - how nodes tend to cluster together
        try:
            avg_clustering = nx.average_clustering(self.graph)
        except Exception:
            avg_clustering = None
            
        # Relationship types distribution
        rel_types = {}
        for _, _, attr in self.graph.edges(data=True):
            rel_type = attr.get('type', 'unknown')
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        # Build and return the results dictionary
        return {
            "basic_stats": {
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "users_count": len(users),
                "resources_count": len(resources),
                "users_percentage": (len(users)/num_nodes*100) if num_nodes > 0 else 0,
                "resources_percentage": (len(resources)/num_nodes*100) if num_nodes > 0 else 0
            },
            "degree_stats": {
                "avg_degree": avg_degree,
                "max_degree": max_degree,
                "min_degree": min_degree
            },
            "top_users_by_centrality": [
                {"user": user, "centrality": centrality} 
                for user, centrality in top_users_by_degree
            ],
            "top_resources_by_centrality": [
                {"resource": resource, "centrality": centrality} 
                for resource, centrality in top_resources_by_degree
            ],
            "connectivity": {
                "is_directed": nx.is_directed(self.graph),
                "weak_components": num_weak_components,
                "strong_components": num_strong_components,
                "largest_weak_component": largest_weak_component,
                "largest_strong_component": largest_strong_component,
                "giant_component_ratio": giant_ratio
            },
            "disconnected_nodes": {
                "total": len(disconnected_nodes),
                "percentage": (len(disconnected_nodes)/num_nodes*100) if num_nodes > 0 else 0,
                "users_count": len(disconnected_users),
                "resources_count": len(disconnected_resources),
                "sample_users": disconnected_users[:5] if disconnected_users else []
            },
            "isolation": {
                "isolated_nodes_count": len(isolated_nodes),
                "isolated_nodes_percentage": (len(isolated_nodes)/num_nodes*100) if num_nodes > 0 else 0,
                "only_incoming_nodes": num_only_incoming,
                "only_outgoing_nodes": num_only_outgoing
            },
            "clustering": {
                "avg_clustering_coefficient": avg_clustering
            },
            "relationship_types_distribution": rel_types
        }
