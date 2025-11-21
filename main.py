import os
import asyncio
import argparse
from typing import List, Dict
import json
from src.collector import Collector
from src.save_strategies import PrintSave, CSVSave, Neo4jSave
from src.graph_analyzer import GraphAnalyzer
from src.load_strategies import CSVLoader, Neo4jLoader


def parse_arguments():
    """
    Parse command line arguments for the GitHub graph explorer
    """
    parser = argparse.ArgumentParser(description="GitHub Work Graph Explorer")

    # Add mode subcommands
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")

    # Collection mode parser
    collect_parser = subparsers.add_parser("collect", help="Collect GitHub data")
    collect_parser.add_argument(
        "--since-iso",
        type=str,
        help="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    collect_parser.add_argument(
        "--until-iso",
        type=str,
        help="End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    collect_parser.add_argument(
        "--repos",
        type=str,
        required=True,
        help="JSON string or file path with repositories information",
    )
    collect_parser.add_argument(
        "--output",
        type=str,
        choices=["print", "csv", "neo4j"],
        default="print",
        help="Output strategy (print, csv, neo4j). Default: print",
    )
    collect_parser.add_argument(
        "--output-file", type=str, help="Output file path for CSV strategy"
    )
    collect_parser.add_argument(
        "--neo4j-uri",
        type=str,
        default="bolt://localhost:7687",
        help="Neo4j URI (default: bolt://neo4j:7687)",
    )
    collect_parser.add_argument(
        "--neo4j-user",
        type=str,
        default="neo4j",
        help="Neo4j username (default: neo4j)",
    )
    collect_parser.add_argument(
        "--neo4j-password",
        type=str,
        default=os.environ.get("NEO4J_PASSWORD", "password"),
        help='Neo4j password (default from NEO4J_PASSWORD env var, or "password")',
    )

    # Analysis mode parser
    analyze_parser = subparsers.add_parser("analyze", help="Analyze GitHub data graph")
    analyze_parser.add_argument(
        "--source",
        type=str,
        choices=["csv", "neo4j"],
        required=True,
        help="Data source for analysis (csv or neo4j)",
    )
    analyze_parser.add_argument(
        "--file", type=str, help="CSV file path for analysis when source is csv"
    )
    analyze_parser.add_argument(
        "--neo4j-uri",
        type=str,
        default="bolt://localhost:7687",
        help="Neo4j URI (default: bolt://neo4j:7687)",
    )
    analyze_parser.add_argument(
        "--neo4j-user",
        type=str,
        default="neo4j",
        help="Neo4j username (default: neo4j)",
    )
    analyze_parser.add_argument(
        "--neo4j-password",
        type=str,
        default=os.environ.get("NEO4J_PASSWORD", "password"),
        help='Neo4j password (default from NEO4J_PASSWORD env var, or "password")',
    )
    analyze_parser.add_argument(
        "--neo4j-query", type=str, help="Custom Neo4j query for analysis"
    )

    # Get edges mode parser
    edges_parser = subparsers.add_parser(
        "get-edges", help="Get edges from GitHub data graph"
    )
    edges_parser.add_argument(
        "--source",
        type=str,
        choices=["csv", "neo4j"],
        required=True,
        help="Data source for getting edges (csv or neo4j)",
    )
    edges_parser.add_argument(
        "--file", type=str, help="CSV file path when source is csv"
    )
    edges_parser.add_argument(
        "--neo4j-uri",
        type=str,
        default="bolt://localhost:7687",
        help="Neo4j URI (default: bolt://neo4j:7687)",
    )
    edges_parser.add_argument(
        "--neo4j-user",
        type=str,
        default="neo4j",
        help="Neo4j username (default: neo4j)",
    )
    edges_parser.add_argument(
        "--neo4j-password",
        type=str,
        default=os.environ.get("NEO4J_PASSWORD", "password"),
        help='Neo4j password (default from NEO4J_PASSWORD env var, or "password")',
    )
    edges_parser.add_argument(
        "--neo4j-query", type=str, help="Custom Neo4j query for filtering edges"
    )
    edges_parser.add_argument(
        "--output",
        type=str,
        choices=["print", "csv", "json"],
        default="print",
        help="Output format (print, csv, json). Default: print",
    )
    edges_parser.add_argument(
        "--output-file", type=str, help="Output file path for CSV or JSON output"
    )

    return parser.parse_args()


def parse_repos_config(repos_config: str) -> List[Dict[str, str]]:
    """
    Parse the organizations configuration from JSON string or file

    Args:
        repos_config: JSON string or path to JSON file with organizations information

    Returns:
        List of organization configurations with username and org keys
    """
    repos = []

    # Check if the input is a file path
    if os.path.isfile(repos_config):
        with open(repos_config, "r") as f:
            repos = json.load(f)
    else:
        # Try to parse as a JSON string
        try:
            repos = json.loads(repos_config)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format: {repos_config}")

    # Validate the format
    if not isinstance(repos, list):
        raise ValueError("Organizations configuration must be a list")

    for repo in repos:
        if not all(k in repo for k in ["username", "org"]):
            raise ValueError(
                f"Each entry must have username and org keys: {repo}"
            )

    return repos


async def collect_data(args):
    """
    Function for collecting GitHub data
    """
    # Parse repositories configuration
    repos = parse_repos_config(args.repos)

    # Create save strategy based on arguments
    if args.output == "csv":
        save_strategy = CSVSave(filename=args.output_file)
    elif args.output == "neo4j":
        save_strategy = Neo4jSave(
            uri=args.neo4j_uri, username=args.neo4j_user, password=args.neo4j_password
        )
    else:  # default to print
        save_strategy = PrintSave()

    # Create collector with the chosen save strategy
    collector = Collector(
        since_iso=getattr(args, "since_iso", None),
        until_iso=getattr(args, "until_iso", None),
        save_strategy=save_strategy,
    )

    # Collect data
    results = await collector.get(repos)

    print(f"Processed {len(results)} repositories")

    # Print any errors
    errors = {repo: data["error"] for repo, data in results.items() if "error" in data}
    if errors:
        print(f"Encountered errors in {len(errors)} repositories:")
        for repo, error in errors.items():
            print(f"  {repo}: {error}")


def analyze_data(args):
    """
    Function for analyzing GitHub data graph
    """
    # Create loader based on source
    if args.source == "csv":
        if not args.file:
            raise ValueError("--file must be specified when source is csv")
        loader = CSVLoader(filepath=args.file)
    else:  # neo4j
        loader = Neo4jLoader(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password,
            query=args.neo4j_query,
        )

    # Create and run analyzer
    analyzer = GraphAnalyzer(load_strategy=loader)
    print(analyzer.create().analyze())


def get_edges(args):
    """
    Function for retrieving edges from the GitHub data graph
    """
    # Create loader based on source
    if args.source == "csv":
        if not args.file:
            raise ValueError("--file must be specified when source is csv")
        loader = CSVLoader(filepath=args.file)
    else:  # neo4j
        loader = Neo4jLoader(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password,
            query=args.neo4j_query,
        )

    # Create analyzer and get edges
    analyzer = GraphAnalyzer(load_strategy=loader)
    analyzer.create()
    edges = analyzer.get_edges()

    # Output edges based on the chosen format
    if args.output == "csv":
        if not args.output_file:
            raise ValueError("--output-file must be specified for CSV output")
        import csv

        with open(args.output_file, "w", newline="") as f:
            # Extract headers from the first edge
            if edges:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "source_name",
                        "source_attrs",
                        "target_name",
                        "target_attrs",
                        "type",
                        "properties",
                    ],
                )
                writer.writeheader()
                for edge in edges:
                    writer.writerow(
                        {
                            "source_name": edge["source"].get("name", ""),
                            "source_attrs": json.dumps(edge["source"]),
                            "target_name": edge["target"].get("name", ""),
                            "target_attrs": json.dumps(edge["target"]),
                            "type": edge.get("type", ""),
                            "properties": json.dumps(edge.get("properties", {})),
                        }
                    )
    elif args.output == "json":
        if not args.output_file:
            raise ValueError("--output-file must be specified for JSON output")
        with open(args.output_file, "w") as f:
            json.dump(edges, f, default=str)
    else:  # default to print
        for edge in edges:
            print(f"Source: {edge['source'].get('name')}")
            print(f"Target: {edge['target'].get('name')}")
            print(f"Type: {edge.get('type')}")
            print(f"Properties: {edge.get('properties')}")
            print("---")


async def main():
    """
    Main function for the GitHub graph explorer
    """
    args = parse_arguments()

    if args.mode == "collect":
        await collect_data(args)
    elif args.mode == "analyze":
        analyze_data(args)
    elif args.mode == "get-edges":
        get_edges(args)
    else:
        print("No mode specified. Use 'collect', 'analyze', or 'get-edges'")
        return 1

    return 0


if __name__ == "__main__":
    asyncio.run(main())
