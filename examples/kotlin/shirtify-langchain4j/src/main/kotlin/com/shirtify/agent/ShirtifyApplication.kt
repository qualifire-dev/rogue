package com.shirtify.agent

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class ShirtifyApplication

fun main(args: Array<String>) {
    runApplication<ShirtifyApplication>(*args)
}
