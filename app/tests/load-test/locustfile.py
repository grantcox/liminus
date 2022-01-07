import json

from locust import FastHttpUser, events, task


initial_cookie_header = (
    '__stripe_mid=3a80611-e1e8-493c-a24e; __utmc=220042694; _ga=GA1.2.1298171797.1640907670; '
    '_gcl_au=1.1.2103370023.1641036344; _gid=GA1.2.747770924.1641201600;'
    '__utma=220042694.1298171797.1640907670.1641215153.1641240057.6; '
    'OptanonConsent=landingPath=NotLandingPage&datestamp=Mon+Jan+03+2022+21%3A31%3A16+GMT%2B0100+(Central+'
    'European+Standard+Time)&version=3.6.19&groups=1%3A1%2C2%3A1%2C4%3A1%2C101%3A1%2C102%3A1%2C105%3A1&'
    'AwaitingReconsent=false'
)
realworld_user_agent = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/96.0.4664.110 Safari/537.36',
)
common_headers = {
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'authority': 'api.liminus',
    'gk-public-csrf-token': '5AMCfbdvmKrzS160car2cxxxxxGHMBXwweRtoa1CxFTlTMIl',
    'cache-control': 'no-cache',
    'origin': 'https://local.liminus',
    'pragma': 'no-cache',
    'referer': 'https://local.liminus/',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': realworld_user_agent,
    'x-requested-with': 'XMLHttpRequest',
}


class GatekeeperPyUser(FastHttpUser):
    @task
    def new_donation(self):
        self.client.post(
            '/donation/public_api/get_donation_form_context?campaign_id=3116',
            headers={
                **common_headers,
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/json',
                'cookie': initial_cookie_header,
            },
            data=json.dumps({'authData': {'userHash': None, 'campaign_id': 3116, 'lang': 'en'}}),
        )

        self.client.post(
            '/donation/public_api/new_donation?campaign_id=3116',
            headers={
                **common_headers,
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/json',
                'recaptcha-token': 'xxxx--efeefefe-xxx-TtlU-eeeee',
                'gk-public-csrf-token': '5AMCfbdvmKrzS160car2cxxxxxGHMBXwweRtoa1CxFTlTMIl',
            },
            data=json.dumps(
                {
                    'known_user_token': None,
                    'campaign': {
                        'campaignId': 3116,
                        'lang': 'fr',
                        'sourceUrl': 'https://local.liminus/campaign/fr/donate/',
                    },
                    'agreement': {
                        'amount': '3',
                        'currency': 'USD',
                        'recurringPeriod': 1,
                        'isOtherAmountLink': 0,
                        'isFixed': False,
                        'currencyFixed': False,
                    },
                    'pay_method': {
                        'existingPayMethodToken': None,
                        'family': 'creditcard',
                        'brand': 'visa',
                        'paymentIntentType': None,
                        'paymentIntentClientSecret': None,
                        'gatewayId': -30,
                        'stripePaymentMethodId': 'pm_1KEZ7EBLE2hpWqXKwMfiWD7P',
                    },
                    'is_sandbox': 1,
                    'confirmed_allow_duplicate_donation': 0,
                    'replacing_order_token': None,
                    'donation_type': 1,
                    'memberData': {
                        'email': 'grant.cox@gmail.com',
                        'countryId': 81,
                        'city': None,
                        'zip': '23232',
                        'cid': 3116,
                        'lang': 'fr',
                        'name': 'Grant Cox',
                        'firstName': 'Grant',
                        'lastName': 'Cox',
                        'gdpr_privacy_policy_data': '',
                        'privacy_policy_text': 'En continuant, vous acceptez de recevoir les emails. Notre',
                    },
                }
            ),
        )

        self.client.post(
            '/act/frontend_api/legacy/entrance.php?resource=consent&action=determineConsentTypesToShow',
            headers={
                **common_headers,
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'gk-public-csrf-token': '5AMCfbdvmKrzS160car2cxxxxxGHMBXwweRtoa1CxFTlTMIl',
            },
            data='uhash=sqdMsb&newuser=0&campaign_id=3116',
        )

        self.client.post(
            '/donation/public_api/get_donation_receipt',
            headers={
                **common_headers,
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'gk-public-csrf-token': '5AMCfbdvmKrzS160car2cxxxxxGHMBXwweRtoa1CxFTlTMIl',
            },
            data='known_user_token=xxxxxxrsfseaefsefafasefrtUwAexrNjb&invoice_code=S-TI956Y1ZD8',
        )

        self.client.get(
            '/act/profile.php?action=getUserData&language=en',
            headers={
                **common_headers,
                'accept': 'application/json, text/javascript, */*; q=0.01',
            },
        )

        self.client.get(
            '/act/frontend_api/legacy/get_share_text.php?asqdMsb&lang=en&cid=3116',
            headers={
                **common_headers,
                'accept': 'application/json, text/javascript, */*; q=0.01',
            },
        )

    @task
    def get_share_text(self):
        self.client.get(
            '/act/frontend_api/legacy/get_share_text.php?lang=en&cid=446',
            headers={
                **common_headers,
                'cookie': initial_cookie_header,
                'accept': 'application/json, text/javascript, */*; q=0.01',
            },
        )

    @task
    def admin_without_staff_auth(self):
        self.client.get('/admin/index.php?o=CampaignHome')

    @task
    def stats_service(self):
        self.client.get('/stats-internal/dashboard/topline')


@events.quitting.add_listener
def _(environment, **kw):
    """
    This hook defines pass/fail criteria for load tests.
    Note that this applies to aggregate stats, not the performance of individual endpoints.
    These criteria can be customized for different services.
    Docs:
    https://docs.locust.io/en/1.3.0/running-locust-without-web-ui.html#controlling-the-exit-code-of-the-locust-process
    """
    if environment.stats.total.fail_ratio > 0.01:
        print('Test failed due to failure ratio > 1%')
        environment.process_exit_code = 1
    elif environment.stats.total.get_response_time_percentile(0.9) > 250:
        print('Test failed due to 90th percentile response time > 250 ms')
        environment.process_exit_code = 1
    elif environment.stats.total.get_response_time_percentile(0.95) > 500:
        print('Test failed due to 95th percentile response time > 500 ms')
        environment.process_exit_code = 1
    elif environment.stats.total.get_response_time_percentile(0.999) > 2000:
        print('Test failed due to 99.9th percentile response time > 2000 ms')
        environment.process_exit_code = 1
    else:
        environment.process_exit_code = 0
