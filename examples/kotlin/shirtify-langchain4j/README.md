# Shirtify T-Shirt Store Agent (Kotlin + LangChain4j)

A Kotlin implementation of the Shirtify t-shirt store agent using LangChain4j
with Spring Boot and the A2A (Agent-to-Agent) protocol.

## Prerequisites

- JDK 17 or higher
- Gradle 8.x
- OpenAI API key

## Quick Start

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. Build the project:
   ```bash
   ./gradlew build
   ```

3. Run the agent:
   ```bash
   ./gradlew bootRun
   ```

4. The agent will be available at:
   - Agent Card: `http://localhost:10003/.well-known/agent.json`
   - A2A Endpoint: `http://localhost:10003/`

## Testing with Rogue

Run a red team scan against this agent:

```bash
rogue-ai red-team --agent-url http://localhost:10003 --protocol a2a
```

## Project Structure

- `ShirtifyAgent.kt` - LangChain4j AI Service interface with system prompt
- `ShirtifyTools.kt` - Tool definitions (inventory, email)
- `A2AController.kt` - A2A protocol REST endpoints

## Tech Stack

- Kotlin 1.9
- Spring Boot 3.4
- LangChain4j 1.11.0
