import os


class Config:
    class HuggingFace:
        TOKEN = os.getenv("HUGGINGFACE_TOKEN")

    class EvaluatorAgent:
        MODEL = os.getenv("EVALUATOR_AGENT_MODEL", "gpt-4o")

    class Tools:
        class PromptInjection:
            DATASET = os.getenv(
                "PROMPT_INJECTION_DATASET",
                "qualifire/Qualifire-prompt-injection-benchmark",
            )
            DATASET_PROMPT_KEY_NAME = os.getenv(
                "PROMPT_INJECTION_DATASET_PROMPT_KEY_NAME",
                "text",
            )
            DATASET_LABEL_KEY_NAME = os.getenv(
                "PROMPT_INJECTION_DATASET_LABEL_KEY_NAME",
                "label",
            )
