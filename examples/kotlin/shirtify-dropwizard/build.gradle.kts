plugins {
    kotlin("jvm") version "1.9.25"
    application
    id("com.github.johnrengelman.shadow") version "8.1.1"
}

group = "com.shirtify"
version = "1.0.0"

application {
    mainClass.set("com.shirtify.agent.ShirtifyApplicationKt")
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(17)
    }
}

repositories {
    mavenCentral()
}

val dropwizardVersion = "4.0.7"
val langchain4jVersion = "1.11.0"

dependencies {
    // Dropwizard
    implementation("io.dropwizard:dropwizard-core:$dropwizardVersion")

    // LangChain4j (core, no Spring Boot starters)
    implementation("dev.langchain4j:langchain4j:$langchain4jVersion")
    implementation("dev.langchain4j:langchain4j-open-ai:$langchain4jVersion")
    implementation("dev.langchain4j:langchain4j-kotlin:$langchain4jVersion")

    // Kotlin
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.17.2")
    implementation("org.jetbrains.kotlin:kotlin-reflect")

    // Test
    testImplementation("io.dropwizard:dropwizard-testing:$dropwizardVersion")
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict")
        javaParameters = true  // Required for LangChain4j tool parameter names
    }
}

tasks.withType<Test> {
    useJUnitPlatform()
}

tasks.named<com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar>("shadowJar") {
    archiveBaseName.set("shirtify-dropwizard")
    archiveClassifier.set("")
    archiveVersion.set("")
    mergeServiceFiles()
    manifest {
        attributes["Main-Class"] = "com.shirtify.agent.ShirtifyApplicationKt"
    }
}
