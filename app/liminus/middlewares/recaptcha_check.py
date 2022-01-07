from http import HTTPStatus
from typing import Optional
from urllib.parse import parse_qsl

from starlette.requests import Request
from starlette.responses import JSONResponse

from liminus import settings
from liminus.base.backend import Backend, RecaptchaEnabled, ReqSettings
from liminus.base.middleware import GkRequestMiddleware
from liminus.campaign_settings import CampaignSettingsProvider
from liminus.constants import Headers
from liminus.errors import ErrorResponse
from liminus.proxy_request import http_request
from liminus.utils import php_bool


logger = settings.logger


class RecaptchaCheckMiddleware(GkRequestMiddleware):
    campaign_settings: CampaignSettingsProvider = CampaignSettingsProvider()

    async def handle_request(self, req: Request, reqset: ReqSettings, backend: Backend):
        if not reqset.recaptcha or reqset.recaptcha.enabled == RecaptchaEnabled.DISABLED:
            # nothing to check for this request
            return

        recaptcha_token = req.headers.get(Headers.RECAPTCHA_TOKEN)
        if recaptcha_token:
            # we don't need to check any campaign settings - if a captcha is provided we always verify
            return await self._verify_recaptcha_token(req, recaptcha_token)

        # no captcha was provided
        # that's ok if it's campaign dependent and this campaign id does not require one
        if reqset.recaptcha.enabled == RecaptchaEnabled.CAMPAIGN_SETTING:
            self._raise_if_campaign_requires_captcha(req)

        else:
            # a captcha is always required and was not provided
            raise self._invalid_recaptcha_response(req, 'Captcha required but not submitted')

    async def _raise_if_campaign_requires_captcha(self, request: Request):
        campaign_id = dict(parse_qsl(request.url.query)).get('campaign_id')
        if not campaign_id:
            # we cannot check the campaign settings, so default fail
            raise self._invalid_recaptcha_response(request, 'No campaign id provided')

        campaign_settings = await self.campaign_settings.get_campaign_settings(int(campaign_id))
        if not campaign_settings:
            # invalid campaign id, default fail
            raise self._invalid_recaptcha_response(request, f'Invalid campaign id "{campaign_id}"')

        captcha_required = php_bool(campaign_settings.get('antispam_captcha_on_sign_forms_enabled', False))
        if captcha_required:
            raise self._invalid_recaptcha_response(
                request, f'Campaign {campaign_id} requires a captcha, but none was provided'
            )

    async def _verify_recaptcha_token(self, request: Request, recaptcha_token: Optional[str]):
        verify_endpoint = settings.RECAPTCHA_VERIFY_URL
        recaptcha_secret = settings.RECAPTCHA_SECRET

        response = await http_request(
            'POST',
            verify_endpoint,
            data={
                'secret': recaptcha_secret,
                'response': recaptcha_token,
            },
        )
        response_data = await response.json()
        # we expect a response like:
        # {'success': True, 'challenge_ts': '2022-01-05T22:23:42Z', 'hostname': 'local.liminus'}

        if not response_data.get('success'):
            raise self._invalid_recaptcha_response(request, f'Captcha verify failed: {response_data}')

    def _invalid_recaptcha_response(self, request: Request, details: str) -> ErrorResponse:
        error = f'{request} failing due to invalid recaptcha: {details}'
        logger.info(error)

        response_text = error if settings.DEBUG else 'Invalid captcha token'
        response = JSONResponse({'error': response_text}, HTTPStatus.UNAUTHORIZED)
        return ErrorResponse(response)
