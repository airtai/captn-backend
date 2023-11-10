from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

import google_ads
import openai_agent

app = FastAPI()
app.include_router(openai_agent.router, tags=["OpenAI"])
app.include_router(google_ads.router, tags=["Google Ads"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
