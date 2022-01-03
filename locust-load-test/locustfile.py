import json

from locust import FastHttpUser, events, task


realworld_cookie_header = (
    '__stripe_mid=3a80611-e1e8-493c-a24e; __utmc=220042694; _ga=GA1.2.1298171797.1640907670; '
    '_gcl_au=1.1.2103370023.1641036344; _gid=GA1.2.747770924.1641201600;'
    '__utma=220042694.1298171797.1640907670.1641215153.1641240057.6; '
    'OptanonConsent=landingPath=NotLandingPage&datestamp=Mon+Jan+03+2022+21%3A31%3A16+GMT%2B0100+(Central+'
    'European+Standard+Time)&version=3.6.19&groups=1%3A1%2C2%3A1%2C4%3A1%2C101%3A1%2C102%3A1%2C105%3A1&'
    'AwaitingReconsent=false'
)


class GatekeeperPyUser(FastHttpUser):
    @task
    def get_donation_form_context(self):
        self.client.post(
            '/donation/public_api/get_donation_form_context?campaign_id=3116',
            headers={
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'authority': 'api.liminus',
                'gk-public-csrf-token': '5AMCfbdvmKrzS160car2cxxxxxGHMBXwweRtoa1CxFTlTMIl',
                'cache-control': 'no-cache',
                'content-type': 'application/json',
                'cookie': realworld_cookie_header,
                'origin': 'https://local.liminus',
                'pragma': 'no-cache',
                'referer': 'https://local.liminus/',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',

            },
            data=json.dumps({
                'authData': {'userHash': None, 'campaign_id': 3116, 'lang': 'en'}
            }),
        )

    @task
    def get_share_text(self):
        self.client.get(
            '/act/frontend_api/legacy/get_share_text.php?lang=en&cid=446',
            headers={
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'authority': 'local.liminus',
                'cache-control': 'no-cache',
                'cookie': realworld_cookie_header,
                'pragma': 'no-cache',
                'referer': 'https://local.liminus/page/en/',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
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
