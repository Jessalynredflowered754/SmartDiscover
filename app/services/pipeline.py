import time

from app.config import settings
from app.models import RecommendRequest, RecommendResponse
from app.services.openrouter_client import OpenRouterClient
from app.services.presenter import PresenterAgent
from app.services.profiler import ProfilerAgent
from app.services.ranker import RankerAgent
from app.services.spotify_client import SpotifyClient


class RecommendationPipeline:
    def __init__(self) -> None:
        self.llm = OpenRouterClient()
        self.profiler = ProfilerAgent(self.llm)
        self.spotify = SpotifyClient()
        self.ranker = RankerAgent(self.llm)
        self.presenter = PresenterAgent()

    async def run(self, payload: RecommendRequest) -> RecommendResponse:
        started_at = time.perf_counter()
        top_k = payload.target_count or settings.top_k_default

        t0 = time.perf_counter()
        profile = await self.profiler.profile(payload.text)
        t1 = time.perf_counter()

        candidates, query_strategy = await self.spotify.search_tracks(profile, top_k)
        t2 = time.perf_counter()
        ranked = await self.ranker.rank(profile, candidates, top_k=top_k)
        t3 = time.perf_counter()
        presented = self.presenter.present(profile, ranked)
        t4 = time.perf_counter()

        fallback_used = len(ranked) < top_k
        fallback_reason = "" if not fallback_used else "Candidates kurang dari target_count setelah ranking."

        return RecommendResponse(
            summary={
                "input_language": profile.language,
                "intent_text": payload.text,
                "target_count": top_k,
                "returned_count": len(presented),
            },
            intent_profile=profile,
            query_strategy=query_strategy,
            recommendations=presented,
            quality_notes={
                "deduplicated": True,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "llm_profiler_used": self.profiler.last_used_llm,
                "llm_ranker_used": self.ranker.last_used_llm,
                "llm_enabled": self.llm.enabled,
                "stage_ms": {
                    "profiler": int((t1 - t0) * 1000),
                    "search": int((t2 - t1) * 1000),
                    "ranker": int((t3 - t2) * 1000),
                    "presenter": int((t4 - t3) * 1000),
                    "total": int((t4 - started_at) * 1000),
                },
            },
        )
