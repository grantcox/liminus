from starlette.requests import Request

from liminus.base import Backend, BaseGkHTTPMiddleware, ReqSettings
from liminus.constants import Headers
from liminus.utils import normalize_ip_address


class AddIpHeadersMiddleware(BaseGkHTTPMiddleware):
    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        # for geo-ip purposes we trust the x-forwarded-for
        # for security purposes we do not trust that, and we use the IP that connected to CloudFlare
        xff = req.headers.get(Headers.X_FORWARDED_FOR, '')
        for ip in xff.split(','):
            ip = ip.strip()
            normalized_ip = normalize_ip_address(ip)
            if normalized_ip:
                # this is the most specific valid IP
                req.state.headers[Headers.X_FORWARDED_FOR_CLIENT_IP] = ip
                req.state.headers[Headers.X_FORWARDED_FOR_CLIENT_IP_NORMALIZED] = normalized_ip
                break

        security_ip = req.headers.get(Headers.CLOUDFLARE_CONNECTING_IP, '')
        security_ip_normalized = normalize_ip_address(ip)
        if security_ip_normalized:
            req.state.headers[Headers.CONNECTING_IP] = security_ip
            req.state.headers[Headers.CONNECTING_IP_NORMALIZED] = security_ip_normalized
