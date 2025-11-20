#!/bin/bash
# Simple test for red team mode

echo "🔴 Testing Red Team Mode"
echo "========================"
echo ""

# Create red team evaluation
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "evaluated_agent_url": "http://localhost:10001",
      "judge_llm": "openai/gpt-4o-mini",
      "evaluation_mode": "red_team",
      "owasp_categories": ["LLM_01", "LLM_06", "LLM_07"],
      "attacks_per_category": 2,
      "business_context": "A test agent for security evaluation."
    },
    "scenarios": [],
    "max_retries": 3,
    "timeout_seconds": 600
  }')

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool

JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to create job"
    exit 1
fi

echo ""
echo "✅ Job created: $JOB_ID"
echo ""
echo "Check status with:"
echo "curl http://localhost:8000/api/v1/evaluations/$JOB_ID | python3 -m json.tool"
