from __future__ import annotations

from urllib.parse import urljoin

import httpx


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: float = 20) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self._client = httpx.Client(timeout=timeout_seconds, follow_redirects=True)

    def build_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self._client.get(self.build_url(path), **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self._client.post(self.build_url(path), **kwargs)

    def close(self) -> None:
        self._client.close()
