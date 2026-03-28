# SmartDiscover

MVP backend untuk SmartDiscover (Multi-Agent Music Discovery Assistant) dengan alur:
1. Profiler Agent
2. Spotify Search Agent
3. Filter and Ranker Agent
4. Presenter Agent

## Fitur MVP
- Endpoint `POST /recommend` dengan output full JSON schema siap konsumsi API
- Endpoint `GET /health`
- Endpoint `GET /spotify/health`
- Endpoint `GET /llm/health`
- Dashboard web Vanilla JS di root path `/`
- Fallback mock candidate jika kredensial Spotify belum tersedia
- Profiler dan Ranker berjalan LLM-first via OpenRouter dengan fallback heuristik
- Tidak menggunakan endpoint Spotify deprecated (`/audio-features`, `/recommendations`)

## Setup
1. Buat virtual environment
2. Install dependency
3. Salin `.env.example` menjadi `.env`
4. Jalankan server

Contoh perintah PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Setelah server jalan, buka dashboard:
- http://127.0.0.1:8000/

Endpoint docs tetap tersedia di:
- http://127.0.0.1:8000/docs

## Contoh Request

```http
POST /recommend
Content-Type: application/json

{
  "text": "aku mau lagu buat belajar malam yang tenang dan fokus",
  "target_count": 15
}
```

## Contoh Response (ringkas)
```json
{
  "summary": {
    "input_language": "id",
    "intent_text": "aku mau lagu buat belajar malam yang tenang dan fokus",
    "target_count": 15,
    "returned_count": 15
  },
  "intent_profile": {
    "mood": "calm",
    "activity": "studying",
    "genre": ["lo-fi"],
    "energy": "low",
    "language": "id"
  },
  "query_strategy": {
    "variants": ["calm studying", "studying low"],
    "broadening_applied": false,
    "notes": "..."
  },
  "recommendations": [
    {
      "rank": 1,
      "title": "Midnight Focus",
      "artist": "Loftline",
      "spotify_url": "",
      "preview_url": "",
      "why": "Cocok untuk studying dengan nuansa calm dan energi low.",
      "score": 0.4123
    }
  ],
  "quality_notes": {
    "deduplicated": true,
    "fallback_used": false,
    "fallback_reason": ""
  }
}
```

## Catatan Integrasi Spotify
Isi variabel berikut pada `.env` agar search benar-benar memanggil Spotify:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

## Catatan Integrasi OpenRouter
Isi variabel berikut pada `.env` untuk mengaktifkan LLM multi-agent:
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` (default: `google/gemini-2.5-flash-lite`)
- `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)

Jika API key tidak ada atau request gagal, pipeline otomatis fallback ke mode heuristik.
