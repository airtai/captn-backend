from prometheus_client import Counter

WEBSOCKET_REQUESTS = Counter(
    "websocket_requests_total", "Total count of websocket requests"
)

WEBSOCKET_TOKENS = Counter("websocket_tokens_total", "Total count of websocket tokens")

PING_REQUESTS = Counter("ping_requests_total", "Total count of ping requests")
