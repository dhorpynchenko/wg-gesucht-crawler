from random import shuffle
from typing import Optional

from ad_parser import AdParser, SearchResultsParser
from model import Author, Ad
from api import API, ALL_CITIES, RequestFailedException, CitySearch
import time
import jsonpickle
import os

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


def scan_city(city: CitySearch, data_dir, delay):

    for results_page in api.get_ads(city, 2):
        res_parser = SearchResultsParser(url, results_page)
        time.sleep(delay)
        for ad in res_parser.parse_search_results():

            dir = data_dir + ad.id
            create_if_no_exists(dir)

            print("Reading ad: %s" % ad.url)
            ad_page = api.get_ad_page(ad.url)
            ad_parser = AdParser(url, ad_page)
            if not ad_parser.is_ad_page():
                print("Not an ad page, skip")
                time.sleep(delay)
                continue
            if not ad_parser.details_page_has_pics():
                time.sleep(delay)
                print("Parser detected that page had no photos block. Try reload page...")
                ad_page = api.get_ad_page(ad.url)
                ad_parser = AdParser(url, ad_page)

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
            ad.city = city.name
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


def main():
    data_dir = './data/'
    delay = 10
    delay_captcha = 60 * 60

    while True:
        cities = [c for c in ALL_CITIES]
        shuffle(cities)
        for city in cities:
            try:
                scan_city(city, data_dir, delay)
            except RequestFailedException as e:
                print("Failure during request. Delay for %s sec. Error %s" % (delay_captcha, e))
                time.sleep(delay_captcha)

    # Check old ads that weren't found in the search output and check if they are deactivated
    # for old in existing_ads:
    #     data_file = data_dir + old + '/ad.json'
    #     if not os.path.exists(data_file):
    #         print("No data file inside data folder %s" % old)
    #         continue
    #     existing_record = read_record(data_file)
    #     if existing_record is None:
    #         continue
    #     if existing_record.deactivated is not None:
    #         continue
    #     if time.time() - existing_record.last_update > 60 * 60 * 24 * 7:
    #         print("Ad '%s' is older than a week old. Skipping check..." % existing_record.id)
    #         continue
    #     print("Check ad for the state: %s" % existing_record.url)
    #     ad_page = api.get_ad_page(existing_record.url)
    #     if Parser(url, ad_page).details_page_is_deactivated_or_not_found():
    #         print("Ad '%s' is deactivated" % existing_record.id)
    #         existing_record.deactivated = time.time()
    #         save_to_file(to_json(existing_record), data_file)
    #         time.sleep(delay)


if __name__ == '__main__':
    main()
