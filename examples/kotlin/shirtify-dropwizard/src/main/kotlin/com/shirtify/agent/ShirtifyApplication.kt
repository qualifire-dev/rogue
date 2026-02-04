package com.shirtify.agent

import com.shirtify.agent.resources.A2AResource
import io.dropwizard.core.Application
import io.dropwizard.core.setup.Bootstrap
import io.dropwizard.core.setup.Environment
import com.fasterxml.jackson.module.kotlin.registerKotlinModule

class ShirtifyApplication : Application<ShirtifyConfiguration>() {

    override fun getName(): String = "shirtify-dropwizard"

    override fun initialize(bootstrap: Bootstrap<ShirtifyConfiguration>) {
        // Register Kotlin module for Jackson
        bootstrap.objectMapper.registerKotlinModule()
    }

    override fun run(configuration: ShirtifyConfiguration, environment: Environment) {
        // Create the LangChain4j agent service
        val agentService = ShirtifyAgentService(
            apiKey = configuration.openaiApiKey,
            modelName = configuration.openaiModel
        )

        // Register the A2A resource
        val a2aResource = A2AResource(
            agentService = agentService,
            agentName = configuration.agentName
        )
        environment.jersey().register(a2aResource)

        // Register health check
        environment.healthChecks().register("agent", AgentHealthCheck(agentService))
    }
}

fun main(args: Array<String>) {
    ShirtifyApplication().run(*args)
}
