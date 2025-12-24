import csv
from typing import Dict, Any, Generator
import os
from .base import Loader


class CSVLoader(Loader):
    """
    Loader implementation that reads relationships from a CSV file.

    This class loads data from a CSV file and converts it into a list of relationship
    dictionaries that can be used to build a networkx MultiGraph.
    """

    def __init__(
        self,
        filepath: str,
        delimiter: str = ",",
        source_col: str = "source",
        target_col: str = "target",
        encoding: str = "utf-8",
    ):
        """
        Initialize the CSVLoader.

        Args:
            filepath: Path to the CSV file
            delimiter: CSV delimiter character
            source_col: Name of the column to use as source node
            target_col: Name of the column to use as target node
            encoding: File encoding
        """
        self.filepath = filepath
        self.delimiter = delimiter
        self.source_col = source_col
        self.target_col = target_col
        self.encoding = encoding

        # Validate the file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV file not found: {filepath}")

    def load_data(self) -> Generator[Dict[str, Any], None, None]:
        """
        Load relationships from the CSV file.

        Returns:
            List of dictionaries, each representing a relationship
        """
        with open(self.filepath, "r", newline="", encoding=self.encoding) as csvfile:
            # Use DictReader to automatically use column headers
            reader = csv.DictReader(csvfile, delimiter=self.delimiter)

            # Check if required columns exist
            if (
                self.source_col not in reader.fieldnames
                or self.target_col not in reader.fieldnames
            ):
                missing = []
                if self.source_col not in reader.fieldnames:
                    missing.append(self.source_col)
                if self.target_col not in reader.fieldnames:
                    missing.append(self.target_col)
                raise ValueError(
                    f"CSV file missing required columns: {', '.join(missing)}"
                )

            # Process each row
            for row in reader:
                # Skip rows where source or target is empty
                if not row[self.source_col] or not row[self.target_col]:
                    continue
                yield row
        