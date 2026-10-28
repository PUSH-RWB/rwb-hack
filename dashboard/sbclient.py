"""Минимальный клиент REST API Superset на стандартной библиотеке (без зависимостей)."""
import http.cookiejar
import json
import time
import urllib.error
import urllib.parse
import urllib.request


class Superset:
    def __init__(self, base, user, password):
        self.base = base.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.http = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        out = self._raw("POST", "/api/v1/security/login",
                        {"username": user, "password": password, "provider": "db", "refresh": True}, auth=False)
        self.token = out["access_token"]
        self.csrf = self._raw("GET", "/api/v1/security/csrf_token/")["result"]

    def _raw(self, method, path, body=None, auth=True):
        headers = {"Content-Type": "application/json", "Referer": self.base}
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["X-CSRFToken"] = getattr(self, "csrf", "")
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        for attempt in range(6):
            req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
            try:
                time.sleep(0.03)                      # Superset ограничивает API: 50 запросов в секунду
                with self.http.open(req, timeout=120) as resp:
                    raw = resp.read()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as err:
                if err.code == 429 and attempt < 5:
                    time.sleep(1.2)
                    continue
                raise RuntimeError(f"{method} {path} -> {err.code}: {err.read().decode()[:1500]}") from None

    def call(self, method, path, body=None):
        return self._raw(method, path, body)

    def find(self, resource, col, value, opr="eq"):
        """Список объектов по фильтру rison: ?q=(filters:!((col:..,opr:..,value:..)),page_size:100)"""
        q = f"(filters:!((col:{col},opr:{opr},value:'{value}')),page_size:100)"
        return self.call("GET", f"/api/v1/{resource}/?q=" + urllib.parse.quote(q, safe="(),:!'"))["result"]
