class Headers:
    PUBLIC_CSRF_TOKEN = 'public-csrf-token'
    X_FORWARDED_FOR_CLIENT_IP = 'x-forwarded-for-client'
    X_FORWARDED_FOR_CLIENT_IP_NORMALIZED = 'x-forwarded-for-client-normalized'
    CONNECTING_IP = 'connecting-ip'
    CONNECTING_IP_NORMALIZED = 'connecting-ip-normalized'
    RECAPTCHA_TOKEN = 'recaptcha-token'

    CLOUDFLARE_CONNECTING_IP = 'cf-connecting-ip'
    X_FORWARDED_FOR = 'x-forwarded-for'
    X_REQUESTED_WITH = 'x-requested-with'

    REQUEST_DEFAULT_ALLOW = {
        'accept-encoding',
        'accept',
        'accept-language',
        'connection',
        'content-type',
        'host',
        'referer',
        'user-agent',
        'x-requested-with',
    }
    RESPONSE_DEFAULT_BLOCK = {
        'member-authentication-jwt',
        'rotate-csrf',
        'staff-authentication-jwt',
        'x-powered-by',
        'server',
    }


class HttpMethods:
    ALL = '*'
    DELETE = 'DELETE'
    GET = 'GET'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    PATCH = 'PATCH'
    POST = 'POST'
    PUT = 'PUT'
