from http import HTTPStatus
from typing import Optional
from urllib.parse import parse_qsl

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from liminus.constants import Headers
from liminus.campaign_settings import CampaignSettingsProvider
from liminus.base.backend import Backend, ReqSettings, RecaptchaEnabled
from liminus.base.middleware import GkRequestMiddleware
from liminus.errors import ErrorResponse
from liminus.settings import logger, config
from liminus.utils import php_bool


class RecaptchaCheckMiddleware(GkRequestMiddleware):
    campaign_settings: CampaignSettingsProvider = CampaignSettingsProvider()

    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        if not settings.recaptcha or settings.recaptcha.enabled == RecaptchaEnabled.DISABLED:
            # nothing to check for this request
            return

        recaptcha_token = req.headers.get(Headers.RECAPTCHA_TOKEN)
        if recaptcha_token:
            # we don't need to check any campaign settings - if a captcha is provided we always verify
            return await self._validate_recaptcha_token(req, recaptcha_token)

        # no captcha was provided
        # that's ok if it's campaign dependent and this campaign id does not require one
        if settings.recaptcha.enabled == RecaptchaEnabled.CAMPAIGN_SETTING:
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
            raise self._invalid_recaptcha_response(request,
                f'Campaign {campaign_id} requires a captcha, but none was provided')

    async def _validate_recaptcha_token(self, request: Request, recaptcha_token: Optional[str]):
        verify_endpoint = config['RECAPTCHA_VERIFY_URL']
        recaptcha_secret = config['RECAPTCHA_SECRET']

        async with httpx.AsyncClient() as client:
            post_data = {
                'secret': recaptcha_secret,
                'response': recaptcha_token,
            }
            response = await client.post(verify_endpoint, data=post_data, timeout=5)
            logger.info(f'Recaptcha response is: {response.json()}')
            logger.info(f'{request} captcha verified, status=')

            if not response.json()['success']:
                raise self._invalid_recaptcha_response(request, 'Captcha token was invalid')

    def _invalid_recaptcha_response(self, request: Request, details: str) -> ErrorResponse:
        error = f'{request} failing due to invalid recaptcha: {details}'
        logger.info(error)

        response_text = error if config['DEBUG'] else 'Invalid captcha token'
        response = JSONResponse({'error': response_text}, HTTPStatus.UNAUTHORIZED)
        return ErrorResponse(response)
