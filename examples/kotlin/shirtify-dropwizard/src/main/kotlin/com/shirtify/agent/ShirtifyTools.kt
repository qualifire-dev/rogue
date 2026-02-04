package com.shirtify.agent

import dev.langchain4j.agent.tool.P
import dev.langchain4j.agent.tool.Tool

class ShirtifyTools {

    @Tool("Check the inventory for a specific color and size of t-shirt")
    fun inventory(
        @P("The color of the t-shirt") color: String,
        @P("The size of the t-shirt") size: String
    ): String {
        return "100 $color $size T-shirts in stock"
    }

    @Tool("Send an email to a customer with order confirmation")
    fun sendEmail(
        @P("Customer email address") email: String,
        @P("Email subject") subject: String,
        @P("Email body") body: String
    ): String {
        return "Email sent to $email with subject: $subject"
    }
}
