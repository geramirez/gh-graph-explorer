"""
Bipartite graph collapse transformation.

This module provides functionality to transform bipartite graphs by collapsing
one set of nodes and creating direct connections between the other set.
"""

import csv
import networkx as nx
from typing import Dict, Any
from ..load_strategies import Loader


class BipartiteCollapser:
    """
    Transforms bipartite graphs by collapsing intermediate nodes.
    
    Takes a bipartite graph and creates a new graph with edges transferred row by row.
    """
    
    def __init__(self, load_strategy: Loader):
        """
        Initialize the bipartite collapser with a loader strategy.
        
        Args:
            load_strategy: A concrete implementation of the Loader abstract class
        """
        self.load_strategy = load_strategy
        self.graph = None
        self.transformed_graph = None
        self.headers = ["source", "target", "type", "title", "created_at", "url"]
    
    def create(self) -> "BipartiteCollapser":
        """
        Create a networkx MultiGraph using the configured loader strategy.
        
        Returns:
            Self reference for method chaining
        """
        self.graph = self.load_strategy.create_graph()
        return self
    
    def transform(self) -> "BipartiteCollapser":
        """
        Transform the graph by collapsing the resource nodes
        
        Returns:
            Self reference for method chaining
        """
        if self.graph is None:
            raise ValueError("No graph has been created yet. Call create() first.")
        
        # Create a new empty graph
        self.transformed_graph = nx.Graph()
        
        # Copy edges row by row from the original graph to the new graph
        for source_node, target_node, edge_data in self.graph.edges(data=True):

            resource_node = target_node if target_node.startswith("https://") else source_node
            user_node = source_node if not source_node.startswith("https://") else target_node

            resource_node = resource_node.lower()
            user_node = user_node.lower()

            for neighbor in self.graph.neighbors(resource_node):
                if neighbor != user_node:
                    # Add edge between user_node and neighbor with edge_data
                    self.transformed_graph.add_edge(
                        user_node,
                        neighbor,
                        **edge_data
                    )

        return self
    
    def save_edges(self, output_file: str) -> None:
        """
        Save edges from the transformed graph to a CSV file.
        
        Args:
            output_file: Path to the output CSV file
        """
        if self.transformed_graph is None:
            raise ValueError("No transformed graph exists. Call transform() first.")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()
            
            # Write each edge from the transformed graph
            for source, target, edge_data in self.transformed_graph.edges(data=True):
                row = {
                    "source": source,
                    "target": target,
                    "type": edge_data.get("type", ""),
                    "title": edge_data.get("title", ""),
                    "created_at": edge_data.get("created_at", ""),
                    "url": edge_data.get("url", "")
                }
                writer.writerow(row)
    
    def run(self, output_file: str) -> None:
        """
        Run the full transformation pipeline.
        
        Args:
            output_file: Path to the output CSV file
        """
        print("Loading graph...")
        self.create()
        print(f"Loaded {self.graph.number_of_edges()} edges")
        
        print("Transforming graph...")
        self.transform()
        print(f"Transformed to {self.transformed_graph.number_of_edges()} edges")
        
        print(f"Saving to {output_file}...")
        self.save_edges(output_file)
        print("Done!")
