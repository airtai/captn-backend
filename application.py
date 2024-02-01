from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

from captn.captn_agents.backend.daily_analysis_team import execute_daily_analysis

load_dotenv()

import captn.captn_agents  # noqa
import google_ads  # noqa
import openai_agent  # noqa


@asynccontextmanager  # type: ignore
async def lifespan(app: FastAPI) -> AsyncGenerator:  # type: ignore
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        execute_daily_analysis, "cron", minute="*/5"
    )  # second="*/59") # use hour="*/22" for production
    scheduler.start()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(openai_agent.router, prefix="/openai", tags=["OpenAI"])
app.include_router(google_ads.router, tags=["Google Ads"])
app.include_router(captn.captn_agents.router, tags=["Captn Agents"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)  # nosec [B104]
