#!/bin/bash

echo "Starting AI Tutor MCP Server..."
echo "================================"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo "Building TypeScript..."
    npm run build
fi

echo "Starting server on port 3000..."
echo "Health check will be available at: http://localhost:3000/health"
echo "Tools manifest at: http://localhost:3000/mcp/tools"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start