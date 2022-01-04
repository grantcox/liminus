import re
from enum import Enum
from typing import Any, List, Optional, Pattern, Set, Type

from pydantic import BaseModel

from liminus.constants import Headers, HttpMethods
from liminus.utils import strip_path_prefix


_middleware_instances = {}


class AuthSettings(BaseModel):
    requires_staff_auth: bool = False
    requires_member_auth: bool = False


class HeadersAllowedSettings(BaseModel):
    allowlist: Set[str] = set(['*'])
    blocklist: Set[str] = set()


class CsrfSettings(BaseModel):
    require_token: bool = False
    require_on_methods: List[str] = [
        HttpMethods.POST,
        HttpMethods.PUT,
        HttpMethods.PATCH,
        HttpMethods.DELETE,
    ]
    single_use: bool = True


class RecaptchaEnabled(Enum):
    DISABLED = 0
    ALWAYS = 1
    CAMPAIGN_SETTING = 2


class RecaptchaSettings(BaseModel):
    enabled: RecaptchaEnabled = RecaptchaEnabled.DISABLED


class ReqSettings(BaseModel):
    CSRF: Optional[CsrfSettings] = None
    auth: Optional[AuthSettings] = None
    recaptcha: Optional[RecaptchaSettings] = None
    allowed_request_headers: Optional[HeadersAllowedSettings] = None
    allowed_response_headers: Optional[HeadersAllowedSettings] = None
    middlewares: Optional[List[Type]] = None
    timeout: Optional[int] = None


class PathRewrites(BaseModel):
    path_from: Optional[str] = None
    path_from_regex: Optional[Pattern] = None
    path_to: Optional[str] = None
    path_to_regex: Optional[Pattern] = None

    def rewrite_path(self, request_path: str) -> str:
        if self.path_from is not None and request_path == self.path_from:
            return self.path_to or request_path

        if self.path_from_regex is not None:
            replacement = self.path_from_regex or self.path_from
            if replacement:
                return re.sub(self.path_from_regex, replacement, request_path)

        return request_path


class ListenPathSettings(ReqSettings):
    prefix: Optional[str] = None
    path_regex: Optional[Pattern] = None
    upstream_dsn: str = ''
    strip_prefix: bool = True
    rewrites: List[PathRewrites] = []

    def matches_path(self, request_path: str) -> bool:
        if self.prefix and request_path.startswith(self.prefix):
            return True

        if self.path_regex and self.path_regex.match(request_path):
            return True

        return False

    def get_upstream_url(self, request_path: str) -> str:
        upstream_path = request_path
        for rewrite in self.rewrites:
            upstream_path = rewrite.rewrite_path(upstream_path)
        if self.strip_prefix:
            upstream_path = strip_path_prefix(request_path, self.prefix, self.path_regex)
        return self.upstream_dsn.rstrip('/') + '/' + upstream_path.lstrip('/')


class RouteSettings(ReqSettings):
    path: Optional[str] = None
    path_regex: Optional[Pattern] = None
    allow_methods: Set[str] = {HttpMethods.ALL}

    def route_exactly_matches(self, request_path: str, request_method: str) -> bool:
        if not self.method_matches(request_method):
            return False

        return self.path == request_path

    def route_matches(self, request_path: str, request_method: str) -> bool:
        if not self.method_matches(request_method):
            return False

        if self.path == request_path:
            return True

        if self.path_regex and self.path_regex.match(request_path):
            return True

        return False

    def method_matches(self, request_method: str) -> bool:
        if HttpMethods.ALL in self.allow_methods:
            return True
        if request_method in self.allow_methods:
            return True
        return False


class Backend(ReqSettings):
    name: str
    listen: ListenPathSettings = ListenPathSettings()
    routes: List[RouteSettings] = [RouteSettings(path_regex=re.compile('.*'))]

    CSRF: CsrfSettings = CsrfSettings()
    auth: AuthSettings = AuthSettings()
    recaptcha: RecaptchaSettings = RecaptchaSettings()
    allowed_request_headers: HeadersAllowedSettings = HeadersAllowedSettings(allowlist=Headers.REQUEST_DEFAULT_ALLOW)
    allowed_response_headers: HeadersAllowedSettings = HeadersAllowedSettings(blocklist=Headers.RESPONSE_DEFAULT_BLOCK)
    middlewares: List[Type] = []
    middleware_instances: List[Any] = []
    timeout: int = 10

    def __str__(self):
        return f'<Backend "{self.name}">'

    def __init__(__pydantic_self__, **data: Any) -> None:
        super().__init__(**data)
        __pydantic_self__._compile_settings()

    def _compile_settings(self):
        # coalesce all the ReqSettings into explicit / complete objects on each route
        # so we don't have to do it for every separate request
        self._coalesce_settings(self.listen, self)

        for route in self.routes:
            self._coalesce_settings(route, self.listen, self)

        # create instances for all the middleware classes
        for mw_class in self.middlewares:
            if mw_class.__name__ not in _middleware_instances:
                _middleware_instances[mw_class.__name__] = mw_class()

            self.middleware_instances.append(_middleware_instances[mw_class.__name__])

    def _coalesce_settings(self, into: ReqSettings, *args):
        for setting_source in args:
            for prop in ReqSettings().dict():
                if getattr(into, prop) is None:
                    setattr(into, prop, getattr(setting_source, prop))
