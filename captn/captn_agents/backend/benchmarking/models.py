from enum import Enum

__all__ = ("Models",)


class Models(str, Enum):
    gpt3_5: str = "gpt3-5"
    gpt4: str = "gpt4"
    gpt4o: str = "gpt4o"
