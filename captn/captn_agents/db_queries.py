from typing import Optional, Union

from prisma.models import UserInitialTeam

from .helpers import get_db_connection


async def get_initial_team(user_id: Union[int, str]) -> Optional[UserInitialTeam]:
    async with get_db_connection() as db:
        user_initial_team = await db.userinitialteam.find_first(
            where={"user_id": int(user_id)}, include={"initial_team": True}
        )

    return user_initial_team
