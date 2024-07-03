from typing import Any, Union

from .helpers import get_db_connection


async def get_initial_team(user_id: Union[int, str]) -> Any:
    async with get_db_connection() as db:
        query = f"""SELECT
    uit.id AS user_initial_team_id,
    uit.user_id,
    it.id AS initial_team_id,
    it.name AS initial_team_name,
    it.smart_suggestions
FROM
    "UserInitialTeam" uit
JOIN
    "InitialTeam" it ON uit.initial_team_id = it.id
WHERE
    uit.user_id = {int(user_id)}"""  # nosec: [B608]
        user_initial_team = await db.query_first(query)

    return user_initial_team
