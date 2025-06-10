from functools import lru_cache

from google.adk.models import LLMRegistry, BaseLlm
from google.adk.models.lite_llm import LiteLlm
from loguru import logger


@lru_cache()
def get_llm_from_model(model: str) -> BaseLlm:
    try:
        llm_cls = LLMRegistry.resolve(model)
    except ValueError:
        logger.debug(
            f"Model {model} not found in LLMRegistry, using LiteLlm",
            extra={"model": model},
        )
        llm_cls = LiteLlm

    return llm_cls(model=model)
