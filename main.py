from ad_parser import Parser
from model import Author
from api import API
import time
import jsonpickle
import os

search_data = {
    # 1 - 1-Room-flats, 0 - Flatshares, 2 - Flats, 3 - Houses
    "categories[]": [1],
    "city_id": 90,
    "noDeact": 1,
    # 2 - No swap
    "exc": 2,
    "img_only": 1,
    # 0 - any , 1 - Short term, 2 - Long term, 3 - Overnight stay
    "rent_types[]": [2]
}

url = "https://www.wg-gesucht.de"
api = API(url)


def save_to_file(content, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    delay = 5
    for results_page in api.get_ads(2, search_data):
        res_parser = Parser(url, results_page)
        time.sleep(delay)
        for ad in res_parser.parse_search_results():

            dir = './data/' + ad.id
            if not os.path.exists(dir) or not os.path.isdir(dir):
                os.mkdir(dir)

            print("Reading ad: %s" % ad.url)
            ad_page = api.get_ad_page(ad.url)
            save_to_file(ad_page, dir + '/ad.html')

            ad_parser = Parser(url, ad_page)
            ad.details = ad_parser.parse_property_details()
            user_ids = ad_parser.parse_user_ids()
            user_data = api.get_user_data(user_ids[0], user_ids[1], user_ids[2])
            ad.author = Author(user_ids[0], user_data['public_name'], user_data['mobile'],
                               user_data['verified_user'] == '1',
                               user_data['_links']['self']['href'])
            save_to_file(jsonpickle.dumps(ad), dir + '/ad.json')
            print("Saved ad %s" % ad.id)
            time.sleep(delay)


if __name__ == '__main__':
    main()
