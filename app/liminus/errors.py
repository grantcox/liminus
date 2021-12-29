from http import HTTPStatus

from httpx import Response


class UnauthorizedResponse(Response):
    def __init__(self, msg: str = '') -> None:
        super().__init__(status_code=HTTPStatus.UNAUTHORIZED, text=msg)
