from functools import lru_cache
from typing import Optional

from google.adk.models import LLMRegistry, BaseLlm
from google.adk.models.lite_llm import LiteLlm
from loguru import logger


@lru_cache()
def get_llm_from_model(
    model: str,
    llm_auth: Optional[str] = None,
) -> BaseLlm:
    try:
        llm_cls = LLMRegistry.resolve(model)
    except ValueError:
        logger.debug(
            f"Model {model} not found in LLMRegistry, using LiteLlm",
            extra={"model": model},
        )
        llm_cls = LiteLlm

    if llm_auth and llm_cls is LiteLlm:
        return LiteLlm(
            model=model,
            api_key=llm_auth,
            temperature=0.0,
        )

    return llm_cls(model=model)
