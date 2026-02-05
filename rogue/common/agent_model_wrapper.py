from functools import lru_cache
from typing import TYPE_CHECKING, Optional

from loguru import logger

if TYPE_CHECKING:
    from google.adk.models import BaseLlm


def _normalize_azure_endpoint(api_base: str, model: str) -> str:
    """Strip trailing path segments that litellm appends itself.

    Users may enter ``https://myresource.openai.azure.com/openai/v1/chat/completions``
    but litellm already appends ``/chat/completions``.  We strip only that
    suffix so the valid ``/openai/v1`` base path is preserved.
    """

    if not model.startswith("azure/"):
        return api_base

    deployment_name = model.split("/")[-1]

    return f"{api_base}/openai/deployments/{deployment_name}"


@lru_cache()
def get_llm_from_model(
    model: str,
    llm_auth: Optional[str] = None,
    api_base: Optional[str] = None,
    api_version: Optional[str] = None,
) -> "BaseLlm":
    # adk imports take a while, importing them here to reduce rogue startup time.
    from google.adk.models import LLMRegistry
    from google.adk.models.lite_llm import LiteLlm

    try:
        llm_cls = LLMRegistry.resolve(model)
    except ValueError:
        logger.debug(
            f"Model {model} not found in LLMRegistry, using LiteLlm",
            extra={"model": model},
        )
        llm_cls = LiteLlm

    if llm_cls is LiteLlm:
        kwargs = {}
        if llm_auth:
            kwargs["api_key"] = llm_auth
        if api_base:
            api_base = _normalize_azure_endpoint(api_base, model)
            kwargs["api_base"] = api_base
        if api_version:
            kwargs["api_version"] = api_version
        logger.info(
            f"Creating LiteLlm for model={model}",
            extra={
                "api_base": api_base,
                "api_version": api_version,
                "has_api_key": bool(llm_auth),
            },
        )
        if kwargs:
            llm = LiteLlm(model=model, **kwargs)
            logger.debug(
                "LiteLlm instance created",
                extra={
                    "model": model,
                    "kwargs": {
                        k: v if k != "api_key" else "***" for k, v in kwargs.items()
                    },
                    "additional_args": getattr(llm, "_additional_args", {}),
                },
            )
            return llm

    return llm_cls(model=model)
