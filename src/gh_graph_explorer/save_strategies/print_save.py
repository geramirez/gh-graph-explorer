from .base import SaveStrategy
from ..edge import Edge


class PrintSave(SaveStrategy):
    """
    Strategy that saves edges by printing them to the console
    """

    def save(self, edge: Edge) -> None:
        """
        Save an edge by printing it to the console

        Args:
            edge: The Edge object to print
        """
        print(edge)
