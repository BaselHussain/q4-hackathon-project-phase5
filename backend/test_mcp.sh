#!/bin/bash
set -e

BASE_URL="http://localhost:8001/mcp"
HEADERS='-H "Content-Type: application/json" -H "Accept: application/json, text/event-stream"'

echo "=== T042: Testing MCP Tools ==="
echo ""

# Initialize session and get ID
echo "1. Initializing session..."
INIT_RESPONSE=$(curl -s -i -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}')

SESSION_ID=$(echo "$INIT_RESPONSE" | grep -i "mcp-session-id" | cut -d' ' -f2 | tr -d '\r')
echo "   Session ID: $SESSION_ID"

# List tools
echo ""
echo "2. Listing tools..."
curl -s -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 2}' | python -c "import sys,json; d=json.load(sys.stdin); tools=[t['name'] for t in d.get('result',{}).get('tools',[])]; print('   Tools:', tools)"

# Test add_task
echo ""
echo "3. Testing add_task..."
ADD_RESULT=$(curl -s -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add_task", "arguments": {"user_id": "550e8400-e29b-41d4-a716-446655440000", "title": "Test task from MCP", "description": "Testing MCP tools"}}, "id": 3}')
echo "   Response: $ADD_RESULT" | head -c 200
echo ""

# Test list_tasks
echo ""
echo "4. Testing list_tasks..."
LIST_RESULT=$(curl -s -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "list_tasks", "arguments": {"user_id": "550e8400-e29b-41d4-a716-446655440000", "status": "all"}}, "id": 4}')
echo "   Response: $LIST_RESULT" | head -c 300
echo ""

# Test with invalid user (T043 - ownership test)
echo ""
echo "=== T043: Testing ownership enforcement ==="
echo "5. Testing with wrong user_id..."
WRONG_USER=$(curl -s -X POST $BASE_URL \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "complete_task", "arguments": {"user_id": "00000000-0000-0000-0000-000000000001", "task_id": "00000000-0000-0000-0000-000000000002"}}, "id": 5}')
echo "   Response: $WRONG_USER"

echo ""
echo "=== All tests completed ==="
