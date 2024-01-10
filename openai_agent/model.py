from typing import List, Literal

from pydantic import BaseModel


class SmartSuggestions(BaseModel):
    suggestions: List[str]
    type: Literal["oneOf", "manyOf"]
