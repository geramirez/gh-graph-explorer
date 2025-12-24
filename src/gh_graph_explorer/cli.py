import os
import asyncio
import argparse
import json
from typing import List, Dict

from .api import collect, analyze, get_edges, bipartite_collapse


def parse_arguments():
    parser = argparse.ArgumentParser(description="GitHub Work Graph Explorer")
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")

    # collect
    collect_parser = subparsers.add_parser("collect", help="Collect GitHub data")
    collect_parser.add_argument("--since-iso", type=str)
    collect_parser.add_argument("--until-iso", type=str)
    collect_parser.add_argument("--orgs", type=str, required=True,
                                help="JSON string or file path with organizations information")
    collect_parser.add_argument("--output", type=str, choices=["print", "csv", "neo4j"], default="print")
    collect_parser.add_argument("--output-file", type=str)
    collect_parser.add_argument("--neo4j-uri", type=str, default="bolt://localhost:7687")
    collect_parser.add_argument("--neo4j-user", type=str, default="neo4j")
    collect_parser.add_argument("--neo4j-password", type=str, default=os.environ.get("NEO4J_PASSWORD", "password"))

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze GitHub data graph")
    analyze_parser.add_argument("--source", type=str, choices=["csv", "neo4j"], required=True)
    analyze_parser.add_argument("--file", type=str)
    analyze_parser.add_argument("--neo4j-uri", type=str, default="bolt://localhost:7687")
    analyze_parser.add_argument("--neo4j-user", type=str, default="neo4j")
    analyze_parser.add_argument("--neo4j-password", type=str, default=os.environ.get("NEO4J_PASSWORD", "password"))
    analyze_parser.add_argument("--neo4j-query", type=str)

    # get-edges
    edges_parser = subparsers.add_parser("get-edges", help="Get edges from the graph")
    edges_parser.add_argument("--source", type=str, choices=["csv", "neo4j"], required=True)
    edges_parser.add_argument("--file", type=str)
    edges_parser.add_argument("--neo4j-uri", type=str, default="bolt://localhost:7687")
    edges_parser.add_argument("--neo4j-user", type=str, default="neo4j")
    edges_parser.add_argument("--neo4j-password", type=str, default=os.environ.get("NEO4J_PASSWORD", "password"))
    edges_parser.add_argument("--neo4j-query", type=str)
    edges_parser.add_argument("--output", type=str, choices=["print", "csv", "json"], default="print")
    edges_parser.add_argument("--output-file", type=str)

    # transform bipartite collapse
    transform_parser = subparsers.add_parser("transform", help="Transform GitHub data graph")
    transform_subparsers = transform_parser.add_subparsers(dest="transform_type")
    bipartite_parser = transform_subparsers.add_parser("bipartite_collapse", help="Collapse bipartite graph")
    bipartite_parser.add_argument("--source", type=str, choices=["csv"], required=True)
    bipartite_parser.add_argument("--file", type=str, required=True)
    bipartite_parser.add_argument("--output-file", type=str, required=True)

    return parser.parse_args()


def parse_orgs_config(orgs_config: str) -> List[Dict[str, str]]:
    if os.path.isfile(orgs_config):
        with open(orgs_config, "r") as f:
            return json.load(f)
    try:
        return json.loads(orgs_config)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format: {orgs_config}")


async def main_async():
    args = parse_arguments()

    if args.mode == "collect":
        orgs = parse_orgs_config(args.orgs)
        result = await collect(
            orgs,
            since_iso=getattr(args, "since_iso", None),
            until_iso=getattr(args, "until_iso", None),
            output=args.output,
            output_file=args.output_file,
            neo4j_uri=args.neo4j_uri,
            neo4j_user=args.neo4j_user,
            neo4j_password=args.neo4j_password,
        )
        print(f"Processed {len(result)} organization(s)")
        
        # Print any errors
        errors = {org: data["error"] for org, data in result.items() if "error" in data}
        if errors:
            print(f"Encountered errors in {len(errors)} organization(s):")
            for org, error in errors.items():
                print(f"  {org}: {error}")

    elif args.mode == "analyze":
        result = analyze(
            source=args.source,
            file=args.file,
            neo4j_uri=args.neo4j_uri,
            neo4j_user=args.neo4j_user,
            neo4j_password=args.neo4j_password,
            neo4j_query=args.neo4j_query,
        )
        print(json.dumps(result, indent=2))

    elif args.mode == "get-edges":
        edges = get_edges(
            source=args.source,
            file=args.file,
            neo4j_uri=args.neo4j_uri,
            neo4j_user=args.neo4j_user,
            neo4j_password=args.neo4j_password,
            neo4j_query=args.neo4j_query,
        )
        if args.output == "csv":
            if not args.output_file:
                raise ValueError("--output-file must be specified for CSV output")
            import csv
            with open(args.output_file, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["source_name", "source_attrs", "target_name", "target_attrs", "type", "properties"],
                )
                writer.writeheader()
                for edge in edges:
                    writer.writerow({
                        "source_name": edge["source"].get("name", ""),
                        "source_attrs": json.dumps(edge["source"]),
                        "target_name": edge["target"].get("name", ""),
                        "target_attrs": json.dumps(edge["target"]),
                        "type": edge.get("type", ""),
                        "properties": json.dumps(edge.get("properties", {})),
                    })
        elif args.output == "json":
            if not args.output_file:
                raise ValueError("--output-file must be specified for JSON output")
            with open(args.output_file, "w") as f:
                json.dump(edges, f, default=str)
        else:
            for edge in edges:
                print(f"Source: {edge['source'].get('name')}")
                print(f"Target: {edge['target'].get('name')}")
                print(f"Type: {edge.get('type')}")
                print(f"Properties: {edge.get('properties')}")
                print("---")

    elif args.mode == "transform" and args.transform_type == "bipartite_collapse":
        bipartite_collapse(source=args.source, file=args.file, output_file=args.output_file)
    else:
        print("No mode specified. Use 'collect', 'analyze', 'get-edges', or 'transform bipartite_collapse'")
        return 1

    return 0


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
