package com.shirtify.agent

import io.dropwizard.core.Configuration
import com.fasterxml.jackson.annotation.JsonProperty
import jakarta.validation.constraints.NotEmpty

class ShirtifyConfiguration : Configuration() {
    @NotEmpty
    @JsonProperty
    var openaiApiKey: String = ""

    @NotEmpty
    @JsonProperty
    var openaiModel: String = "gpt-4o"

    @JsonProperty
    var agentName: String = "Shirtify T-Shirt Store Agent (Dropwizard)"
}
