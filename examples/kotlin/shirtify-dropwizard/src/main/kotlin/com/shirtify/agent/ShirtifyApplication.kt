package com.shirtify.agent

import com.shirtify.agent.resources.A2AResource
import io.dropwizard.configuration.SubstitutingSourceProvider
import io.dropwizard.core.Application
import io.dropwizard.core.setup.Bootstrap
import io.dropwizard.core.setup.Environment
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import org.apache.commons.text.StringSubstitutor
import org.apache.commons.text.lookup.StringLookupFactory

class ShirtifyApplication : Application<ShirtifyConfiguration>() {

    override fun getName(): String = "shirtify-dropwizard"

    override fun initialize(bootstrap: Bootstrap<ShirtifyConfiguration>) {
        // Register Kotlin module for Jackson
        bootstrap.objectMapper.registerKotlinModule()

        // Register A2A SDK Jackson module for Part<?> polymorphism and AgentCard compatibility
        bootstrap.objectMapper.registerModule(A2AJacksonModule())

        // Enable ${VAR} substitution in config.yml, checking env vars then system properties (.env)
        val substitutor = StringSubstitutor { key ->
            System.getenv(key) ?: System.getProperty(key)
        }
        bootstrap.configurationSourceProvider = SubstitutingSourceProvider(
            bootstrap.configurationSourceProvider,
            substitutor
        )
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
    // Load .env file and set as system properties so Dropwizard's
    // ${OPENAI_API_KEY} substitution in config.yml picks them up
    val dotenv = io.github.cdimascio.dotenv.Dotenv.configure()
        .ignoreIfMissing()
        .load()
    for (entry in dotenv.entries()) {
        if (System.getenv(entry.key) == null) {
            System.setProperty(entry.key, entry.value)
        }
    }

    ShirtifyApplication().run(*args)
}
