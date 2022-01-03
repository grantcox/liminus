from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Route


async def catch_all(request: Request):
    # just echo the request URL back
    return JSONResponse({'method': request.method, 'url': request.url.path})


routes = [
    Route('/{rest_of_path:path}', catch_all, methods=['GET', 'POST']),
]
app = Starlette(routes=routes)
