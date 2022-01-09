from liminus import settings
from liminus.backends.admin import admin_backend
from liminus.backends.auth_service import auth_service_backend
from liminus.backends.dev_cloudflare_simulator import dev_cfsimulator_backend
from liminus.backends.devvm_simplesaml import devvm_simplesaml_backend
from liminus.backends.donations_service import donation_service_backend
from liminus.backends.health_check import health_check_backend
from liminus.backends.petitions_service import petitions_service_backend
from liminus.backends.stats_service import stats_service_backend
from liminus.backends.web_act import web_act_backend


all_backends = [
    auth_service_backend,
    dev_cfsimulator_backend,
    devvm_simplesaml_backend,
    donation_service_backend,
    health_check_backend,
    petitions_service_backend,
    stats_service_backend,
    web_act_backend,
    admin_backend,
]
valid_backends = [be for be in all_backends if be.name in settings.ENABLED_BACKENDS]
# the health check is always enabled
valid_backends.append(health_check_backend)

for be in valid_backends:
    be.init()

__all__ = ['valid_backends']
