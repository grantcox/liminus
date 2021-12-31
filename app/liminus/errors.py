from starlette.responses import Response


class ErrorResponse(Exception):
    def __init__(self, response: Response) -> None:
        self.response = response
