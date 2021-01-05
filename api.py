import json
import requests


class CitySearch:
    categories = {
        0: "wg-zimmer",
        1: "1-zimmer-wohnungen",
        2: "wohnungen",
        3: "haeuser"
    }

    def __init__(self, name, city_id) -> None:
        self.name = name
        self.id = city_id
        self.search_params = {
            # 1 - 1-Room-flats, 0 - Flatshares, 2 - Flats, 3 - Houses
            "categories[]": [1, 2],
            "city_id": self.id,
            "noDeact": 1,
            # 2 - No swap
            "exc": 2,
            "img_only": 1,
            # 0 - any , 1 - Short term, 2 - Long term, 3 - Overnight stay
            "rent_types[]": [2]
        }

    def get_search_url(self, url, page: int):
        categories_sorted = sorted(self.search_params["categories[]"])
        categories = "+".join(str(c) for c in categories_sorted)
        url_suffix = "-und-".join(CitySearch.categories[c] for c in categories_sorted)
        return (url + "/%s-in-%s.%s.%s.1.%s.html") % (url_suffix, self.name, self.id, categories, page)


MUNICH = CitySearch("Munchen", 90)
BERLIN = CitySearch("Berlin", 8)
COLOGNE = CitySearch("Koeln", 73)
DUSSELDORF = CitySearch("Dusseldorf", 30)
DORTMUND = CitySearch("Dortmund", 26)
ESSEN = CitySearch("Essen", 35)
DRESDEN = CitySearch("Dresden", 27)
NURNBERG = CitySearch("Nurnberg", 96)
STUTTGART = CitySearch("Stuttgart", 124)
FRANKFURT = CitySearch("Frankfurt-am-Main", 41)
HANNOVER = CitySearch("Hannover", 57)
BREMEN = CitySearch("Bremen", 17)
HAMBURG = CitySearch("Hamburg", 55)

ALL_CITIES = [MUNICH, BERLIN, COLOGNE, FRANKFURT, HAMBURG, STUTTGART, DRESDEN, HANNOVER, BREMEN, DUSSELDORF,
              DORTMUND, ESSEN,  NURNBERG]


class RequestFailedException(Exception):
    pass


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

    def __update_cookies(self, response: requests.Response):
        self.__set_cookie('PHPSESSID', response.cookies.get('PHPSESSID', None))

    def get_ads(self, city: CitySearch, pages: int):
        for p in range(pages):
            p_url = city.get_search_url(self.url, p)
            try:
                response = requests.get(p_url, params=city.search_params, headers=self.headers, cookies=self.cookies)
                self.__check_throw_response_success(response, p_url)
                self.__update_cookies(response)
            except Exception as e:
                raise RequestFailedException("Failed to get search results: %s" % e)
            yield response.content.decode("utf-8")

    def get_ad_page(self, url):
        try:
            ad_page = requests.get(url, headers=self.headers, cookies=self.cookies)
            self.__check_throw_response_success(ad_page, url)
            self.__update_cookies(ad_page)
        except Exception as e:
            raise RequestFailedException("Failed to get ad page: %s" % e)
        return ad_page.content.decode("utf-8")

    def get_user_data(self, user_id, asset_id, asset_type) -> dict:
        try:
            url = self.url + '/api/profiles/contact-data/' + user_id
            user_data_resp = requests.get(url + '?asset_type=' + asset_type + '&asset_id=' + asset_id,
                                          headers=self.headers, cookies=self.cookies)
            self.__check_throw_response_success(user_data_resp, url)
            self.__update_cookies(user_data_resp)
        except Exception as e:
            raise RequestFailedException("Failed to get user details: %s" % e)
        return json.loads(user_data_resp.content.decode("utf-8"))

    def get_image(self, url):
        try:
            response = requests.get(url, cookies=self.cookies)
            self.__check_throw_response_success(response)
        except Exception as e:
            raise RequestFailedException("Failed to get image: %s" % e)
        return response.content
