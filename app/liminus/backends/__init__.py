from liminus.backends.auth_service import auth_service_backend
from liminus.backends.dev_cloudflare_simulator import dev_cfsimulator_backend
from liminus.backends.devvm_simplesaml import devvm_simplesaml_backend
from liminus.backends.donations_service import donation_service_backend
from liminus.backends.health_check import health_check_backend
from liminus.backends.web_act import web_act_backend
from liminus.backends.admin import admin_backend


all_backends = [
    auth_service_backend,
    dev_cfsimulator_backend,
    devvm_simplesaml_backend,
    donation_service_backend,
    health_check_backend,
    web_act_backend,
    admin_backend,
]
valid_backends = [be for be in all_backends if be is not None]
