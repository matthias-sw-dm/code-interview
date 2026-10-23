import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid7())
        start = time.perf_counter()

        logger.info("→ %s %s request_id=%s", request.method, request.url.path, request_id)

        response = await call_next(request)

        duration = time.perf_counter() - start
        logger.info(
            "← %s %s status=%d duration=%.3fs request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            request_id,
        )

        response.headers["X-Request-ID"] = request_id
        return response
