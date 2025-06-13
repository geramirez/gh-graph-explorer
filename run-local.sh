#!/bin/bash
set -e

# Script to run GitHub Graph Explorer commands in Docker

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ || -z $key ]] && continue
        # Remove quotes and whitespace from the value
        value=$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//g' -e 's/"$//g' -e "s/^'//g" -e "s/'$//g")
        # Export the variable
        export "$key=$value"
        echo "Exported: $key"
    done < .env
fi

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN environment variable is not set."
    echo "Please set it first with: export GITHUB_TOKEN=your_github_token"
    echo "Or add it to your .env file as GITHUB_TOKEN=your_github_token"
    exit 1
fi

# Default command is to run main.py with all arguments passed
docker run --rm -it \
  -v "$PWD":/app \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  gh-graph-explorer-local \
  python main.py "$@"

# Exit with the same status as the docker command
exit $?
