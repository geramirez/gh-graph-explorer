from abc import ABC, abstractmethod
import networkx as nx
from typing import Dict, Any, Generator

class Loader(ABC):
    """
    Abstract base class for loading data into a networkx MultiGraph.

    This class defines the interface that all loader implementations must follow.
    Subclasses should implement the load_data method to retrieve and format data
    from various sources.
    """

    @abstractmethod
    def load_data(self) -> Generator[Dict[str, Any], None, None]:
        """
        Load data from the source and return it as a list of relationship dictionaries.

        Returns:
            List of dictionaries, each representing a relationship
        """
        pass

    def get_bipartite(self, node: str) -> int:
        """
        Determine the bipartite group of a node.

        Args:
            node: Node identifier

        Returns:
            Integer representing the bipartite group
        """
        return 0 if node.startswith("https://") else 1

    def create_graph(self) -> nx.MultiGraph:
        """
        Creates a networkx MultiGraph from the loaded data.

        Returns:
            A networkx MultiGraph containing the relationships
        """
        G = nx.MultiGraph()

        # Add each relationship to the graph
        for rel in self.load_data():
            source = rel.get("source")
            target = rel.get("target")

            # Skip if source or target is missing
            if not source or not target:
                continue

            # Create edge with all attributes from the relationship
            G.add_node(source, bipartite=self.get_bipartite(source))
            G.add_node(target, bipartite=self.get_bipartite(target))
            G.add_edge(
                source,
                target,
                **{k: v for k, v in rel.items() if k not in ("source", "target")},
            )

        return G
