from liminus_fastapi.base import Backend, ListenPathSettings


health_check_backend = Backend(
    name='health-check',
    listen=[
        ListenPathSettings(
            prefix_regex='/health(/|$)',
        ),
    ],
    middlewares=[],
)
