from fastapi import FastAPI

import google_ads_auth_service
import openai_agent

app = FastAPI()
app.include_router(openai_agent.router, tags=["OpenAI"])
app.include_router(google_ads_auth_service.router, tags=["Google Ads"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
