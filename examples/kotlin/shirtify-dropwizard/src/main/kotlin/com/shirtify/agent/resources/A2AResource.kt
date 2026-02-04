package com.shirtify.agent.resources

import com.shirtify.agent.ShirtifyAgentService
import com.fasterxml.jackson.databind.ObjectMapper
import io.a2a.spec.*
import jakarta.ws.rs.*
import jakarta.ws.rs.core.MediaType
import org.slf4j.LoggerFactory
import java.util.*
import java.util.concurrent.ConcurrentHashMap

// JSON-RPC envelope classes (SDK doesn't expose these — transport handles them in the SDK server module)
data class A2ARequest(
    val jsonrpc: String = "2.0",
    val id: String? = null,
    val method: String = "",
    val params: Map<String, Any>? = null
)

data class A2AResponse(
    val jsonrpc: String = "2.0",
    val id: String?,
    val result: Any? = null,
    val error: A2AError? = null
)

data class A2AError(
    val code: Int,
    val message: String,
    val data: Any? = null
)

@Path("/")
@Produces(MediaType.APPLICATION_JSON)
class A2AResource(
    private val agentService: ShirtifyAgentService,
    private val agentName: String
) {
    private val log = LoggerFactory.getLogger(A2AResource::class.java)
    private val mapper = ObjectMapper()
    private val tasks = ConcurrentHashMap<String, Task>()

    @GET
    @Path(".well-known/agent.json")
    fun getAgentCard(): AgentCard {
        return AgentCard.builder()
            .name(agentName)
            .description("A Kotlin/LangChain4j/Dropwizard agent that sells Shirtify T-Shirts")
            .version("1.0.0")
            .defaultInputModes(listOf("text", "text/plain"))
            .defaultOutputModes(listOf("text", "text/plain"))
            .capabilities(
                AgentCapabilities.builder()
                    .streaming(false)
                    .pushNotifications(false)
                    .stateTransitionHistory(false)
                    .build()
            )
            .skills(listOf(
                AgentSkill.builder()
                    .id("sell_tshirt")
                    .name("Sell T-Shirt")
                    .description("Helps with selling Shirtify T-Shirts")
                    .tags(listOf("sell", "tshirt", "store"))
                    .examples(listOf("I want to buy a t-shirt", "Show me available colors"))
                    .build()
            ))
            .supportedInterfaces(listOf(
                AgentInterface("jsonrpc", "http://localhost:10004/")
            ))
            .build()
    }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    fun handleA2ARequest(request: A2ARequest): A2AResponse {
        log.info("A2A request: method={}, id={}, params={}", request.method, request.id,
            mapper.writeValueAsString(request.params))

        val response = when (request.method) {
            "message/send" -> handleMessageSend(request)
            "tasks/send" -> handleMessageSend(request)
            "tasks/get" -> handleTaskGet(request)
            "tasks/cancel" -> handleTaskCancel(request)
            else -> A2AResponse(
                id = request.id,
                error = A2AError(-32601, "Method not found: ${request.method}")
            )
        }

        log.info("A2A response: {}", mapper.writeValueAsString(response))
        return response
    }

    private fun handleMessageSend(request: A2ARequest): A2AResponse {
        val params = request.params ?: run {
            log.warn("message/send: missing params")
            return A2AResponse(id = request.id, error = A2AError(-32602, "Missing params"))
        }

        val message = params["message"] as? Map<*, *>
        log.info("message/send: raw message={}", mapper.writeValueAsString(message))

        val parts = (message?.get("parts") as? List<*>)?.filterIsInstance<Map<*, *>>()
        log.info("message/send: parsed parts={}", mapper.writeValueAsString(parts))

        // Support both "text" and "kind":"text" field for the text content
        val userInput = parts?.firstOrNull()?.get("text") as? String
        if (userInput == null) {
            log.warn("message/send: could not extract text from parts. message keys={}, parts={}",
                message?.keys, mapper.writeValueAsString(parts))
            return A2AResponse(id = request.id, error = A2AError(-32602, "Missing message text"))
        }

        log.info("message/send: userInput=\"{}\"", userInput)

        // Extract contextId from message or params
        val contextId = (message?.get("contextId") as? String)
            ?: (params["contextId"] as? String)
            ?: UUID.randomUUID().toString()
        val taskId = UUID.randomUUID().toString()

        val task = Task.builder()
            .id(taskId)
            .contextId(contextId)
            .status(TaskStatus(TaskState.WORKING))
            .history(listOf(
                Message.builder()
                    .role(Message.Role.USER)
                    .parts(TextPart(userInput))
                    .build()
            ))
            .build()
        tasks[taskId] = task

        return try {
            val response = agentService.chat(userInput)
            log.info("message/send: agent response=\"{}\"", response)

            val completedTask = Task.builder(task)
                .status(TaskStatus(TaskState.COMPLETED))
                .artifacts(listOf(
                    Artifact.builder()
                        .artifactId(UUID.randomUUID().toString())
                        .name("response")
                        .parts(TextPart(response))
                        .build()
                ))
                .build()
            tasks[taskId] = completedTask

            // Return in message/send response format using SDK Message type
            val responseMessage = Message.builder()
                .role(Message.Role.AGENT)
                .contextId(contextId)
                .parts(TextPart(response))
                .build()

            A2AResponse(
                id = request.id,
                result = responseMessage
            )
        } catch (e: Exception) {
            log.error("message/send: agent error", e)
            val failedTask = Task.builder(task)
                .status(TaskStatus(TaskState.FAILED))
                .build()
            tasks[taskId] = failedTask
            A2AResponse(
                id = request.id,
                error = A2AError(-32000, "Agent error: ${e.message}")
            )
        }
    }

    private fun handleTaskGet(request: A2ARequest): A2AResponse {
        val taskId = request.params?.get("taskId") as? String
            ?: return A2AResponse(id = request.id, error = A2AError(-32602, "Missing taskId"))

        val task = tasks[taskId]
            ?: return A2AResponse(id = request.id, error = A2AError(-32000, "Task not found"))

        return A2AResponse(id = request.id, result = task)
    }

    private fun handleTaskCancel(request: A2ARequest): A2AResponse {
        return A2AResponse(
            id = request.id,
            error = A2AError(-32601, "Cancel not supported")
        )
    }
}
