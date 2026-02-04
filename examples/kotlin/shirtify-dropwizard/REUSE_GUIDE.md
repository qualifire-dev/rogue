# Building Your Own A2A Agent with Kotlin + Dropwizard

This guide explains what you can copy as-is from the Shirtify example and what you need to customize for your own agent.

## What You Can Reuse As-Is

These files are generic A2A infrastructure with no agent-specific logic. Copy them directly.

### `A2AJacksonModule.kt`

The entire Jackson module is reusable. It bridges the A2A Java SDK spec types (which use Gson internally) with Dropwizard's Jackson serialization. It handles:

- `Part<?>` polymorphic serialization/deserialization (`TextPart`, `DataPart`, `FilePart`)
- `AgentCard` serialization with backward-compatible `url` field (required by rogue TUI)
- `TaskState` enum wire format (`"working"`, `"completed"`, etc.)
- `TaskStatus`, `Message`, `Artifact`, `AgentSkill`, `AgentCapabilities` serialization

No changes needed unless the A2A spec changes.

### JSON-RPC Envelope Classes (in `A2AResource.kt`)

These three data classes wrap JSON-RPC 2.0 transport and are not agent-specific:

```kotlin
data class A2ARequest(...)
data class A2AResponse(...)
data class A2AError(...)
```

The SDK's server module handles these internally, but since we use Dropwizard's JAX-RS instead of the SDK server (which requires CDI), we need to keep these.

### `A2AResource.kt` Request Routing

The `handleA2ARequest()` method and its `when` block dispatching `message/send`, `tasks/get`, and `tasks/cancel` is standard A2A protocol routing. The request parsing logic in `handleMessageSend()` (extracting text from parts, contextId handling) is also reusable.

### `build.gradle.kts` Structure

The Gradle setup is reusable:
- Shadow JAR configuration
- Kotlin compiler options (`-Xjsr305=strict`, `javaParameters`)
- The `a2a-java-sdk-spec` dependency (use only `spec`, not the server module)

### `Makefile`

The `dev`, `build`, and `clean` targets are generic.

### `ShirtifyApplication.kt` Bootstrap Pattern

The `.env` loading, Kotlin module registration, and A2A Jackson module registration pattern is reusable:

```kotlin
bootstrap.objectMapper.registerKotlinModule()
bootstrap.objectMapper.registerModule(A2AJacksonModule())
```

## What You Need to Change

### `AgentCard` in `A2AResource.getAgentCard()`

Update the agent card to describe **your** agent:

```kotlin
AgentCard.builder()
    .name("Your Agent Name")                          // <-- change
    .description("What your agent does")              // <-- change
    .version("1.0.0")
    .defaultInputModes(listOf("text", "text/plain"))
    .defaultOutputModes(listOf("text", "text/plain"))
    .capabilities(
        AgentCapabilities.builder()
            .streaming(false)         // set true if you support streaming
            .pushNotifications(false) // set true if you support push
            .build()
    )
    .skills(listOf(                                   // <-- change
        AgentSkill.builder()
            .id("your_skill_id")
            .name("Your Skill")
            .description("What this skill does")
            .tags(listOf("your", "tags"))
            .examples(listOf("Example prompt 1", "Example prompt 2"))
            .build()
    ))
    .supportedInterfaces(listOf(
        AgentInterface("jsonrpc", "http://localhost:YOUR_PORT/")  // <-- change port
    ))
    .build()
```

### Agent Service (`ShirtifyAgentService.kt`)

Replace entirely with your own agent logic. This file contains:
- The LLM configuration (model, API key)
- The system prompt that defines agent behavior
- The `chat()` method that processes user input

Your service just needs to expose a `chat(message: String): String` method (or equivalent) that the resource can call.

### Tools (`ShirtifyTools.kt`)

Replace with your own LangChain4j tools. Each `@Tool`-annotated method defines a capability your agent can use. Delete the Shirtify-specific `inventory()` and `sendEmail()` methods and add your own.

### Configuration (`ShirtifyConfiguration.kt` + `config.yml`)

Update to match your agent's configuration needs:

- **`config.yml`**: Change the port, agent name, and any agent-specific settings
- **`ShirtifyConfiguration.kt`**: Add/remove configuration fields as needed

### Health Check (`AgentHealthCheck.kt`)

Update the health check if your agent service has a different interface. The pattern (call the agent and check for exceptions) is reusable, but the service type reference needs to match yours.

## File-by-File Summary

| File | Reuse? | Action |
|------|--------|--------|
| `A2AJacksonModule.kt` | Copy as-is | No changes needed |
| `A2AResource.kt` (JSON-RPC classes) | Copy as-is | No changes needed |
| `A2AResource.kt` (request routing) | Copy as-is | No changes needed |
| `A2AResource.kt` (agent card) | Modify | Update name, description, skills, port |
| `A2AResource.kt` (agent service ref) | Modify | Point to your service class |
| `ShirtifyAgentService.kt` | Replace | Write your own agent logic |
| `ShirtifyTools.kt` | Replace | Define your own tools |
| `ShirtifyConfiguration.kt` | Modify | Add your config fields |
| `ShirtifyApplication.kt` | Modify | Change class names, keep bootstrap pattern |
| `AgentHealthCheck.kt` | Modify | Update service type reference |
| `config.yml` | Modify | Change port, agent name, settings |
| `build.gradle.kts` | Modify | Change group/artifact, keep dependency structure |
| `Makefile` | Copy as-is | No changes needed |

## Key Dependency Note

Only use `a2a-java-sdk-spec` — **not** `a2a-java-sdk-server-common` or `a2a-java-sdk-server-jakarta`. The server modules require CDI (`@ApplicationScoped`) which is incompatible with Dropwizard's HK2 dependency injection. The spec module gives you all the protocol data types without the container dependency.

```kotlin
// Good
implementation("io.github.a2asdk:a2a-java-sdk-spec:1.0.0.Alpha1")

// Don't use with Dropwizard
implementation("io.github.a2asdk:a2a-java-sdk-server-jakarta:1.0.0.Alpha1")
```
