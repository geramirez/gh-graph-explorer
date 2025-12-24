from typing import Dict, Optional
from datetime import datetime


class Edge:
    """
    Class representing an edge in the GitHub work graph.
    """

    def __init__(
        self,
        edge_type: Optional[str] = None,
        title: Optional[str] = None,
        created_at: Optional[str] = None,
        login: Optional[str] = None,
        url: Optional[str] = None,
        parent_url: Optional[str] = None,
    ):
        """
        Initialize an Edge with the given properties.

        Args:
            edge_type: Type of the edge (e.g., issue_created, pr_created)
            title: Title of the related GitHub object
            created_at: Creation timestamp
            login: User login associated with the edge
            url: URL of the GitHub object
            parent_url: URL of the parent object (for comments this is the issue/discussion URL)
        """
        self._type = edge_type
        self._title = title
        self._created_at = created_at
        self._login = login
        self._url = url
        self._parent_url = parent_url

    def source(self) -> str:
        """
        Return the source of the edge, which is the login of the user who created it.
        """
        return self._login

    def target(self) -> str:
        """
        Return the target of the edge, which is the URL of the GitHub object.
        """
        if self._parent_url:
            return self._parent_url
        return self._url

    def type(self) -> str:
        """
        Return the type of the edge.
        """
        return self._type

    def created_at(self) -> Optional[datetime]:
        """
        Return the creation date of the edge.
        """
        return self._created_at

    def url(self) -> Optional[str]:
        """
        Return the URL of the edge.
        """
        return self._url

    def title(self) -> Optional[str]:
        """
        Return the title of the edge.
        """
        return self._title

    def to_row(self) -> Dict[str, Optional[str]]:
        """
        Return a row representation of the edge data.

        Returns:
            Dictionary containing the edge data in row format
        """
        return {
            "source": self.source(),
            "target": self.target(),
            "type": self.type(),
            "title": self.title(),
            "created_at": self.created_at(),
            "url": self.url(),
        }

    def __str__(self) -> str:
        """
        Return a string representation of the edge.

        Returns:
            String representation of the edge
        """
        return f"Edge(type={self._type}, title={self._title}, created_at={self._created_at}, login={self._login}, url={self._url}, parent_url={self._parent_url})"
