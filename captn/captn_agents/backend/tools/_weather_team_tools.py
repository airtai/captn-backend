from typing import Any, Dict

from ..toolboxes import Toolbox
from ._functions import REPLY_TO_CLIENT_DESCRIPTION, BaseContext, reply_to_client

__all__ = ("create_weather_team_toolbox",)


def create_weather_team_toolbox(
    user_id: int,
    conv_id: int,
    kwargs: Dict[str, Any],
) -> Toolbox:
    toolbox = Toolbox()

    context = BaseContext(
        user_id=user_id,
        conv_id=conv_id,
    )
    toolbox.set_context(context)

    toolbox.add_function(REPLY_TO_CLIENT_DESCRIPTION)(reply_to_client)

    return toolbox
