from typing import Dict, Any, Generator
from neo4j import GraphDatabase
from .base import Loader


class Neo4jLoader(Loader):
    """
    Loader implementation that reads relationships from a Neo4j database.

    This class executes a Cypher query in Neo4j and converts the results
    into a list of relationship dictionaries that can be used to build
    a networkx MultiGraph.
    """

    def __init__(
        self,
        uri: str = "bolt://neo4j:7687",
        username: str = "neo4j",
        password: str = "password",
        query: str = None,
        params: Dict[str, Any] = None,
    ):
        """
        Initialize the Neo4jLoader.

        Args:
            uri: URI for the Neo4j database connection
            username: Username for Neo4j authentication
            password: Password for Neo4j authentication
            query: Custom Cypher query to execute. If None, a default query that fetches
                  all relationships will be used.
            params: Parameters to use with the query
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.query = query or self._default_query()
        self.params = params or {}
        self.driver = None

    def _default_query(self) -> str:
        """
        Returns the default Cypher query to retrieve relationships.

        Returns:
            A Cypher query string
        """
        return """
        MATCH (source)-[rel]->(target)
        RETURN source.name AS source, target.url AS target, 
               type(rel) AS type, properties(rel) AS properties
        """

    def _connect(self):
        """
        Establish connection to Neo4j database.
        """
        if not self.driver:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri, auth=(self.username, self.password)
                )
            except Exception as e:
                raise ConnectionError(f"Error connecting to Neo4j: {e}")

    def _close(self):
        """
        Close the Neo4j connection.
        """
        if self.driver:
            self.driver.close()
            self.driver = None

    def load_data(self) -> Generator[Dict[str, Any], None, None]:
        """
        Execute query and load relationships from Neo4j.

        Returns:
            List of dictionaries, each representing a relationship
        """
        try:
            self._connect()

            with self.driver.session() as session:
                # Execute the query
                result = session.run(self.query, self.params)

                # Process each record
                for record in result:
                    # Extract basic relationship data
                    rel = {
                        "source": record.get("source"),
                        "target": record.get("target"),
                        "type": record.get("type"),
                    }

                    # Add properties from the relationship
                    properties = record.get("properties", {})
                    if properties:
                        for key, value in properties.items():
                            rel[key] = value

                    yield rel


        finally:
            self._close()
