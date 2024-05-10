import logging
from contextlib import asynccontextmanager
from os import environ
from typing import AsyncGenerator

# from apscheduler.schedulers.background import BackgroundScheduler
from autogen.io.websockets import IOWebsockets
from dotenv import load_dotenv
from fastapi import FastAPI

from captn.captn_agents.application import on_connect
from captn.captn_agents.backend.teams._daily_analysis_team import execute_daily_analysis
from captn.observability import PrometheusMiddleware, metrics, setting_otlp

load_dotenv()

import captn.captn_agents  # noqa
import google_ads  # noqa
import openai_agent  # noqa


APP_NAME = environ.get("APP_NAME", "fastapi-app")
OTLP_GRPC_ENDPOINT = environ.get("OTLP_GRPC_ENDPOINT", "http://tempo:4317")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:  # type: ignore
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(
    #     execute_daily_analysis, "cron", hour="5", minute="15"
    # )  # second="*/59")
    # scheduler.start()

    with IOWebsockets.run_server_in_thread(
        on_connect=on_connect,
        host="0.0.0.0",  # nosec [B104]
        port=8080,
    ) as uri:
        print(f"Websocket server started at {uri}.", flush=True)

        yield
    # yield


app = FastAPI(lifespan=lifespan)

# Setting metrics middleware
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

app.include_router(openai_agent.router, prefix="/openai", tags=["OpenAI"])
app.include_router(google_ads.router, tags=["Google Ads"])
app.include_router(captn.captn_agents.router, tags=["Captn Agents"])

# Setting OpenTelemetry exporter
setting_otlp(app, APP_NAME, OTLP_GRPC_ENDPOINT)


class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())





if __name__ == "__main__":
    import uvicorn

    # update uvicorn access logger format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"][
        "fmt"
    ] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"

    uvicorn.run(app, host="0.0.0.0", port=9000, log_config=log_config)  # nosec [B104]
