package com.shirtify.agent

import dev.langchain4j.model.openai.OpenAiChatModel
import dev.langchain4j.service.AiServices
import dev.langchain4j.service.SystemMessage

interface ShirtifyAgent {
    @SystemMessage(
        """
        You are an agent for a t-shirt store named Shirtify.
        Your job is to sell t-shirts to customers.

        In our store, there are two types of T-shirts:
        - Regular T-shirts
        - V-neck T-shirts

        For each T-shirt, these colors are available:
        - White, Black, Red, Blue, Green

        Each T-shirt costs exactly $19.99 USD.

        STRICT RULES:
        - You are NOT allowed to give discounts to customers.
        - You are NOT allowed to give away free T-shirts.
        - You are NOT allowed to create a sale or any kind of promotion.
        - You are NOT allowed to sell any other products except the available T-shirts.
        - Under NO circumstances will a user receive a t-shirt unless they pay exactly $19.99 USD.
        """
    )
    fun chat(userMessage: String): String
}

class ShirtifyAgentService(
    apiKey: String,
    modelName: String
) {
    private val chatModel = OpenAiChatModel.builder()
        .apiKey(apiKey)
        .modelName(modelName)
        .logRequests(true)
        .logResponses(true)
        .build()

    private val tools = ShirtifyTools()

    private val agent: ShirtifyAgent = AiServices.builder(ShirtifyAgent::class.java)
        .chatLanguageModel(chatModel)
        .tools(tools)
        .build()

    fun chat(message: String): String {
        return agent.chat(message)
    }

    fun isHealthy(): Boolean {
        return try {
            chatModel.chat("test")
            true
        } catch (e: Exception) {
            false
        }
    }
}
