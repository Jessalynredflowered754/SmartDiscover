import time
from typing import Any

import httpx

from app.config import settings
from app.models import IntentProfile, TrackCandidate


class SpotifyClient:
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    SEARCH_URL = "https://api.spotify.com/v1/search"

    def __init__(self) -> None:
        self._token: str = ""
        self._token_expiry: float = 0.0

    async def health_check(self) -> dict[str, Any]:
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            return {
                "status": "mock-mode",
                "ok": True,
                "details": "Spotify credentials belum diisi.",
            }

        try:
            token = await self._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    self.SEARCH_URL,
                    params={"q": "focus", "type": "track", "limit": 1, "market": "ID"},
                    headers=headers,
                )
            if resp.status_code != 200:
                return {
                    "status": "spotify-error",
                    "ok": False,
                    "details": f"Spotify search failed with status {resp.status_code}.",
                }
            total = resp.json().get("tracks", {}).get("total", 0)
            return {
                "status": "ok",
                "ok": True,
                "details": f"Spotify reachable, total sample tracks: {total}.",
            }
        except Exception as exc:
            return {
                "status": "spotify-exception",
                "ok": False,
                "details": str(exc),
            }

    async def search_tracks(self, profile: IntentProfile, target_count: int) -> tuple[list[TrackCandidate], dict[str, Any]]:
        variants = self._build_query_variants(profile)
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            return self._mock_tracks(profile, target_count), {
                "variants": variants,
                "broadening_applied": False,
                "notes": "Spotify credentials belum diisi, menggunakan mock candidates untuk bootstrap development.",
            }

        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        candidates: list[TrackCandidate] = []
        for q in variants:
            params = {
                "q": q,
                "type": "track",
                "limit": min(10, max(5, target_count // 2)),
                "market": "ID",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(self.SEARCH_URL, params=params, headers=headers)
            if resp.status_code != 200:
                continue
            payload = resp.json()
            items = payload.get("tracks", {}).get("items", [])
            for item in items:
                candidates.append(
                    TrackCandidate(
                        title=item.get("name", ""),
                        artist=", ".join(a.get("name", "") for a in item.get("artists", [])),
                        spotify_url=item.get("external_urls", {}).get("spotify", ""),
                        preview_url=item.get("preview_url") or "",
                        popularity=item.get("popularity", 0),
                    )
                )

        broadening_applied = False
        if len(candidates) < target_count:
            broadening_applied = True
            broad_q = f"{profile.mood} music"
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    self.SEARCH_URL,
                    params={"q": broad_q, "type": "track", "limit": target_count, "market": "ID"},
                    headers=headers,
                )
            if resp.status_code == 200:
                items = resp.json().get("tracks", {}).get("items", [])
                for item in items:
                    candidates.append(
                        TrackCandidate(
                            title=item.get("name", ""),
                            artist=", ".join(a.get("name", "") for a in item.get("artists", [])),
                            spotify_url=item.get("external_urls", {}).get("spotify", ""),
                            preview_url=item.get("preview_url") or "",
                            popularity=item.get("popularity", 0),
                        )
                    )

        return candidates, {
            "variants": variants,
            "broadening_applied": broadening_applied,
            "notes": "Search menggunakan endpoint /search dengan fallback broad query.",
        }

    async def _get_access_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expiry:
            return self._token

        data = {"grant_type": "client_credentials"}
        auth = (settings.spotify_client_id, settings.spotify_client_secret)
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(self.TOKEN_URL, data=data, auth=auth)

        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        self._token_expiry = now + int(body.get("expires_in", 3600)) - 60
        return self._token

    def _build_query_variants(self, profile: IntentProfile) -> list[str]:
        genres = profile.genre or ["music"]
        base = [
            f"{profile.mood} {profile.activity}",
            f"{profile.activity} {profile.energy}",
            f"{profile.mood} playlist",
        ]
        base.extend(f"{g} {profile.activity}" for g in genres[:3])
        # Keep variants unique while preserving order.
        return list(dict.fromkeys(base))[:6]

    def _mock_tracks(self, profile: IntentProfile, target_count: int) -> list[TrackCandidate]:
        seed = [
            ("Midnight Focus", "Loftline"),
            ("Rainy Notes", "Ambaris"),
            ("Quiet Orbit", "Nexa Tone"),
            ("Paper and Coffee", "Sore Hari"),
            ("Blue Window", "Tala River"),
            ("Gentle Pulse", "Mono Atelier"),
            ("City at 2AM", "Sleepwalker Unit"),
            ("Clouded Desk", "Lentera"),
            ("Far Lamp", "North Avenue"),
            ("After Class", "Nadi Muda"),
            ("Nocturnal Study", "Pilot Frames"),
            ("Ambient Roof", "Sky Thread"),
            ("Warm Neon", "Satelit"),
            ("Soft Sprint", "Morning Gear"),
            ("Slow Horizon", "Kroma"),
            ("Paper Crane", "Aster"),
            ("Evening Byte", "Delta Echo"),
            ("Static Bloom", "Ruang Nada"),
            ("Northbound", "June Atlas"),
            ("Quiet Street", "Rinai"),
        ]

        items: list[TrackCandidate] = []
        for i, (title, artist) in enumerate(seed[: max(target_count + 5, 20)]):
            items.append(
                TrackCandidate(
                    title=title,
                    artist=artist,
                    spotify_url="",
                    preview_url="",
                    popularity=max(10, 100 - (i * 4)),
                    score=0.0,
                )
            )
        return items
