from neo4j import GraphDatabase
from .base import SaveStrategy
from ..edge import Edge


class Neo4jSave(SaveStrategy):
    """
    Strategy that saves edges to a Neo4j database
    """

    def __init__(
        self,
        uri: str = "bolt://neo4j:7687",
        username: str = "neo4j",
        password: str = "password",
    ):
        """
        Initialize Neo4j save strategy with connection details

        Args:
            uri: URI for the Neo4j database
            username: Username for Neo4j authentication
            password: Password for Neo4j authentication
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self._connect()

    def _connect(self):
        """
        Establish connection to Neo4j database
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            raise

    def save(self, edge: Edge) -> None:
        """
        Save an edge to Neo4j database

        Args:
            edge: The Edge object to save
        """
        if not self.driver:
            self._connect()

        with self.driver.session() as session:
            # Create a Cypher query to save the edge
            # This will create or match the source and target nodes and create a relationship between them
            result = session.execute_write(self._create_edge, edge)

    def _create_edge(self, tx, edge: Edge) -> None:
        """
        Create an edge in the Neo4j database using a transaction

        Args:
            tx: Neo4j transaction
            edge: The Edge object to save

        Returns:
            The number of edges created (0 if edge already existed)
        """
        # Create a query using MERGE for both nodes and the relationship
        # This ensures that duplicates are not created
        properties = edge.to_row()
        relationship_type = properties["type"].upper().replace(" ", "_")

        query = (
            "MERGE (source:User {name: $source_name}) "
            "MERGE (target:GitHubObject {url: $target_url}) "
            f"MERGE (source)-[r:{relationship_type} {{url: $url}}]->(target) "
            "ON CREATE SET r.title = $title, "
            "r.created_at = $created_at "
            "RETURN count(r) as edges_count"
        )
        result = tx.run(
            query,
            source_name=edge.source(),
            target_url=edge.target(),
            title=edge.title(),
            created_at=edge.created_at(),
            url=edge.url(),
        )

        summary = result.consume()
        return summary.counters.relationships_created

    def finalize(self) -> None:
        """
        Close the Neo4j connection
        """
        if self.driver:
            self.driver.close()
