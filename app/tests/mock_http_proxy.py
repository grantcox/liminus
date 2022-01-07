from aioresponses import aioresponses


# extend the aioresponses class to store the magicmock created
# so we can assert_called_with etc
class MockHttpProxy(aioresponses):
    def start(self):
        self._responses = []
        self._matches = {}
        self.active_mock = self.patcher.start()
        self.patcher.return_value = self._request_mock
