from typing import Generator, Tuple

from datasets import (
    Dataset,
    load_dataset,
    DatasetDict,
    IterableDatasetDict,
    IterableDataset,
)

from ...config import Config


class PromptInjectionTool:
    def __init__(self) -> None:
        self._dataset: Dataset = None

    def _load_dataset(self, dataset_name: str) -> None:
        dataset_dict = load_dataset(dataset_name)

        if isinstance(dataset_dict, (DatasetDict, IterableDatasetDict)):
            if "test" in dataset_dict.keys():
                self._dataset = dataset_dict["test"]
            else:
                dataset_key = list(dataset_dict.keys())[0]
                self._dataset = dataset_dict[dataset_key]
        elif isinstance(dataset_dict, (Dataset, IterableDataset)):
            self._dataset = dataset_dict
        else:
            raise ValueError("Invalid dataset")

    def _yield_next_prompt_and_label(
        self,
    ) -> Generator[Tuple[str, str], None, None]:
        for item in self._dataset:
            prompt = item[Config.Tools.PromptInjection.DATASET_PROMPT_KEY_NAME]
            label = item[Config.Tools.PromptInjection.DATASET_LABEL_KEY_NAME]

            if not isinstance(prompt, list) and not isinstance(label, list):
                yield prompt, label
                continue

            for i in range(min(len(prompt), len(label))):
                yield prompt[i], label[i]

    def run(self):
        self._load_dataset(Config.Tools.PromptInjection.DATASET)
