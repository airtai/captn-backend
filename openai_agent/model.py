from typing import List, Literal

from pydantic import BaseModel


class SmartSuggestions(BaseModel):
    suggestions: List[str]
    suggestions_type: Literal["Button", "Checkbox"]
