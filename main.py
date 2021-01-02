from typing import Optional

from ad_parser import Parser
from model import Author, Ad
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


def to_json(ad: Ad):
    return jsonpickle.encode(ad)


def read_record(data_file) -> Optional[Ad]:
    try:
        if os.path.exists(data_file):
            with open(data_file) as f:
                record = jsonpickle.decode(f.read())
                if not isinstance(record, Ad):
                    raise Exception("Expected Ad object but got '%s'" % record)
                return record
    except Exception as e:
        print("Failed to read previous record of this ad %s" % e)
    return None


def main():
    data_dir = './data/'
    existing_ads = {a for a in os.listdir(data_dir)}
    delay = 5
    for results_page in api.get_ads(2, search_data):
        res_parser = Parser(url, results_page)
        time.sleep(delay)
        for ad in res_parser.parse_search_results():

            existing_ads.discard(ad.id)

            dir = data_dir + ad.id
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
            data_file = dir + '/ad.json'
            prev_record = read_record(data_file)

            ad.details = ad_parser.parse_property_details()
            user_ids = ad_parser.parse_user_ids()
            user_data = api.get_user_data(user_ids[0], user_ids[1], user_ids[2])
            ad.author = Author(user_ids[0], user_data['public_name'], user_data['mobile'],
                               user_data['verified_user'] == '1',
                               user_data['_links']['self']['href'])
            if prev_record is not None:
                ad.created = prev_record.created
            save_to_file(to_json(ad), data_file)
            print("Saved ad %s" % ad.id)

            pic_dir = dir + '/img'
            create_if_no_exists(pic_dir)
            for p_url in ad.details.imgs:
                content = api.get_image(p_url)
                img_name = p_url.rsplit('/', 1)[-1]
                img_url = pic_dir + '/' + img_name
                if os.path.exists(img_url):
                    continue
                with open(img_url, "wb") as img_file:
                    img_file.write(content)

            time.sleep(delay)

    # Check old ads that weren't found in the search output and check if they are deactivated
    for old in existing_ads:
        data_file = data_dir + old + '/ad.json'
        if not os.path.exists(data_file):
            print("No data file inside data folder %s" % old)
            continue
        existing_record = read_record(data_file)
        if existing_record is None:
            continue
        if existing_record.deactivated is not None:
            continue
        if time.time() - existing_record.last_update > 60 * 60 * 24 * 7:
            print("Ad '%s' is older than a week old. Skipping check..." % existing_record.id)
            continue
        print("Check ad for the state: %s" % existing_record.url)
        ad_page = api.get_ad_page(existing_record.url)
        if Parser(url, ad_page).details_page_is_deactivated_or_not_found():
            print("Ad '%s' is deactivated" % existing_record.id)
            existing_record.deactivated = time.time()
            save_to_file(to_json(existing_record), data_file)
            time.sleep(delay)


if __name__ == '__main__':
    main()
