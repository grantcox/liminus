# flake8: noqa F401
from typing import List

from liminus.backends.donations_service import donation_service_backend
from liminus.backends.health_check import health_check_backend
from liminus.backends.web_act import web_act_backend
from liminus.base import Backend


all_backends = [
    donation_service_backend,
    health_check_backend,
    web_act_backend,
]
valid_backends = [be for be in all_backends if be is not None]
