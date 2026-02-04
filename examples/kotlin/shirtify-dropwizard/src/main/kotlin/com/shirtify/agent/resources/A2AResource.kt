package com.shirtify.agent.resources

import com.shirtify.agent.ShirtifyAgentService
import com.fasterxml.jackson.databind.ObjectMapper
import jakarta.ws.rs.*
import jakarta.ws.rs.core.MediaType
import org.slf4j.LoggerFactory
import java.util.*
import java.util.concurrent.ConcurrentHashMap

// A2A Protocol Data Classes
data class AgentCard(
    val name: String,
    val description: String,
    val url: String,
    val version: String,
    val defaultInputModes: List<String>,
    val defaultOutputModes: List<String>,
    val capabilities: Map<String, Any>,
    val skills: List<AgentSkill>
)

data class AgentSkill(
    val id: String,
    val name: String,
    val description: String,
    val tags: List<String>,
    val examples: List<String>
)

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

data class Task(
    val id: String,
    val contextId: String,
    val state: String,
    val messages: MutableList<Message> = mutableListOf(),
    val artifacts: MutableList<Artifact> = mutableListOf()
)

data class Message(
    val role: String,
    val parts: List<Part>
)

data class Part(
    val type: String = "text",
    val text: String
)

data class Artifact(
    val name: String,
    val parts: List<Part>
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
        return AgentCard(
            name = agentName,
            description = "A Kotlin/LangChain4j/Dropwizard agent that sells Shirtify T-Shirts",
            url = "http://localhost:10004/",
            version = "1.0.0",
            defaultInputModes = listOf("text", "text/plain"),
            defaultOutputModes = listOf("text", "text/plain"),
            capabilities = mapOf("streaming" to false),
            skills = listOf(
                AgentSkill(
                    id = "sell_tshirt",
                    name = "Sell T-Shirt",
                    description = "Helps with selling Shirtify T-Shirts",
                    tags = listOf("sell", "tshirt", "store"),
                    examples = listOf("I want to buy a t-shirt", "Show me available colors")
                )
            )
        )
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
        val messageId = message?.get("messageId") as? String ?: UUID.randomUUID().toString()
        val taskId = UUID.randomUUID().toString()

        val task = Task(
            id = taskId,
            contextId = contextId,
            state = "working"
        )
        task.messages.add(Message("user", listOf(Part(text = userInput))))
        tasks[taskId] = task

        return try {
            val response = agentService.chat(userInput)
            log.info("message/send: agent response=\"{}\"", response)
            task.artifacts.add(Artifact("response", listOf(Part(text = response))))
            tasks[taskId] = task.copy(state = "completed")

            // Return in message/send response format
            A2AResponse(
                id = request.id,
                result = mapOf(
                    "kind" to "message",
                    "role" to "agent",
                    "messageId" to UUID.randomUUID().toString(),
                    "contextId" to contextId,
                    "parts" to listOf(mapOf("kind" to "text", "text" to response))
                )
            )
        } catch (e: Exception) {
            log.error("message/send: agent error", e)
            tasks[taskId] = task.copy(state = "failed")
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
