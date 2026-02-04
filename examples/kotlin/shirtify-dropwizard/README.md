# Shirtify T-Shirt Store Agent (Kotlin + LangChain4j + Dropwizard)

A Kotlin implementation of the Shirtify t-shirt store agent using LangChain4j
with Dropwizard and the A2A (Agent-to-Agent) protocol.

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
   ./gradlew shadowJar
   ```

3. Run the agent:
   ```bash
   java -jar build/libs/shirtify-dropwizard.jar server src/main/resources/config.yml
   ```

   Or using Gradle:
   ```bash
   ./gradlew run --args="server src/main/resources/config.yml"
   ```

4. The agent will be available at:
   - Agent Card: `http://localhost:10004/.well-known/agent.json`
   - A2A Endpoint: `http://localhost:10004/`
   - Admin/Health: `http://localhost:10005/healthcheck`

## Testing with Rogue

Run a red team scan against this agent:

```bash
rogue-ai red-team --agent-url http://localhost:10004 --protocol a2a
```

## Project Structure

- `ShirtifyApplication.kt` - Dropwizard Application entry point
- `ShirtifyConfiguration.kt` - YAML configuration mapping
- `ShirtifyAgentService.kt` - LangChain4j AI Service (manual wiring)
- `ShirtifyTools.kt` - Tool definitions (inventory, email)
- `A2AResource.kt` - Jersey JAX-RS A2A endpoints
- `AgentHealthCheck.kt` - Dropwizard health check

## Tech Stack

- Kotlin 1.9
- Dropwizard 4.0
- LangChain4j 1.11.0
- Jersey (JAX-RS)
- Jetty
