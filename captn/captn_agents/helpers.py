from contextlib import asynccontextmanager
from os import environ
from typing import Optional

from prisma import Prisma  # type: ignore[attr-defined]


@asynccontextmanager  # type: ignore
async def get_db_connection(db_url: Optional[str] = None) -> Prisma:  # type: ignore
    if not db_url:
        db_url = environ.get("DATABASE_URL")
    db = Prisma(datasource={"url": db_url})  # type: ignore
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()


async def get_wasp_db_url() -> str:
    curr_db_url = environ.get("DATABASE_URL")
    wasp_db_name = environ.get("WASP_DB_NAME", "waspdb")
    wasp_db_url = curr_db_url.replace(curr_db_url.split("/")[-1], wasp_db_name)  # type: ignore[union-attr]
    return wasp_db_url
