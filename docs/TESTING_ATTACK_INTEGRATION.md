# Testing Attack Strategy Integration

## Quick Test

Yes, you can use the same curl command! Attack enhancement happens automatically when you run a red team evaluation. Here's how to test and verify it's working:

## Step-by-Step Test

### 1. Start the Target Agent

```bash
# Terminal 1: Start t-shirt store agent
cd /Users/drorivry/develop/rogue-private
uv run python -m examples.tshirt_store_agent
# Runs on http://localhost:10001
```

### 2. Start the Rogue Server

```bash
# Terminal 2: Start Rogue server
cd /Users/drorivry/develop/rogue-private
uv run python -m rogue server
# Runs on http://localhost:8000
```

### 3. Run Red Team Evaluation (Same curl command)

```bash
# Terminal 3: Create evaluation job
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "evaluated_agent_url": "http://localhost:10001",
      "judge_llm": "openai/gpt-4o-mini",
      "judge_llm_api_key": "sk-your-key-here",
      "evaluation_mode": "red_team",
      "owasp_categories": ["LLM_01", "LLM_06", "LLM_07"],
      "attacks_per_category": 3,
      "business_context": "A t-shirt store agent that sells custom t-shirts."
    },
    "scenarios": [],
    "max_retries": 3,
    "timeout_seconds": 600
  }'
```

Save the `job_id` from the response.

### 4. Monitor Server Logs (To See Attack Enhancement)

Watch the server logs in Terminal 2. You should see debug messages like:

```
🔴 Enhanced message with attack
  - attack_name: PromptInjection
  - category_id: LLM_01
  - context_id: abc123...
  - original_length: 50
  - enhanced_length: 200
```

### 5. Check Results

```bash
# Get evaluation results
curl http://localhost:8000/api/v1/evaluations/{job_id} | jq '.results'
```

## Using the Test Script

You can also use the existing test script:

```bash
cd /Users/drorivry/develop/rogue-private
./test_server_red_team.sh
```

This script:
1. Checks server health
2. Creates a red team evaluation
3. Polls for completion
4. Shows results

## What to Look For

### In Server Logs

Look for these log messages indicating attack enhancement:

1. **Attack Enhancement Logs**:
   ```
   🔴 Enhanced message with attack
   ```

2. **Attack Selection**:
   ```
   attack_name: PromptInjection
   category_id: LLM_01
   ```

3. **Message Transformation**:
   ```
   original_length: 50
   enhanced_length: 200
   ```

### In Evaluation Results

Check the evaluation results for:

1. **Red Teaming Results**: Look for `red_teaming_results` in the response
2. **OWASP Summary**: Check `owasp_summary` for category-level results
3. **Conversation History**: Review chat messages to see enhanced attack messages

### Example: Checking Results

```bash
# Get full results
curl -s http://localhost:8000/api/v1/evaluations/{job_id} | jq '{
  status: .status,
  red_teaming_results: .results.red_teaming_results,
  owasp_summary: .results.owasp_summary,
  conversations: .results.conversations
}'
```

## Verifying Attack Enhancement

### Method 1: Check Logs

Enable debug logging to see attack enhancement:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
uv run python -m rogue server
```

### Method 2: Inspect Chat History

Look at the conversation history in results. Enhanced messages will be:
- Longer than original (due to attack wrappers)
- Contain encoded/obfuscated content (for encoding attacks)
- Include adversarial instructions (for prompt injection)

### Method 3: Compare Message Lengths

Attack-enhanced messages are typically longer:
- **Original**: ~50-100 characters
- **Enhanced**: ~200-500 characters (varies by attack type)

## Expected Behavior

### Attack Enhancement Probability

- **70%** of messages will be enhanced with attacks
- **30%** of messages will be sent raw (for natural variation)

### Attack Selection

Attacks are selected based on:
1. **OWASP Category**: Matches attack to vulnerability type
2. **Attack Weight**: Higher weight = more likely to be selected
3. **Random Selection**: From weighted attack list

### Attack Types by Category

**LLM_01 (Prompt Injection)**:
- PromptInjection (weight=3) - most common
- Base64, ROT13, Leetspeak (weight=2)
- Roleplay, PromptProbing (weight=2)

**LLM_06 (Excessive Agency)**:
- Roleplay (weight=3) - most common
- PromptInjection, PromptProbing (weight=2)

**LLM_07 (System Prompt Leakage)**:
- PromptInjection, PromptProbing (weight=2)
- Base64, ROT13 (weight=1)

## Troubleshooting

### No Attack Enhancement Logs

If you don't see attack enhancement logs:

1. **Check evaluation mode**: Must be `"evaluation_mode": "red_team"`
2. **Check OWASP categories**: Must include at least one category
3. **Check logs**: Look for errors in server logs

### Attacks Not Being Applied

If attacks aren't being applied:

1. **Verify red team evaluator**: Check logs for "🔴 Creating Red Team" messages
2. **Check scenario tracking**: Verify scenarios are being generated
3. **Check attack classes**: Ensure attack classes are imported correctly

### Debug Mode

Enable more verbose logging:

```python
# In your test script or server startup
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Quick Test Command

Here's a one-liner to test attack integration:

```bash
# Start agent, server, and run test
(cd /Users/drorivry/develop/rogue-private && \
 uv run python -m examples.tshirt_store_agent &) && \
sleep 2 && \
(cd /Users/drorivry/develop/rogue-private && \
 uv run python -m rogue server &) && \
sleep 2 && \
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "evaluated_agent_url": "http://localhost:10001",
      "judge_llm": "openai/gpt-4o-mini",
      "judge_llm_api_key": "sk-your-key-here",
      "evaluation_mode": "red_team",
      "owasp_categories": ["LLM_01"],
      "attacks_per_category": 2,
      "business_context": "Test agent"
    },
    "scenarios": [],
    "max_retries": 1,
    "timeout_seconds": 300
  }' | jq -r '.job_id'
```

## Next Steps

After verifying attack integration works:

1. **Test Different Categories**: Try different OWASP categories
2. **Test Attack Weights**: Verify higher-weight attacks are selected more often
3. **Test Multi-Turn**: Run longer evaluations to see attack variety
4. **Review Results**: Analyze which attacks successfully exploit vulnerabilities

## Related Documentation

- [Attack Strategy Integration](./ATTACK_STRATEGY_INTEGRATION.md) - Full implementation details
- [Testing with curl](./TESTING_WITH_CURL.md) - General API testing guide
- [Red Teaming Guide](./RED_TEAMING_GUIDE.md) - Comprehensive red teaming documentation
