from ad_parser import Parser
from model import Author
from api import API
import time
import jsonpickle
import os

search_data = {
    # Mark for accom offers request
    "offer_filter": 1,
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


def main():
    for results_page in api.get_ads(2, search_data):
        res_parser = Parser(url, results_page)
        for ad in res_parser.parse_search_results():
            ad_page = api.get_ad_page(ad.url)
            ad_parser = Parser(url, ad_page)
            ad.details = ad_parser.parse_property_details()
            user_ids = ad_parser.parse_user_ids()
            user_data = api.get_user_data(user_ids[0], user_ids[1], user_ids[2])
            ad.author = Author(user_ids[0], user_data['public_name'], user_data['mobile'],
                               user_data['verified_user'] == '1',
                               user_data['_links']['self']['href'])
            dir = './data/' + ad.id
            if not os.path.exists(dir) or not os.path.isdir(dir):
                os.mkdir(dir)
            with open(dir + '/ad.json', 'w', encoding='utf-8') as f:
                f.write(jsonpickle.dumps(ad))
            print("Saved ad %s" % ad.id)


if __name__ == '__main__':
    main()
