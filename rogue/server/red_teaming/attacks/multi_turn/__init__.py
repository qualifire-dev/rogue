"""
Multi-turn adversarial attack strategies - Free tier only.

Premium multi-turn attacks (GOAT, Crescendo, Simba, etc.) are handled
by the Deckard premium service.
"""

from .social_engineering_prompt_extraction import SocialEngineeringPromptExtraction

__all__ = [
    "SocialEngineeringPromptExtraction",
]
