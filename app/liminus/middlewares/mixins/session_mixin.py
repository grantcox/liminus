import json
from dataclasses import dataclass
from http.cookies import SimpleCookie
from secrets import token_urlsafe
from time import time
from typing import Optional, Tuple

from starlette.requests import Request
from starlette.responses import Response

from liminus.redis_client import redis_client
from liminus.settings import logger
from liminus.utils import get_cache_hash_key, to_seconds


@dataclass
class Session:
    session_id: str
    session_data: Optional[dict]


class SessionHandlerMixin:
    SESSION_KEY_PREFIX = ''
    SESSION_ID_COOKIE_NAME = ''
    SESSION_COOKIE_DOMAIN = ''

    SESSION_IDLE_TIMEOUT_SECONDS = to_seconds(minutes=30)
    SESSION_STRICT_MAX_LIFETIME_SECONDS = to_seconds(hours=24)

    async def _ensure_session(self, request: Request) -> Tuple[Session, bool]:
        # if the request has no session cookie specified, or it's an invalid session id, create a new one
        session = await self._load_session(request)

        is_new = False
        if session.session_data is None:
            is_new = True
            session.session_data = {'strict_expiry': int(time()) + self.SESSION_STRICT_MAX_LIFETIME_SECONDS}

        return session, is_new

    async def _load_session(self, request: Request) -> Session:
        session_id = self._get_session_id(request)
        session_data = await self._load_session_from_cache(session_id)

        # our sessions have a 'strict expiry', which ensures there is a max lifetime even if something
        # is keeping active requests going
        if session_data:
            strict_expiry = int(session_data.get('strict_expiry', 0))
            if strict_expiry < time():
                # this session needs to be invalidated
                logger.info(f'session {session_id} has expired, invalidating')
                await self._store_session(session_id, None)
                session_data = None

        return Session(session_id, session_data)

    async def _store_session(self, *args):
        if isinstance(args[0], Session):
            session_id, session_data = args[0].session_id, args[0].session_data
        else:
            session_id, session_data = args[0], args[1]

        await self._store_session_in_cache(session_id, self.SESSION_IDLE_TIMEOUT_SECONDS, session_data)

    def _get_session_id(self, request):
        cookies = self._get_cookies(request)
        return cookies[self.SESSION_ID_COOKIE_NAME] if self.SESSION_ID_COOKIE_NAME in cookies else None

    def _get_session_redis_key(self, session_id: str) -> str:
        # Use a hash of the session id, so even if someone could access Redis they couldn't swap sessions
        return get_cache_hash_key(self.SESSION_KEY_PREFIX, session_id)

    async def _store_session_in_cache(self, session_id: str, exp: int, data: Optional[dict]):
        key = self._get_session_redis_key(session_id)
        encoded_data = json.dumps(data)
        await redis_client().setex(key, exp, encoded_data)

    async def _load_session_from_cache(self, session_id: str) -> Optional[dict]:
        if not session_id:
            return None
        key = self._get_session_redis_key(session_id)
        encoded_data = await redis_client().get(key)
        return json.loads(encoded_data) if encoded_data else None

    def _generate_unique_session_id(self) -> str:
        return token_urlsafe(32)

    def _append_session_cookie_to_response(self, response: Response, session_id: str, age: Optional[int] = None):
        new_cookie = self._build_cookie(session_id, age)

        # We want to append this new cookie rather than setting, as one response can set multiple cookies
        response.headers.append('Set-Cookie', new_cookie)

    def _append_session_cookie_to_request(self, request: Request, session_id: str, age: Optional[int] = None):
        new_cookie = self._build_cookie(session_id, age)

        # We want to append this new cookie rather than setting, as one response can set multiple cookies
        request.state.headers.append('Set-Cookie', new_cookie)

    def _build_cookie(self, session_id: str, age: Optional[int] = None) -> str:
        # if age is None, it's a true session cookie, eg the browser will remove it when the tab is closed
        # if age is set, it's a persistent cookie with the given lifetime
        age_clause = '' if age is None else f'Max-Age={str(age)}; '
        return (
            f'{self.SESSION_ID_COOKIE_NAME}={session_id}; '
            f'Domain={self.SESSION_COOKIE_DOMAIN}; {age_clause} '
            'Path=/; secure; HttpOnly; SameSite=Lax'
        )

    def _get_cookies(self, request: Request) -> dict:
        cookies_header = request.headers.get('Cookie', '')
        return self._parse_cookie_header(cookies_header)

    def _parse_cookie_header(self, cookie_header_value: str) -> dict:
        if not cookie_header_value:
            return {}

        cookie: SimpleCookie = SimpleCookie()
        cookie.load(cookie_header_value)

        cookies = {key: morsel.value for key, morsel in cookie.items()}
        return cookies
