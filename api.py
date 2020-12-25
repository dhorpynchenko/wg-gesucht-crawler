import json
import requests


class API:

    def __init__(self, url) -> None:
        super().__init__()
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 OPR/73.0.3856.284'
        }

    def __get_search_url(self, page: int):
        return (self.url + "/1-zimmer-wohnungen-in-Munchen.90.1.1.%s.html") % page

    def get_ads(self, pages: int, search_params: dict):
        for p in range(pages):
            p_url = self.__get_search_url(p)
            response = requests.get(p_url, params=search_params, headers=self.headers)
            assert p_url in response.url and response.status_code == 200, "Failed to get search results"
            yield response.content.decode("utf-8")

    def get_ad_page(self, url):
        ad_page = requests.get(url, headers=self.headers)
        assert ad_page.status_code == 200, "Failed to get ad page"
        return ad_page.content.decode("utf-8")

    def get_user_data(self, user_id, asset_id, asset_type) -> dict:
        user_data_resp = requests.get(self.url + '/api/profiles/contact-data/' + user_id + '?asset_type='
                                      + asset_type + '&asset_id=' + asset_id, headers=self.headers)
        assert user_data_resp.status_code == 200, "Failed to get user details"
        return json.loads(user_data_resp.content.decode("utf-8"))
