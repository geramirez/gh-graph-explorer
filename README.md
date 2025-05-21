# Graph explorer 

## Usage

### Get Data
1. pip install -r requirements.txt
1. Collect the data
    1. generate a github token with read permissions for repos + and set it in the GH_TOKEN env variable
    1. edit + run `build_graph.py`

### explore data
1. jupyter lab
1. load the csv file that was downloaded before


### Collecting Data (Same as Before)
```
# Print output
uv run main.py collect --repos data/repos.json --days 30 --output print

# CSV output
uv run main.py collect --repos data/repos.json --days 30 --output csv --output-file github_data.csv

# Neo4j output
uv run main.py collect --repos data/repos.json --days 30 --output neo4j --neo4j-uri bolt://localhost:7687
```

### Analyzing Data (New Functionality)
```
# Analyze from CSV file
uv run main.py analyze --source csv --file github_data.csv

# Analyze from Neo4j
uv run main.py analyze --source neo4j --neo4j-uri bolt://localhost:7687
```

The analyzer will use the appropriate loader (CSVLoader or Neo4jLoader) to load the data, create a networkx MultiGraph, and then use the GraphAnalyzer's analyze method to display information about the graph, such as the number of nodes and edges.

If you want to customize the Neo4j query for analysis, you can also use the --neo4j-query parameter:
```
uv run main.py analyze --source neo4j --neo4j-query "MATCH (source)-[rel]->(target)  WHERE rel.created_at > \"2025-04-01\" RETURN source.name AS source, target.url AS target, type(rel) AS type, properties(rel) AS properties" --neo4j-uri bolt://localhost:7687
```

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
          repos_file: 'repos.json'
          days: '1'
          output_file: 'github_data.csv'
          commit_message: 'Update GitHub repository data [Skip CI]'
```

#### Creating a repos.json file

Create a `repos.json` file in the root of your repository with the following structure:

```json
[
  {
    "username": "dependabot",
    "owner": "octocat",
    "repo": "Hello-World"
  },
  {
    "username": "user1",
    "owner": "organization1",
    "repo": "repo-name-1"
  },
  {
    "username": "user2",
    "owner": "organization2",
    "repo": "repo-name-2"
  }
]
```

#### Action Inputs

The GitHub Action accepts the following inputs:

- `github_token`: GitHub token with read access to repos (required)
- `repos_file`: Path to the JSON file containing repository information (default: `repos.json`)
- `days`: Number of days to look back (default: `1`)
- `output_file`: Output file path for CSV (default: `github_data.csv`)
- `commit_message`: Commit message for the CSV file update (default: `Update GitHub repository data`)

### Setup with Claude Desktop
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

Create a user Projection with relationship type filtering
```neo4j
MATCH (u1:User)-[r1:PR_REVIEW_APPROVED|PR_REVIEW_COMMENTED]->(g:GitHubObject)<-[r2]-(u2:User)
WHERE u1.name <> u2.name
WITH u1, u2, collect(g.name) as gitobjects, count(g) as weight
MERGE (u1)-[r:COLLABORATED]->(u2)
SET r.projects = gitobjects, r.weight = weight
```

Create a user Projection with date filtering
```neo4j
MATCH (u1:User)-[r1]->(g:GitHubObject)<-[r2]-(u2:User)
WHERE u1.name <> u2.name 
  AND r1.created_at > "2023-01-01" AND r2.created_at > "2023-01-01"
WITH u1, u2, collect(g.name) as gitobjects, count(g) as weight
MERGE (u1)-[r:CONNECTED_RECENT]->(u2)
SET r.projects = gitobjects, r.weight = weight
```

Create a focused projection for specific users
```neo4j
MATCH (u1:User)-[r1]->(g:GitHubObject)<-[r2]-(u2:User)
WHERE u1.name IN ["user1", "user2", "user3"] 
  AND u2.name IN ["user1", "user2", "user3"]
  AND u1.name <> u2.name
WITH u1, u2, collect(g.name) as gitobjects, count(g) as weight
MERGE (u1)-[r:TEAM_COLLABORATION]->(u2)
SET r.projects = gitobjects, r.weight = weight
```

View the user projection
```neo4j
MATCH p = (u1:User)-[]-(u2:User) Return p limit 200
```