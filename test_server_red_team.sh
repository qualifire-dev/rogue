#!/bin/bash
# Quick test script for red team mode via curl

set -e

SERVER_URL="${SERVER_URL:-http://localhost:8000}"
AGENT_URL="${AGENT_URL:-http://localhost:10001}"
JUDGE_LLM="${JUDGE_LLM:-openai/gpt-4o-mini}"

echo "🔴 Testing Rogue Red Team Mode"
echo "================================"
echo "Server: $SERVER_URL"
echo "Target Agent: $AGENT_URL"
echo "Judge LLM: $JUDGE_LLM"
echo ""

# Check if server is running
echo "1. Checking server health..."
if ! curl -s -f "$SERVER_URL/api/v1/health" > /dev/null; then
    echo "❌ Server is not running at $SERVER_URL"
    echo "   Start it with: uvx rogue-ai server"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Create red team evaluation
echo "2. Creating red team evaluation job..."
RESPONSE=$(curl -s -X POST "$SERVER_URL/api/v1/evaluations" \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_config\": {
      \"evaluated_agent_url\": \"$AGENT_URL\",
      \"judge_llm\": \"$JUDGE_LLM\",
      \"evaluation_mode\": \"red_team\",
      \"owasp_categories\": [\"LLM_01\", \"LLM_06\", \"LLM_07\"],
      \"attacks_per_category\": 3,
      \"business_context\": \"A test agent for security evaluation.\"
    },
    \"scenarios\": [],
    \"max_retries\": 3,
    \"timeout_seconds\": 600
  }")

JOB_ID=$(echo "$RESPONSE" | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to create evaluation job"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "✅ Job created: $JOB_ID"
echo ""

# Poll for completion
echo "3. Waiting for evaluation to complete..."
MAX_WAIT=300  # 5 minutes
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS=$(curl -s "$SERVER_URL/api/v1/evaluations/$JOB_ID" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Evaluation completed!"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Evaluation failed"
        curl -s "$SERVER_URL/api/v1/evaluations/$JOB_ID" | grep -A 5 "error_message" || true
        exit 1
    fi
    
    echo "   Status: $STATUS (waiting...)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "⏰ Timeout waiting for evaluation"
    exit 1
fi

# Get results
echo ""
echo "4. Fetching results..."
curl -s "$SERVER_URL/api/v1/evaluations/$JOB_ID" | python3 -m json.tool

echo ""
echo "✅ Test complete!"
echo "View full results: curl $SERVER_URL/api/v1/evaluations/$JOB_ID"
