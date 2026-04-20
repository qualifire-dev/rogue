package com.shirtify.agent

import com.codahale.metrics.health.HealthCheck

class AgentHealthCheck(
    private val agentService: ShirtifyAgentService
) : HealthCheck() {

    override fun check(): Result {
        return if (agentService.isHealthy()) {
            Result.healthy("Agent is responding")
        } else {
            Result.unhealthy("Agent is not responding")
        }
    }
}
