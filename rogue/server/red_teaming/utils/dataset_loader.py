"""
Dataset loader utility for advanced prompt injection sources.
"""

import re
from typing import List, Optional

import requests
from loguru import logger

# Constants
L1B3RT4S_URL = (
    "https://raw.githubusercontent.com/elder-plinius/L1B3RT4S/main/OPENAI.mkd"
)
QUALIFIRE_DATASET_NAME = "qualifire/prompt-injections-benchmark"


class DatasetLoader:
    """Loader for external prompt injection datasets."""

    _l1b3rt4s_cache: Optional[List[str]] = None
    _qualifire_cache: Optional[List[str]] = None

    @classmethod
    def get_l1b3rt4s_prompts(cls) -> List[str]:
        """
        Fetch and parse prompts from L1B3RT4S repository.

        Returns:
            List of prompt templates containing {Z} or {user_input} placeholders.
        """
        if cls._l1b3rt4s_cache is not None:
            return cls._l1b3rt4s_cache

        try:
            response = requests.get(L1B3RT4S_URL, timeout=10)
            response.raise_for_status()
            content = response.text

            prompts = []
            # Split by headers to separate different prompts
            sections = re.split(r"^#\s+.*$", content, flags=re.MULTILINE)

            for section in sections:
                if not section.strip():
                    continue

                # Basic heuristic: if it contains the placeholder,
                # it's likely a template
                # The repo uses {Z} and {user_input} as placeholders
                if "{Z}" in section or "{user_input}" in section:
                    # Clean up the section
                    cleaned = section.strip()
                    if len(cleaned) > 50:  # meaningful length
                        prompts.append(cleaned)

            logger.info(f"Loaded {len(prompts)} prompts from L1B3RT4S")
            cls._l1b3rt4s_cache = prompts
            return prompts

        except Exception as e:
            logger.warning(f"Failed to load L1B3RT4S prompts: {e}")
            return []

    @classmethod
    def get_qualifire_prompts(cls, sample_size: int = 100) -> List[str]:
        """
        Fetch prompts from Qualifire dataset.

        Args:
            sample_size: Number of samples to load (to avoid memory issues)

        Returns:
            List of jailbreak prompts.
        """
        if cls._qualifire_cache is not None:
            return cls._qualifire_cache

        try:
            # datasets import takes a while, import locally
            from datasets import load_dataset

            # Try loading 'test' split, fallback to 'train' if needed
            try:
                dataset = load_dataset(QUALIFIRE_DATASET_NAME, split="test")
            except Exception:
                # Fallback or retry with different split if 'test' fails
                dataset = load_dataset(QUALIFIRE_DATASET_NAME, split="train")

            # Filter for jailbreak label
            # Assuming label column exists and 'jailbreak' is the target value
            # Based on user info: "label" == "jailbreak"
            jailbreaks = dataset.filter(lambda x: x["label"] == "jailbreak")

            # Take a sample
            prompts = []
            count = 0
            for item in jailbreaks:
                if count >= sample_size:
                    break
                prompts.append(item["text"])
                count += 1

            logger.info(f"Loaded {len(prompts)} prompts from Qualifire")
            cls._qualifire_cache = prompts
            return prompts

        except Exception as e:
            logger.warning(f"Failed to load Qualifire prompts: {e}")
            return []

    @classmethod
    def get_all_prompts(cls) -> List[str]:
        """Get all available advanced prompts."""
        prompts = []
        prompts.extend(cls.get_l1b3rt4s_prompts())
        prompts.extend(cls.get_qualifire_prompts())
        return prompts
