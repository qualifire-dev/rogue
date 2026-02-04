package com.shirtify.agent.resources

import com.shirtify.agent.ShirtifyAgentService
import jakarta.ws.rs.*
import jakarta.ws.rs.core.MediaType
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
        return when (request.method) {
            "tasks/send" -> handleTaskSend(request)
            "tasks/get" -> handleTaskGet(request)
            "tasks/cancel" -> handleTaskCancel(request)
            else -> A2AResponse(
                id = request.id,
                error = A2AError(-32601, "Method not found: ${request.method}")
            )
        }
    }

    private fun handleTaskSend(request: A2ARequest): A2AResponse {
        val params = request.params ?: return A2AResponse(
            id = request.id,
            error = A2AError(-32602, "Missing params")
        )

        val message = params["message"] as? Map<*, *>
        val parts = (message?.get("parts") as? List<*>)?.filterIsInstance<Map<*, *>>()
        val userInput = parts?.firstOrNull()?.get("text") as? String
            ?: return A2AResponse(
                id = request.id,
                error = A2AError(-32602, "Missing message text")
            )

        val contextId = params["contextId"] as? String ?: UUID.randomUUID().toString()
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
            task.artifacts.add(Artifact("response", listOf(Part(text = response))))
            tasks[taskId] = task.copy(state = "completed")

            A2AResponse(
                id = request.id,
                result = mapOf(
                    "task" to tasks[taskId],
                    "message" to Message("agent", listOf(Part(text = response)))
                )
            )
        } catch (e: Exception) {
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
