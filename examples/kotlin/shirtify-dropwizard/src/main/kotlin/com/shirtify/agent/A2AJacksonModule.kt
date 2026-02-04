package com.shirtify.agent

import com.fasterxml.jackson.core.JsonGenerator
import com.fasterxml.jackson.core.JsonParser
import com.fasterxml.jackson.databind.*
import com.fasterxml.jackson.databind.module.SimpleModule
import io.a2a.spec.*

/**
 * Jackson module that bridges the A2A Java SDK spec types (designed for Gson)
 * with Dropwizard's Jackson-based serialization.
 *
 * Handles:
 * - Part<?> polymorphism using "kind" discriminator field
 * - AgentCard serialization with backward-compatible "url" field for rogue TUI
 * - TaskState enum wire format
 */
class A2AJacksonModule : SimpleModule("A2AJacksonModule") {

    init {
        // Part serialization/deserialization
        addSerializer(TextPart::class.java, PartSerializer.TextPartSerializer())
        addSerializer(DataPart::class.java, PartSerializer.DataPartSerializer())
        addSerializer(Part::class.java, PartSerializer())
        addDeserializer(Part::class.java, PartDeserializer())

        // AgentCard with backward-compatible url field
        addSerializer(AgentCard::class.java, AgentCardSerializer())

        // TaskState enum wire format
        addSerializer(TaskState::class.java, TaskStateSerializer())
        addDeserializer(TaskState::class.java, TaskStateDeserializer())

        // TaskStatus serialization
        addSerializer(TaskStatus::class.java, TaskStatusSerializer())

        // Message serialization
        addSerializer(Message::class.java, MessageSerializer())

        // Message.Role enum
        addSerializer(Message.Role::class.java, MessageRoleSerializer())

        // Artifact serialization
        addSerializer(Artifact::class.java, ArtifactSerializer())

        // AgentSkill serialization
        addSerializer(AgentSkill::class.java, AgentSkillSerializer())

        // AgentCapabilities serialization
        addSerializer(AgentCapabilities::class.java, AgentCapabilitiesSerializer())
    }
}

// -- Part Serializers --

class PartSerializer : JsonSerializer<Part<*>>() {
    override fun serialize(value: Part<*>, gen: JsonGenerator, serializers: SerializerProvider) {
        when (value) {
            is TextPart -> TextPartSerializer().serialize(value, gen, serializers)
            is DataPart -> DataPartSerializer().serialize(value, gen, serializers)
            is FilePart -> {
                gen.writeStartObject()
                gen.writeStringField("kind", "file")
                gen.writeObjectField("file", value.file())
                gen.writeEndObject()
            }
            else -> {
                gen.writeStartObject()
                gen.writeStringField("kind", "unknown")
                gen.writeEndObject()
            }
        }
    }

    class TextPartSerializer : JsonSerializer<TextPart>() {
        override fun serialize(value: TextPart, gen: JsonGenerator, serializers: SerializerProvider) {
            gen.writeStartObject()
            gen.writeStringField("kind", "text")
            gen.writeStringField("text", value.text())
            gen.writeEndObject()
        }
    }

    class DataPartSerializer : JsonSerializer<DataPart>() {
        override fun serialize(value: DataPart, gen: JsonGenerator, serializers: SerializerProvider) {
            gen.writeStartObject()
            gen.writeStringField("kind", "data")
            gen.writeObjectField("data", value.data())
            gen.writeEndObject()
        }
    }
}

class PartDeserializer : JsonDeserializer<Part<*>>() {
    override fun deserialize(p: JsonParser, ctxt: DeserializationContext): Part<*> {
        val node = p.codec.readTree<JsonNode>(p)
        val kind = node.get("kind")?.asText()

        return when (kind) {
            "text", null -> {
                // Support both {"kind": "text", "text": "..."} and {"text": "..."}
                val text = node.get("text")?.asText() ?: ""
                TextPart(text)
            }
            "data" -> {
                val mapper = p.codec as ObjectMapper
                val data = mapper.convertValue(node.get("data"), Map::class.java)
                @Suppress("UNCHECKED_CAST")
                DataPart(data as Map<String, Any>)
            }
            "file" -> {
                // Basic file part support - parse as URI-based file
                val fileNode = node.get("file")
                val uri = fileNode?.get("uri")?.asText() ?: ""
                val mimeType = fileNode?.get("mimeType")?.asText()
                val name = fileNode?.get("name")?.asText()
                FilePart(FileWithUri(uri, mimeType, name))
            }
            else -> TextPart(node.get("text")?.asText() ?: "")
        }
    }
}

// -- AgentCard Serializer --

class AgentCardSerializer : JsonSerializer<AgentCard>() {
    override fun serialize(value: AgentCard, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeStartObject()

        gen.writeStringField("name", value.name())
        gen.writeStringField("description", value.description())
        gen.writeStringField("version", value.version())

        // Backward-compatible "url" field for rogue TUI
        // Extract from the first supportedInterface, or default
        val url = value.supportedInterfaces()
            ?.firstOrNull()
            ?.url()
            ?: "http://localhost:10004/"
        gen.writeStringField("url", url)

        // Standard SDK fields
        if (value.provider() != null) {
            gen.writeObjectField("provider", value.provider())
        }
        if (value.documentationUrl() != null) {
            gen.writeStringField("documentationUrl", value.documentationUrl())
        }
        if (value.iconUrl() != null) {
            gen.writeStringField("iconUrl", value.iconUrl())
        }

        // Capabilities
        gen.writeObjectFieldStart("capabilities")
        gen.writeBooleanField("streaming", value.capabilities().streaming())
        gen.writeBooleanField("pushNotifications", value.capabilities().pushNotifications())
        gen.writeBooleanField("stateTransitionHistory", value.capabilities().stateTransitionHistory())
        gen.writeEndObject()

        // defaultInputModes
        gen.writeArrayFieldStart("defaultInputModes")
        value.defaultInputModes()?.forEach { gen.writeString(it) }
        gen.writeEndArray()

        // defaultOutputModes
        gen.writeArrayFieldStart("defaultOutputModes")
        value.defaultOutputModes()?.forEach { gen.writeString(it) }
        gen.writeEndArray()

        // skills
        gen.writeArrayFieldStart("skills")
        value.skills()?.forEach { skill ->
            serializers.defaultSerializeValue(skill, gen)
        }
        gen.writeEndArray()

        gen.writeEndObject()
    }
}

// -- TaskState Serializer/Deserializer --

class TaskStateSerializer : JsonSerializer<TaskState>() {
    override fun serialize(value: TaskState, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeString(value.asString())
    }
}

class TaskStateDeserializer : JsonDeserializer<TaskState>() {
    override fun deserialize(p: JsonParser, ctxt: DeserializationContext): TaskState {
        return TaskState.fromString(p.text)
    }
}

// -- TaskStatus Serializer --

class TaskStatusSerializer : JsonSerializer<TaskStatus>() {
    override fun serialize(value: TaskStatus, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeStartObject()
        gen.writeStringField("state", value.state().asString())
        if (value.message() != null) {
            gen.writeObjectField("message", value.message())
        }
        if (value.timestamp() != null) {
            gen.writeStringField("timestamp", value.timestamp().toString())
        }
        gen.writeEndObject()
    }
}

// -- Message Serializer --

class MessageSerializer : JsonSerializer<Message>() {
    override fun serialize(value: Message, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeStartObject()
        gen.writeStringField("role", value.role().asString())
        gen.writeStringField("messageId", value.messageId())
        if (value.contextId() != null) {
            gen.writeStringField("contextId", value.contextId())
        }
        if (value.taskId() != null) {
            gen.writeStringField("taskId", value.taskId())
        }
        gen.writeStringField("kind", "message")

        gen.writeArrayFieldStart("parts")
        value.parts().forEach { part ->
            serializers.defaultSerializeValue(part, gen)
        }
        gen.writeEndArray()

        gen.writeEndObject()
    }
}

// -- Message.Role Serializer --

class MessageRoleSerializer : JsonSerializer<Message.Role>() {
    override fun serialize(value: Message.Role, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeString(value.asString())
    }
}

// -- Artifact Serializer --

class ArtifactSerializer : JsonSerializer<Artifact>() {
    override fun serialize(value: Artifact, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeStartObject()
        gen.writeStringField("artifactId", value.artifactId())
        if (value.name() != null) {
            gen.writeStringField("name", value.name())
        }
        if (value.description() != null) {
            gen.writeStringField("description", value.description())
        }

        gen.writeArrayFieldStart("parts")
        value.parts().forEach { part ->
            serializers.defaultSerializeValue(part, gen)
        }
        gen.writeEndArray()

        gen.writeEndObject()
    }
}

// -- AgentSkill Serializer --

class AgentSkillSerializer : JsonSerializer<AgentSkill>() {
    override fun serialize(value: AgentSkill, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeStartObject()
        gen.writeStringField("id", value.id())
        gen.writeStringField("name", value.name())
        gen.writeStringField("description", value.description())

        gen.writeArrayFieldStart("tags")
        value.tags()?.forEach { gen.writeString(it) }
        gen.writeEndArray()

        if (value.examples() != null) {
            gen.writeArrayFieldStart("examples")
            value.examples().forEach { gen.writeString(it) }
            gen.writeEndArray()
        }

        gen.writeEndObject()
    }
}

// -- AgentCapabilities Serializer --

class AgentCapabilitiesSerializer : JsonSerializer<AgentCapabilities>() {
    override fun serialize(value: AgentCapabilities, gen: JsonGenerator, serializers: SerializerProvider) {
        gen.writeStartObject()
        gen.writeBooleanField("streaming", value.streaming())
        gen.writeBooleanField("pushNotifications", value.pushNotifications())
        gen.writeBooleanField("stateTransitionHistory", value.stateTransitionHistory())
        gen.writeEndObject()
    }
}
