"""Single-instance demo access control and a global model-spend ceiling."""
import base64
import secrets
import time
from collections import deque
from threading import Lock
from fastapi.responses import JSONResponse
from .config import settings

class GenerationGate:
    def __init__(self):
        self.lock = Lock()
        self.events = deque()
        self.active = False

    def enter(self, limit):
        with self.lock:
            current = time.monotonic()
            while self.events and self.events[0] <= current - 3600:
                self.events.popleft()
            if self.active:
                return 'Another response is being generated. Please try again shortly.'
            if len(self.events) >= limit:
                return 'The hourly generation limit has been reached. Please try again later.'
            self.events.append(current)
            self.active = True
            return None

    def leave(self):
        with self.lock:
            self.active = False

gate = GenerationGate()

def authorized(header, cfg):
    try:
        scheme, value = header.split(' ', 1)
        if scheme.lower() != 'basic':
            return False
        user, password = base64.b64decode(value, validate=True).decode().split(':', 1)
        return secrets.compare_digest(user.encode(), cfg.access_username.encode()) and secrets.compare_digest(password.encode(), cfg.access_password.encode())
    except (ValueError, UnicodeError):
        return False

async def protect(request, call_next):
    cfg = settings()
    if request.url.path == '/api/health/live':
        return await call_next(request)
    if cfg.access_password and not authorized(request.headers.get('authorization', ''), cfg):
        return JSONResponse({'error': {'code': 'access_required', 'message': 'Sign in with the reviewer credentials.'}}, 401,
            headers={'WWW-Authenticate': 'Basic realm="Lenny Research Studio", charset="UTF-8"', 'Cache-Control': 'no-store'})
    generation = request.method == 'POST' and request.url.path.startswith('/api/sessions/') and request.url.path.endswith('/messages')
    if not generation:
        return await call_next(request)
    reason = gate.enter(cfg.generation_requests_per_hour)
    if reason:
        return JSONResponse({'error': {'code': 'generation_limit', 'message': reason}}, 429, headers={'Retry-After': '60'})
    try:
        return await call_next(request)
    finally:
        gate.leave()
