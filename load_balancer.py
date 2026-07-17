import asyncio
import os
from dataclasses import dataclass

import httpx
from fastapi import FastAPI, HTTPException, Request, Response


DEFAULT_BACKENDS = (
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
)
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def load_backends() -> list[str]:
    configured = os.getenv("LATTICE_BACKENDS")

    if not configured:
        return list(DEFAULT_BACKENDS)

    backends = [
        backend.strip().rstrip("/")
        for backend in configured.split(",")
        if backend.strip()
    ]

    if not backends:
        raise RuntimeError("LATTICE_BACKENDS must include at least one backend URL")

    return backends


@dataclass
class RoundRobinPool:
    backends: list[str]
    index: int = 0

    def __post_init__(self):
        self._lock = asyncio.Lock()

    async def next_backend(self) -> str:
        async with self._lock:
            backend = self.backends[self.index % len(self.backends)]
            self.index += 1
            return backend


backend_pool = RoundRobinPool(load_backends())
app = FastAPI(title="Lattice Load Balancer", version="0.1.0")


@app.get("/lb/health")
def load_balancer_health():
    return {
        "status": "OK",
        "strategy": "round_robin",
        "backends": backend_pool.backends,
    }


@app.get("/lb/backends")
def list_backends():
    return {
        "backends": backend_pool.backends,
    }


def proxy_request_headers(request: Request, backend: str) -> dict[str, str]:
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }
    forwarded_for = request.client.host if request.client else ""

    if request.headers.get("x-forwarded-for"):
        forwarded_for = f"{request.headers['x-forwarded-for']}, {forwarded_for}"

    headers["x-forwarded-for"] = forwarded_for
    headers["x-forwarded-proto"] = request.url.scheme
    headers["x-lattice-backend"] = backend
    return headers


def proxy_response_headers(response: httpx.Response) -> dict[str, str]:
    return {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
        and key.lower() not in {"content-length", "content-encoding"}
    }


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy(path: str, request: Request):
    backend = await backend_pool.next_backend()
    target_url = httpx.URL(f"{backend}/{path}").copy_with(
        query=request.url.query.encode("utf-8")
    )

    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=300.0) as client:
            backend_response = await client.request(
                method=request.method,
                url=target_url,
                content=await request.body(),
                headers=proxy_request_headers(request, backend),
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Backend {backend} is unavailable: {exc}",
        ) from exc

    return Response(
        content=backend_response.content,
        status_code=backend_response.status_code,
        headers=proxy_response_headers(backend_response),
        media_type=backend_response.headers.get("content-type"),
    )
