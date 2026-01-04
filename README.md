# GitHub Graph Explorer

A tool for collecting and analyzing GitHub collaboration data using Social Network Analysis. This project helps visualize and understand team dynamics through GitHub activity.

For background on the theory and application of Social Network Analysis to engineering teams, see [Theory.md](Theory.md).

## Table of Contents

| Section | Description |
|---------|-------------|
| [Dependencies](#dependencies) | Required tools and libraries |
| [Installation](#installation) | Setup instructions |
| [Collecting Data](#collecting-data) | Data collection commands |
| [Analyzing Data](#analyzing-data) | Data analysis commands |
| [Using the GitHub Action](#using-the-github-action) | Automating data collection |
| [Setup with Claude Desktop](#setup-with-claude-desktop) | Example configuration |
| [Useful Queries](#useful-queries) | Example Neo4j queries |

## Usage

### Dependencies
- [uv](https://github.com/astral-sh/uv) - for packaging and running the project
- [GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) - with Discussions, Issues, Pull requests scopes for accessing data.
- [docker](https://www.docker.com/) - for running the Neo4j database (optional, but recommended for Neo4j output)

### Installation

#### As a Python Library

Install the package from your repository or local directory:

```bash
pip install gh-graph-explorer
# or for editable install from local clone:
pip install -e .
# or with uv:
uv pip install -e .
```

Then import and use the API in your Python code:

```python
from gh_graph_explorer import collect, analyze, get_edges, bipartite_collapse, __version__

# Example: collect data programmatically
import asyncio

orgs = [{"username": "octocat", "org": "github"}]
result = asyncio.run(collect(
    orgs,
    since_iso="2025-01-01",
    until_iso="2025-01-15",
    output="csv",
    output_file="data.csv"
))
print(result)

# Example: analyze data
analysis = analyze(source="csv", file="data.csv")
print(analysis)

# Example: retrieve edges
edges = get_edges(source="csv", file="data.csv")
for edge in edges:
    print(edge)
```

#### Using the CLI

The package includes a command-line interface. After installation, the `gh-graph-explorer` command will be available:

```bash
gh-graph-explorer --help
```

1. Set up your GitHub Personal Access Token
    - Create a `.env` file in the root directory of the project.
    - Add your GitHub token to the `.env` file:
      ```
      GITHUB_TOKEN=your_github_token_here
      ```

#### For Docker Setup 
In case you don't have uv installed or prefer to run the project in a container (note: currently doesn't work with neo4j or jupyter):
1. `docker build -f Dockerfile.local -t gh-graph-explorer-local .`
2. `chmod +x ./run-local.sh` 
3. Run all the following commands with `./run-local.sh`, for example: `./run-local.sh collect ...`


### Collecting Data

Use the CLI or library to collect GitHub data:

```bash
# Print output (default: last 1 day)
gh-graph-explorer collect --orgs data/orgs.json --output print

# CSV output
gh-graph-explorer collect --orgs data/orgs.json --output csv --output-file github_data.csv

# Neo4j output
gh-graph-explorer collect --orgs data/orgs.json --output neo4j --neo4j-uri bolt://localhost:7687

# Using specific date ranges (recommended for precise control)
gh-graph-explorer collect --orgs data/orgs.json --since-iso 2025-05-01 --until-iso 2025-05-20 --output csv --output-file github_data.csv

# Using full ISO datetime format
gh-graph-explorer collect --orgs data/orgs.json --since-iso 2025-05-01T00:00:00 --until-iso 2025-05-20T23:59:59 --output neo4j
```

**Note**: The CLI uses `--since-iso` and `--until-iso` to specify the date range for data collection. Both parameters accept either `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS` formats. If not provided, the default is the last day.

### Analyzing Data

```bash
# Analyze from CSV file
gh-graph-explorer analyze --source csv --file github_data.csv

# Analyze from Neo4j
gh-graph-explorer analyze --source neo4j --neo4j-uri bolt://localhost:7687
```

The analyzer will use the appropriate loader (CSVLoader or Neo4jLoader) to load the data, create a networkx MultiGraph, and then use the GraphAnalyzer's analyze method to display information about the graph, such as the number of nodes and edges.

If you want to customize the Neo4j query for analysis, you can also use the `--neo4j-query` parameter:

```bash
gh-graph-explorer analyze --source neo4j --neo4j-query "MATCH (source)-[rel]->(target) WHERE rel.created_at > \"2025-04-01\" RETURN source.name AS source, target.url AS target, type(rel) AS type, properties(rel) AS properties" --neo4j-uri bolt://localhost:7687
```

### Retrieving Edges

```bash
# Get edges from CSV
gh-graph-explorer get-edges --source csv --file github_data.csv --output print

# Save edges to neo4j
gh-graph-explorer get-edges --source csv --file github_data.csv --output neo4j --neo4j-uri bolt://localhost:7687

```

### Transforming Data

#### Bipartite Graph Collapse

```bash
# Collapse bipartite graph from CSV
gh-graph-explorer transform bipartite_collapse --source csv --file github_data.csv --output-file collapsed.csv
```

Or use the library API:

```python
from gh_graph_explorer import bipartite_collapse

bipartite_collapse(source="csv", file="github_data.csv", output_file="collapsed.csv")
```

### Analyzing Data with Jupyter Lab + CSVs

```bash
uv run jupyter lab
```

There is a template notebook available at `notebooks/graph-explorer-template.ipynb` that you can use to explore the data interactively.


### Using the GitHub Action

You can use this tool as a GitHub Action in your own repositories. This will automatically collect GitHub repository data and commit the results to your repository.

#### Setting up the Action

Create a `.github/workflows/collect-github-data.yml` file in your repository with the following content:

```yaml
name: Collect GitHub Graph Data

on:
  # Run daily at midnight
  schedule:
    - cron: '0 0 * * *'
  
  # Allow manual trigger
  workflow_dispatch:

jobs:
  collect-data:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Run GitHub Graph Data Collector
        uses: yourusername/gh-graph-explore@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          orgs_file: 'orgs.json'
          output_file: 'github_data.csv'
          commit_message: 'Update GitHub organization data [Skip CI]'
```

#### Creating an orgs.json file

Create an `orgs.json` file in the root of your repository with the following structure:

```json
[
  {
    "username": "dependabot",
    "org": "octocat"
  },
  {
    "username": "user1",
    "org": "organization1"
  },
  {
    "username": "user2",
    "org": "organization2"
  }
]
```

#### Action Inputs

The GitHub Action accepts the following inputs:

- `github_token`: GitHub token with read access to orgs (required)
- `orgs_file`: Path to the JSON file containing organization information (default: `orgs.json`)
- `since_iso`: Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) (optional)
- `until_iso`: End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) (optional)
- `output_file`: Output file path for CSV (default: `github_data.csv`)
- `commit_message`: Commit message for the CSV file update (default: `Update GitHub repository data`)

> **Note:** For CLI usage, use `--since-iso` and `--until-iso` as shown above. The `days` parameter is only relevant for the GitHub Action workflow.

### Setup with Claude Desktop
```json
{
    "mcpServers": {
        "gh-graph-explorer": {
            "command": "uv",
            "args": [
                "--directory",
                "path to directory",
                "run",
                "mcp_server.py"
            ],
            "env": {
                "GITHUB_TOKEN": "*****",
                "NEO4J_PASSWORD": "password",
                "NEO4J_USERNAME": "neo4j",
                "NEO4J_URI": "bolt://localhost:7687"
            }
        }
      }
}
```

### Useful queries 
Filter by date
```neo4j
MATCH (source)-[rel:PR_REVIEW_APPROVED]->(target)  WHERE rel.created_at > "2025-04-15" RETURN * limit 100
```

Create a user Projection 
```neo4j

MATCH (u1:User)-[] -> (g:GitHubObject) <- []-(u2:User)
WHERE u1.name < u2.name
WITH u1, u2, collect(g.name) as gitobjects, count(g) as weight
MERGE (u1)-[r:CONNECTED]->(u2)
SET r.name = gitobjects, r.weight = weight
```

View the user projection
```neo4j
MATCH p = (u1:User)-[]-(u2:User) Return p limit 200
```

### Bipartite Graph Collapse Transformation

The `BipartiteCollapser` class in [`src/transformations/bipartite_collapser.py`](src/transformations/bipartite_collapser.py) provides functionality to transform bipartite graphs by collapsing one set of nodes and creating direct connections between the other set.

#### Usage

1. **Initialize with a Loader strategy**  
   The collapser requires a loader implementing the `Loader` abstract class (see [`src/load_strategies/base.py`](src/load_strategies/base.py)).

   ```python
   from src.transformations.bipartite_collapser import BipartiteCollapser
   from src.load_strategies.csv_loader import CSVLoader

   loader = CSVLoader('path/to/input.csv')
   collapser = BipartiteCollapser(loader)
   ```

2. **Run the transformation pipeline**  
   Use the `run` method to load, transform, and save the collapsed graph edges to a CSV file.

   ```python
   collapser.run('path/to/output.csv')
   ```

   This will:
   - Load the bipartite graph using the loader
   - Collapse resource nodes, connecting users directly
   - Save the resulting edges to the specified CSV file

#### Command-Line Example

You can also use the transformation in a script:

```python
from src.transformations.bipartite_collapser import BipartiteCollapser
from src.load_strategies.csv_loader import CSVLoader

if __name__ == "__main__":
    loader = CSVLoader("github_bipartite_collapse.csv")
    collapser = BipartiteCollapser(loader)
    collapser.run("collapsed_edges.csv")
```

#### Output Format

The output CSV will contain the following columns:

- `source`: Source node (user)
- `target`: Target node (user)
- `type`: Edge type
- `title`: Resource title
- `created_at`: Creation date
- `url`: Resource URL

#### Notes

- Ensure your loader is compatible with the expected graph format.
- The transformation assumes resource nodes are identified by URLs (starting with `https://`).

For more details, see the source code in [`src/transformations/bipartite_collapser.py`](src/transformations/bipartite_collapser.py).