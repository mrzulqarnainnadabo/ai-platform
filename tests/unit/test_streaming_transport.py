import asyncio

from api.index import ProductAnalyticsMiddleware


async def _streaming_app(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/event-stream; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": b"data: one\\n\\n", "more_body": True})
    await send({"type": "http.response.body", "body": b"data: two\\n\\n", "more_body": False})


def test_pure_asgi_analytics_middleware_preserves_stream_frames_and_no_content_length():
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    async def run():
        middleware = ProductAnalyticsMiddleware(_streaming_app)
        await middleware(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/models/stream",
                "headers": [],
            },
            receive,
            send,
        )

    asyncio.run(run())

    start = messages[0]
    assert start["type"] == "http.response.start"
    assert not any(key == b"content-length" for key, _ in start["headers"])
    assert messages[1]["body"] == b"data: one\\n\\n"
    assert messages[2]["body"] == b"data: two\\n\\n"
    assert messages[2]["more_body"] is False
