import re
import time

from lxml import etree

from model import PropertyDetails, Ad


class Parser:

    def __init__(self, url: str, html_page) -> None:
        self.url = url
        self.doc = etree.fromstring(html_page, etree.HTMLParser())
        self.body = self.doc.find("body")

    def __get_last_update(self, online):
        online = online.strip()
        m = re.findall("^Online: ([0-9]+) ([a-zA-Z]+)$", online)
        if m is None or len(m) == 0:
            return None
        else:
            now = time.time()
            val = int(m[0][0])
            val_type = m[0][1]
            if val_type == "Sekunde" or val_type == "Sekunden":
                return now - val
            elif val_type == "Minute" or val_type == "Minuten":
                return now - val * 60
            elif val_type == "Stunde" or val_type == "Stunden":
                return now - val * 60 * 60
            elif val_type == "Tag" or val_type == "Tage":
                return now - val * 60 * 60 * 24
            else:
                raise Exception("Unknown online type '%s'" % val_type)

    def __get_all_tag_content(self, node):
        """

        :param node:
        :return:
        """
        return ' '.join([it.strip() for it in node.itertext()]).strip()

    def parse_search_results(self):
        results = self.body.xpath(".//div[contains(@class, 'offer_list_item')]")
        for item in results:
            item_id = item.attrib["data-id"]
            pic = item.xpath(".//a[contains(@href, '" + item_id + "')]")
            item_url = self.url + pic[0].attrib["href"]
            item_online = item.xpath(".//span[contains(text(), 'Online:')]")[0].text
            last_update = self.__get_last_update(item_online)
            yield Ad(item_id, item_url, last_update)

    def parse_property_details(self) -> PropertyDetails:
        body = self.doc.find("body")
        title = self.doc.xpath("//title")[0]
        main_content = body.xpath(".//div[contains(@class, 'panel-body')]")[0]

        ad_details = PropertyDetails(title.text)

        def try_read_descr(tag_elem):
            descr_lookup = tag_elem.xpath(".//div[contains(@id, 'ad_description_text')]")
            if len(descr_lookup) > 0:
                descr = ""
                for i in range(5):
                    fr_text = descr_lookup[0].xpath(".//div[@id='freitext_%s']" % i)
                    if len(fr_text) > 0:
                        fr_h3 = fr_text[0].xpath(".//h3[@class='headline headline-default']")
                        fr_h3 = "" if len(fr_h3) == 0 else fr_h3[0].text.strip()
                        fr_content = fr_text[0].xpath(".//p[@id='freitext_%s_content']" % i)[0]
                        descr = descr + ("%s\n%s\n" % (fr_h3, self.__get_all_tag_content(fr_content)))
                ad_details.descr = descr

        def get_data_from_wrapper_part(part_tag):
            part_descr = part_tag.xpath(".//label[contains(@class, 'description')]")[0]
            return "%s %s" % (get_data_from_wrapper_part_amount(part_tag), part_descr.text.strip())

        def get_data_from_wrapper_part_amount(part_tag):
            return part_tag.xpath(".//label[contains(@class, 'amount')]")[0].text.strip()

        def get_wrapper_top_part(wr_tag):
            part_res = wr_tag.xpath(".//div[@class='basic_facts_top_part']")
            return part_res[0] if len(part_res) > 0 else None

        def get_wrapper_bottom_part(wr_tag):
            part_res = wr_tag.xpath(".//div[@class='basic_facts_bottom_part']")
            return part_res[0] if len(part_res) > 0 else None

        def try_read_apartm_data(tag_elem):
            apart_data_container = tag_elem.xpath(".//div[@id='rent_wrapper']")
            if len(apart_data_container) > 0:
                ad_details.type = get_data_from_wrapper_part(get_wrapper_bottom_part(apart_data_container[0]))
                ad_details.size = get_data_from_wrapper_part_amount(get_wrapper_top_part(apart_data_container[0]))

        def try_read_costs(tag_elem):
            cost_data_container = tag_elem.xpath(".//div[@id='graph_wrapper']")
            if len(cost_data_container) > 0:
                top_cost = get_wrapper_top_part(cost_data_container[0])
                ad_details.misc_cost = get_data_from_wrapper_part_amount(top_cost.xpath(".//div[@id='misc_costs']")[0])
                ad_details.util_cost = get_data_from_wrapper_part_amount(
                    top_cost.xpath(".//div[@id='utilities_costs']")[0])
                ad_details.rent_cost = get_data_from_wrapper_part_amount(top_cost.xpath(".//div[@id='rent']")[0])
                bottom_cost = get_wrapper_bottom_part(cost_data_container[0])
                ad_details.total_cost = get_data_from_wrapper_part_amount(bottom_cost)

        def try_read_deposit_and_transfer(tag_elem):
            dep_data_container = tag_elem.xpath(".//div[@id='provision_equipment_wrapper']")
            if len(dep_data_container) > 0:
                dep_data_containers = dep_data_container[0].xpath(".//div[@class='provision-equipment']")
                ad_details.deposit = get_data_from_wrapper_part_amount(dep_data_containers[0])
                ad_details.transfer_cost = get_data_from_wrapper_part_amount(dep_data_containers[1])

        def try_read_address(tag_elem):
            address_container = tag_elem.xpath(".//a[@href='#mapContainer']")
            if len(address_container) > 0:
                ad_details.address = self.__get_all_tag_content(address_container[0])

        def try_read_from_date(tag_elem):
            from_container = tag_elem.xpath(".//div/p[contains(text(), 'frei ab:')]")
            if len(from_container) > 0:
                for b in from_container[0]:
                    if b.tag == 'b':
                        text = b.text.strip()
                        if ad_details.from_date is None:
                            ad_details.from_date = text
                        else:
                            ad_details.to_date = text

        def get_characteristic_with_icon(icon_class):
            ch_tag = main_content.xpath(".//span[contains(@class, '%s')]" % icon_class)
            if len(ch_tag) > 0:
                ch_tag = ch_tag[0].getparent()
                if ch_tag is not None:
                    return self.__get_all_tag_content(ch_tag)
            return None

        for t in main_content:
            if t.tag != "div":
                continue
            try_read_descr(t)
            try_read_apartm_data(t)
            try_read_costs(t)
            try_read_deposit_and_transfer(t)
            try_read_address(t)
            try_read_from_date(t)

        ad_details.floor = get_characteristic_with_icon("glyphicons-building")
        ad_details.furniture = get_characteristic_with_icon("glyphicons-bed")

        images = []
        for img_tag in main_content.xpath(".//img[@class='sp-image']"):
            url = img_tag.attrib.get('data-src', None)
            if url:
                images.append(url)
        ad_details.imgs = images
        return ad_details

    def details_page_has_pics(self) -> bool:
        return len(self.body.xpath(".//div[@id='WG-Pictures']")) > 0

    def parse_user_ids(self):
        author_ids = self.body.xpath(".//script[contains(text(), 'window.contactedData =')]")[0].text
        user_id = re.findall("user_id: \"([0-9]+)\"", author_ids)[0]
        asset_id = re.findall("asset_id: \"([0-9]+)\"", author_ids)[0]
        asset_type = re.findall("asset_type: \"([0-9]+)\"", author_ids)[0]
        return user_id, asset_id, asset_type
