from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class ChatHistory(BaseModel):
    messages: list[Message] = Field(default_factory=list)

    def add_message(self, message: Message):
        self.messages.append(message)
