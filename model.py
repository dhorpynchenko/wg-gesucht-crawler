from datetime import datetime


class Ad:

    def __init__(self, ad_id: str, ad_url, last_update) -> None:
        super().__init__()
        self.id = ad_id
        self.url = ad_url
        self.last_update = last_update
        self.details = None
        self.author = None

    def __repr__(self):
        return "%s %s" % (datetime.fromtimestamp(self.last_update), self.url)


class PropertyDetails:

    def __init__(self, title):
        self.title = title
        self.imgs = []
        self.descr = None
        self.type = None
        self.size = None

        self.address = None

        self.misc_cost = None
        self.util_cost = None
        self.rent_cost = None
        self.total_cost = None

        self.deposit = None
        self.transfer_cost = None

        self.from_date = None
        self.to_date = None


class Author:

    def __init__(self, user_id, name, phone, verified, profile_link):
        self.id = user_id
        self.name = name
        self.phone = phone
        self.verified = verified
        self.profile_link = profile_link
