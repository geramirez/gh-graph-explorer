from abc import ABC, abstractmethod
from ..edge import Edge


class SaveStrategy(ABC):
    """
    Abstract base class for edge saving strategies
    """

    @abstractmethod
    def save(self, edge: Edge) -> None:
        """
        Save an edge using the strategy's implementation

        Args:
            edge: The Edge object to save
        """
        pass

    def finalize(self) -> None:
        """
        Optional method to finalize the saving process (e.g., close files)
        """
        pass
