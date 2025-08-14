# Testing Guide: Gradio UI with FastAPI Server

This guide shows you how to test the complete Phase 3 implementation with the Gradio UI connected to the FastAPI server.

## Prerequisites

Make sure you have the dependencies installed:
```bash
uv sync --dev --examples
```

## Step 1: Start the FastAPI Server

In **Terminal 1**, start the server:

```bash
uv run python -m rogue.server
```

You should see output like:
```
INFO: Started server process [12345]
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

**Keep this terminal running!**

## Step 2: Verify Server is Running

In **Terminal 2**, test the server:

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test SDK connection
uv run python -c "
import asyncio
from rogue_sdk import RogueSDK, RogueClientConfig

async def test():
    config = RogueClientConfig(base_url='http://localhost:8000', timeout=30.0)
    sdk = RogueSDK(config)
    health = await sdk.health()
    print(f'✅ Server status: {health.status}')
    await sdk.close()

asyncio.run(test())
"
```

## Step 3: Start the Gradio UI

In **Terminal 2** (or a new terminal), start the UI:

```bash
uv run python -m rogue ui
```

The UI will start on http://localhost:7860

## Step 4: Test the Full Workflow

### Option A: Using the Gradio UI

1. **Open your browser** to http://localhost:7860

2. **Config Tab**: Set up your agent configuration
   - Agent URL: `http://localhost:10001` (or your agent's URL)
   - Authentication: Choose appropriate auth type
   - Models: Set judge LLM model (e.g., `openai/gpt-4o-mini`)
   - API Keys: Add your LLM provider API key

3. **Interview Tab**: Generate business context
   - Answer questions about your agent
   - The AI interviewer will help extract business context

4. **Scenarios Tab**: Generate test scenarios
   - Based on the business context from step 3
   - Review and edit scenarios as needed

5. **Run & Evaluate Tab**: Execute evaluations
   - Click "Run Scenarios"
   - ✅ **Status Updates**: See real-time progress messages
   - ✅ **Chat Messages**: Watch live conversation during evaluation
   - ✅ **Multiple Workers**: See parallel execution in action
   - ✅ **WebSocket Connection**: Real-time updates from server

6. **Report Tab**: View results
   - See evaluation results and summary
   - Export reports if needed

### **What You Should See in the UI**

When running evaluations, you should now see:

- **Real-time Status Updates**: 
  - "Job abc123 started, connecting to real-time updates..."
  - "Status: running (15s elapsed)"
  - "Connected to WebSocket for job abc123"

- **Live Chat Messages**:
  - "Worker 1: Evaluating 3 scenarios..."
  - "Processing scenario batch 1 - 25s elapsed"
  - "✅ Evaluation completed for worker 1!"

- **Progress Indicators**: Each worker shows its own status and chat history
- **Parallel Execution**: Multiple workers running simultaneously with separate progress

### Option B: Using the CLI

Test the CLI with SDK integration:

```bash
# Create a test directory
mkdir -p .rogue_test
cd .rogue_test

# Create a simple scenarios file
cat > scenarios.json << 'EOF'
{
  "scenarios": [
    {
      "scenario": "Test basic functionality",
      "type": "policy"
    }
  ]
}
EOF

# Run evaluation via CLI (will use SDK if server is running)
uv run python -m rogue cli \
  --evaluated-agent-url "http://localhost:10001" \
  --judge-llm "openai/gpt-4o-mini" \
  --business-context "Test agent for demonstration"
```

## Step 5: Test WebSocket Real-time Updates

The UI now supports real-time updates via WebSocket! When you run evaluations:

1. **Status updates** appear in real-time
2. **Chat conversations** stream live during agent evaluation
3. **Progress indicators** update without page refresh
4. **Error handling** gracefully falls back if WebSocket fails

## Step 6: Test Fallback Mechanism

To test the fallback to legacy services:

1. **Stop the server** (Ctrl+C in Terminal 1)
2. **Try running an evaluation** in the UI
3. You should see a warning message about falling back to legacy services
4. The evaluation should still work using the original `ScenarioEvaluationService`

## Recent Fixes

✅ **Fixed SDK Integration Issues** (2025-07-30):
- Fixed `quick_evaluate()` method call - removed invalid `scenario_type` parameter
- Fixed method names: `health_check()` → `health()`, `wait_for_completion()` → `wait_for_evaluation()`
- Added proper type conversion and error handling
- **Fixed UI Updates**: Implemented proper real-time status and chat updates
- **Enhanced WebSocket Support**: Added WebSocket connection with polling fallback
- **Added Progress Indicators**: Real-time status updates and chat messages during evaluation

## Debugging UI Updates

If the UI is not showing real-time updates, check these logs:

### **1. Gradio UI Debug Logs**
```bash
# The UI now creates detailed debug logs
tail -f gradio_ui_debug.log
```

Look for these log patterns:
- `🚀 Starting run_and_evaluate_scenarios` - Button clicked
- `🔧 Starting worker X with Y scenarios` - Workers starting
- `📨 Received update: worker_id=X, type=status` - Updates received
- `💬 Adding chat message for worker X` - Chat messages
- `📊 Status update for worker X` - Status updates

### **2. Test UI Updates in Isolation**
```bash
# Run a simple UI update test
uv run python debug_ui_updates.py
# Open http://localhost:7861 and test basic updates
```

### **3. Server Logs**
```bash
# Check server logs for evaluation processing
uv run python -m rogue.server
# Look for job creation and processing logs
```

### **4. Common Issues**

**No updates appearing:**
- Check `gradio_ui_debug.log` for `📨 Received update` messages
- Verify workers are starting: look for `🔧 Starting worker` logs
- Check if updates are being yielded: look for `Yielding X updates to UI`

**Chat not updating:**
- Look for `💬 Adding chat message` in logs
- Verify chat history length: `Worker X chat history now has Y messages`
- Check component index: `Chat update prepared for component index Z`

**Status not updating:**
- Look for `📊 Status update` in logs  
- Verify status messages are being sent to queue
- Check if status updates are being processed

## Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
lsof -ti:8000

# Kill process if needed
kill $(lsof -ti:8000)

# Start server on different port
uv run python -m rogue.server --port 8001
```

### UI Can't Connect to Server
- Make sure server is running on http://localhost:8000
- Check server logs for errors
- Verify SDK connection with the test command above

### WebSocket Issues
- WebSocket connections require both HTTP and WS protocols
- If WebSocket fails, the system automatically falls back to polling
- Check browser developer tools for WebSocket connection errors

## Architecture Overview

```
Browser (localhost:7860)
    ↓ HTTP/WebSocket
Gradio UI
    ↓ Python SDK
FastAPI Server (localhost:8000)
    ↓ HTTP/WebSocket
Agent Under Test
```

## Key Features Demonstrated

✅ **SDK Integration**: UI uses Python SDK for server communication  
✅ **Real-time Updates**: WebSocket streaming for live progress  
✅ **Fallback Mechanism**: Graceful degradation to legacy services  
✅ **Backward Compatibility**: All existing functionality preserved  
✅ **Type Safety**: Proper type conversion between legacy and SDK types  

## Next Steps

- Try different agent configurations
- Test with various LLM models
- Experiment with different scenario types
- Monitor server logs for debugging
- Use the API documentation at http://localhost:8000/docs

Happy testing! 🚀
