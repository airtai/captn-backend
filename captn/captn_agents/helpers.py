from contextlib import asynccontextmanager
from os import environ
from typing import Any, Callable, Optional

from prisma import Prisma  # type: ignore[attr-defined]


def retry_context_manager(num_retries: int = 3) -> Callable[[Any], Any]:  # type: ignore
    def _retry_context_manager(context_manager: Any) -> Any:
        @asynccontextmanager
        async def retry_on_fail(
            context_manager: Any = context_manager,
            num_retries: int = num_retries,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            for i in range(num_retries):
                try:
                    async with context_manager(*args, **kwargs) as ret_val:  # type: ignore
                        yield ret_val
                        break
                except Exception as e:
                    print(f"Caught exception {e} on attempt {i}")
                    if i == num_retries - 1:
                        raise e

        return retry_on_fail

    return _retry_context_manager


@retry_context_manager(num_retries=3)  # type: ignore
@asynccontextmanager  # type: ignore
async def get_db_connection(db_url: Optional[str] = None) -> Prisma:  # type: ignore
    if not db_url:
        db_url = environ.get("DATABASE_URL")
    if "connect_timeout" not in db_url:  # type: ignore
        db_url += "?connect_timeout=60"  # type: ignore
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
    if "connect_timeout" not in wasp_db_url:  # type: ignore
        wasp_db_url += "?connect_timeout=60"
    return wasp_db_url
