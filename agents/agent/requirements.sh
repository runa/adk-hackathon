#!/bin/sh
set -e

# Install Node.js, npm, and npx
apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# npx is included with npm (which comes with nodejs)

# Install @modelcontextprotocol/server-google-maps and its dependencies globally
npm install -g @modelcontextprotocol/server-google-maps

curl -LsSf https://astral.sh/uv/install.sh | sh
