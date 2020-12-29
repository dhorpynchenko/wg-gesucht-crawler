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

def create_if_no_exists(dir_path):
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        os.mkdir(dir_path)

def main():
    delay = 5
    for results_page in api.get_ads(2, search_data):
        res_parser = Parser(url, results_page)
        time.sleep(delay)
        for ad in res_parser.parse_search_results():

            dir = './data/' + ad.id
            create_if_no_exists(dir)

            print("Reading ad: %s" % ad.url)
            ad_page = api.get_ad_page(ad.url)
            ad_parser = Parser(url, ad_page)
            if not ad_parser.details_page_has_pics():
                time.sleep(delay)
                print("Parser detected that page had no photos block. Try reload page...")
                ad_page = api.get_ad_page(ad.url)
                ad_parser = Parser(url, ad_page)

            save_to_file(ad_page, dir + '/ad.html')

            ad.details = ad_parser.parse_property_details()
            user_ids = ad_parser.parse_user_ids()
            user_data = api.get_user_data(user_ids[0], user_ids[1], user_ids[2])
            ad.author = Author(user_ids[0], user_data['public_name'], user_data['mobile'],
                               user_data['verified_user'] == '1',
                               user_data['_links']['self']['href'])
            save_to_file(jsonpickle.dumps(ad), dir + '/ad.json')
            print("Saved ad %s" % ad.id)

            pic_dir = dir + '/img'
            create_if_no_exists(pic_dir)
            for p_url in ad.details.imgs:
                content = api.get_image(p_url)
                img_name = p_url.rsplit('/', 1)[-1]
                with open(pic_dir + '/' + img_name, "wb") as img_file:
                    img_file.write(content)

            time.sleep(delay)


if __name__ == '__main__':
    main()
