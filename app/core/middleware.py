"""Middleware untuk penanganan request_id pada setiap request yang masuk."""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Memastikan setiap request memiliki request_id unik untuk pelacakan end-to-end."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Gunakan header X-Request-ID jika disediakan oleh pemanggil (backend),
        # atau buat UUID baru jika belum ada.
        req_id = request.headers.get("X-Request-ID")
        if not req_id or not req_id.strip():
            req_id = str(uuid.uuid4())

        # Pasang di state request dan contextvar
        request.state.request_id = req_id
        token = request_id_ctx.set(req_id)

        try:
            response = await call_next(request)
            # Selalu sertakan header X-Request-ID pada response
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)
