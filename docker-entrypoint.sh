#!/bin/bash
set -e

# Check if the GITHUB_TOKEN environment variable is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "WARNING: GITHUB_TOKEN environment variable is not set. GitHub API rate limits may apply."
    echo "Consider running with: docker run -e GITHUB_TOKEN=your_token ..."
fi

# Run the command passed to the entrypoint
exec "$@"
