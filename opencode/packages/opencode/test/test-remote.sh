#!/bin/bash
# OpenCode Remote API Test Script
# This script helps test the remote API functionality

set -e

# Configuration
SERVER_URL="${OPENCODE_REMOTE_URL:-http://localhost:4096}"
USERNAME="${OPENCODE_REMOTE_USERNAME:-opencode}"
PASSWORD="${OPENCODE_REMOTE_PASSWORD:-}"

echo "======================================"
echo "OpenCode Remote API Test Script"
echo "======================================"
echo "Server URL: $SERVER_URL"
echo "Username: $USERNAME"
echo "Password: ${PASSWORD:+***set***}"
echo ""

# Function to make API requests
api_request() {
  local endpoint="$1"
  local method="${2:-GET}"
  local data="$3"

  local curl_args=(-X "$method" "$SERVER_URL$endpoint" -H "Content-Type: application/json")

  if [ -n "$PASSWORD" ]; then
    curl_args+=(-u "$USERNAME:$PASSWORD")
  fi

  if [ -n "$data" ]; then
    curl_args+=(-d "$data")
  fi

  curl -s "${curl_args[@]}"
}

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
result=$(api_request "/remote/health")
echo "$result" | jq '.' 2>/dev/null || echo "$result"
echo ""

# Test 2: List Commands
echo "Test 2: List Available Commands"
echo "--------------------------------"
result=$(api_request "/remote/commands")
echo "$result" | jq '.data[] | {name, description}' 2>/dev/null || echo "$result"
echo ""

# Test 3: Get Status
echo "Test 3: Get Status (All Sessions)"
echo "---------------------------------"
result=$(api_request "/remote/execute" "POST" '{"type":"status"}')
echo "$result" | jq '.' 2>/dev/null || echo "$result"
echo ""

# Test 4: Send a Simple Prompt
echo "Test 4: Send Simple Prompt"
echo "-------------------------"
result=$(api_request "/remote/execute" "POST" '{"type":"prompt","message":"Hello, what is 2+2?"}')
echo "$result" | jq '.' 2>/dev/null || echo "$result"
echo ""

# Test 5: Execute a Shell Command
echo "Test 5: Execute Shell Command (echo test)"
echo "-----------------------------------------"
result=$(api_request "/remote/execute" "POST" '{"type":"shell","command":"echo Remote API Test"}')
echo "$result" | jq '.' 2>/dev/null || echo "$result"
echo ""

echo "======================================"
echo "All tests completed!"
echo "======================================"
echo ""
echo "To test interactively, use the remote client:"
echo "  bun test/remote-client.ts health"
echo "  bun test/remote-client.ts list"
echo "  bun test/remote-client.ts prompt 'Hello AI'"
echo "  bun test/remote-client.ts shell 'ls -la'"
echo ""
