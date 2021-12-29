from typing import Any, List, Optional, Type

from pydantic import BaseModel

from liminus.constants import Headers, HttpMethods
from liminus.settings import config
from liminus.utils import path_matches, strip_path_prefix


class CorsSettings(BaseModel):
    # these settings will be passed directly to Starlette CorsMiddleware
    enable: bool = False
    allow_origins: List[str] = []
    allow_origin_regex: Optional[str] = config['APIS_CORS_ALLOWED_ORIGINS_REGEX'] or None
    allow_methods: List[str] = ['*']
    allow_headers: List[str] = ['*']
    expose_headers: List[str] = []
    allow_credentials: bool = False
    max_age: int = 600

    # we need to construct a Starlette CORSMiddleware instance for each set of settings
    # so we will create one instance per model instance
    cors_middleware_instance: Optional[Any] = None


class HeadersAllowedSettings(BaseModel):
    allowlist: List[str] = ['*']
    blocklist: List[str] = []


class CsrfSettings(BaseModel):
    require_token: bool = False
    require_on_methods: List[str] = [
        HttpMethods.POST,
        HttpMethods.PUT,
        HttpMethods.PATCH,
        HttpMethods.DELETE,
    ]
    single_use: bool = True


class ReqSettings(BaseModel):
    CSRF: Optional[CsrfSettings] = None
    CORS: Optional[CorsSettings] = None
    allowed_request_headers: Optional[HeadersAllowedSettings] = None
    allowed_response_headers: Optional[HeadersAllowedSettings] = None
    middlewares: Optional[List[Type]] = None
    timeout: Optional[int] = None


class ListenPathSettings(ReqSettings):
    prefix: Optional[str] = None
    prefix_regex: Optional[str] = None
    upstream_dsn: str = ''
    strip_prefix: bool = True

    def matches_path(self, request_path: str) -> bool:
        return path_matches(request_path, self.prefix, self.prefix_regex, match_prefix=True)

    def get_upstream_url(self, request_path: str) -> str:
        upstream_path = request_path
        if self.strip_prefix:
            upstream_path = strip_path_prefix(request_path, self.prefix, self.prefix_regex)
        return self.upstream_dsn.rstrip('/') + '/' + upstream_path.lstrip('/')


class RouteSettings(ReqSettings):
    path: Optional[str] = None
    path_regex: Optional[str] = None
    allow_methods: List[str] = [HttpMethods.ALL]

    def path_exactly_matches(self, request_path: str) -> bool:
        if self.path and self.path == request_path:
            return True
        return False

    def path_matches(self, request_path: str) -> bool:
        return path_matches(request_path, self.path, self.path_regex)


class Backend(ReqSettings):
    name: str
    listen: List[ListenPathSettings] = []
    routes: List[RouteSettings] = [RouteSettings(path_regex='.*')]

    CORS: CorsSettings = CorsSettings()
    CSRF: CsrfSettings = CsrfSettings()
    allowed_request_headers: HeadersAllowedSettings = HeadersAllowedSettings(allowlist=Headers.REQUEST_DEFAULT_ALLOW)
    allowed_response_headers: HeadersAllowedSettings = HeadersAllowedSettings(blocklist=Headers.RESPONSE_DEFAULT_BLOCK)
    middlewares: List[Type] = []

    def __str__(self):
        return f'<Backend "{self.name}">'
