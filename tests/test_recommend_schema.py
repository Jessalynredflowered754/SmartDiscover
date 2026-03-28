from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_recommend_default_schema_and_count() -> None:
    response = client.post(
        "/recommend",
        json={"text": "aku mau lagu buat belajar malam yang tenang dan fokus"},
    )

    assert response.status_code == 200
    body = response.json()

    assert set(body.keys()) == {
        "summary",
        "intent_profile",
        "query_strategy",
        "recommendations",
        "quality_notes",
    }

    summary = body["summary"]
    recommendations = body["recommendations"]

    assert summary["target_count"] == 15
    assert summary["returned_count"] == len(recommendations)
    assert len(recommendations) == 15

    ranks = [item["rank"] for item in recommendations]
    assert ranks == sorted(ranks)
    assert ranks[0] == 1


def test_recommend_custom_target_count() -> None:
    response = client.post(
        "/recommend",
        json={"text": "energetic running mix", "target_count": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["summary"]["target_count"] == 5
    assert body["summary"]["returned_count"] == len(body["recommendations"])
    assert len(body["recommendations"]) == 5


def test_spotify_health_endpoint() -> None:
    response = client.get("/spotify/health")
    assert response.status_code == 200
    body = response.json()

    assert body["service"] == "spotify"
    assert "status" in body
    assert "ok" in body
    assert "details" in body
