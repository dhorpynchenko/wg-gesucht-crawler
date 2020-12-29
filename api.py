import json
import requests


class API:

    def __init__(self, url) -> None:
        super().__init__()
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 OPR/73.0.3856.284'
        }
        self.cookies = {

        }

    def __set_cookie(self, name, value):
        if value:
            print("Update cookie to %s" % value)
            self.cookies[name] = value
        elif self.cookies.get(name, None):
            del self.cookies[name]

    def __check_throw_response_success(self, response: requests.Response, target_url=None):
        if response.status_code != 200:
            raise Exception("Response status code is %s" % response.status_code)
        elif target_url is not None and target_url not in response.url:
            raise Exception("Expected url %s but redirected to \n%s" % (target_url, response.url))

    def __get_search_url(self, page: int):
        return (self.url + "/1-zimmer-wohnungen-in-Munchen.90.1.1.%s.html") % page

    def __update_cookies(self, response: requests.Response):
        self.__set_cookie('PHPSESSID', response.cookies.get('PHPSESSID', None))

    def get_ads(self, pages: int, search_params: dict):
        for p in range(pages):
            p_url = self.__get_search_url(p)
            try:
                response = requests.get(p_url, params=search_params, headers=self.headers, cookies=self.cookies)
                self.__check_throw_response_success(response, p_url)
                self.__update_cookies(response)
            except Exception as e:
                raise Exception("Failed to get search results: %s" % e)
            yield response.content.decode("utf-8")

    def get_ad_page(self, url):
        try:
            ad_page = requests.get(url, headers=self.headers, cookies=self.cookies)
            self.__check_throw_response_success(ad_page, url)
            self.__update_cookies(ad_page)
        except Exception as e:
            raise Exception("Failed to get ad page: %s" % e)
        return ad_page.content.decode("utf-8")

    def get_user_data(self, user_id, asset_id, asset_type) -> dict:
        try:
            url = self.url + '/api/profiles/contact-data/' + user_id
            user_data_resp = requests.get(url + '?asset_type=' + asset_type + '&asset_id=' + asset_id,
                                          headers=self.headers, cookies=self.cookies)
            self.__check_throw_response_success(user_data_resp, url)
            self.__update_cookies(user_data_resp)
        except Exception as e:
            raise Exception("Failed to get user details: %s" % e)
        return json.loads(user_data_resp.content.decode("utf-8"))

    def get_image(self, url):
        try:
            response = requests.get(url, cookies=self.cookies)
            self.__check_throw_response_success(response)
        except Exception as e:
            raise Exception("Failed to get image: %s" % e)
        return response.content
