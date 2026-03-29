from app.services.spotify_client import SpotifyClient


def test_extract_preview_from_embed_html_returns_url() -> None:
    html = """
    <html>
      <head></head>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{"state":{"data":{"entity":{"audioPreview":{"url":"https://p.scdn.co/mp3-preview/abc123"}}}}}}}
        </script>
      </body>
    </html>
    """

    preview = SpotifyClient._extract_preview_from_embed_html(html)

    assert preview == "https://p.scdn.co/mp3-preview/abc123"


def test_extract_preview_from_embed_html_returns_none_when_missing() -> None:
    html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{"state":{"data":{"entity":{}}}}}}
        </script>
      </body>
    </html>
    """

    preview = SpotifyClient._extract_preview_from_embed_html(html)

    assert preview is None
