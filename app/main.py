from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import RecommendRequest, RecommendResponse
from app.services.pipeline import RecommendationPipeline


app = FastAPI(title="SmartDiscover API", version="0.1.0")
pipeline = RecommendationPipeline()
app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse("web/index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "smartdiscover-api"}


@app.get("/spotify/health")
async def spotify_health() -> dict:
    status = await pipeline.spotify.health_check()
    return {"service": "spotify", **status}


@app.get("/llm/health")
async def llm_health() -> dict:
    status = await pipeline.llm.health_check()
    return {"service": "openrouter", "model": pipeline.llm.model, **status}


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(payload: RecommendRequest) -> RecommendResponse:
    return await pipeline.run(payload)
