from typing import List, Literal

from pydantic import BaseModel, Field
from typing_extensions import Annotated

suggestions_description = """List of quick replies which the client can use for replying to the incoming message.
These suggestions will be displayed to the client and he can click on them (the suggestions represents the clients replies to the message),
so never use word 'client' within the suggestions or "I need more information about your bussines", otherwise you will be penalized!
smart suggestions must contain explicit commands which the client can accept. e.g.: ["Yes", "No"].
Never suggest multiple (almost) similar suggestions. e.g.: ["Yes, I approve", "I approve"].
When you expect some headlines/keywords etc. from the client, you can use smart suggestions to suggest them,
and you should also add smart suggestion like "Can you please make some suggestions?".
It is always useful to suggest general smart suggestions like "Can you please make some suggestions?" or "Can you give me few examples?"
Also when the current task is finished, smart suggestions should suggest the next steps to the client.
Each smart suggestion should focus only on one thing. e.g.: "Update ad copy xy" is a good suggestion, but "Update ad copy xy and add new keywords yz" is not.
When you need to suggest keywords, hedlines, etc. Use 3+ suggestions, e.g.: ["Use headline x", "Use headline y", "Use headline z" ...] (with type 'manyOf')."""

type_description = """Type of the smart suggestions.
One of the following: Literal['oneOf', 'manyOf'].
If 'type' is 'oneOf', the client can click on only one suggestion.
If 'type' is 'manyOf', the client can click on multiple suggestions.
Use 'manyOf' for suggestions which are not mutually exclusive.
(e.g. ["Add keyword x", "Add keyword y"] or ['Suggest new headlines for the ad', 'Suggest new descriptions for the ad']).
Use 'oneOf' for suggestions which are mutually exclusive and for bigger tasks which require multiple steps.
(e.g. 'Add new keywords', 'Remove a keyword', 'Change match type', 'Optimize ad copy').
Also, use 'oneOf' when one of the suggestions is a question, e.g.: ["Can you please make some suggestions?"]."""


class SmartSuggestions(BaseModel):
    suggestions: Annotated[List[str], Field(..., description=suggestions_description)]
    type: Annotated[
        Literal["oneOf", "manyOf"], Field(..., description=type_description)
    ]
