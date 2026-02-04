plugins {
    kotlin("jvm") version "2.3.0"
    application
    id("com.gradleup.shadow") version "9.0.0-beta12"
}

group = "com.shirtify"
version = "1.0.0"

application {
    mainClass.set("com.shirtify.agent.ShirtifyApplicationKt")
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(25)
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

    // A2A Protocol SDK (spec types only — no CDI/server dependencies)
    implementation("io.github.a2asdk:a2a-java-sdk-spec:1.0.0.Alpha1")

    // LangChain4j (core, no Spring Boot starters)
    implementation("dev.langchain4j:langchain4j:$langchain4jVersion")
    implementation("dev.langchain4j:langchain4j-open-ai:$langchain4jVersion")


    // dotenv
    implementation("io.github.cdimascio:dotenv-java:3.1.0")

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
    isZip64 = true
    archiveBaseName.set("shirtify-dropwizard")
    archiveClassifier.set("")
    archiveVersion.set("")
    mergeServiceFiles()
    manifest {
        attributes["Main-Class"] = "com.shirtify.agent.ShirtifyApplicationKt"
    }
}
