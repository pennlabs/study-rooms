import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from penndata.models import Event


EVENT_TYPE_MAP = [
    ("https://rodin.house.upenn.edu/calendar", Event.TYPE_RODIN_COLLEGE_HOUSE),
    ("https://harnwell.house.upenn.edu/calendar", Event.TYPE_HARNWELL_COLLEGE_HOUSE),
    ("https://harrison.house.upenn.edu/calendar", Event.TYPE_HARRISON_COLLEGE_HOUSE),
    ("https://gutmann.house.upenn.edu/calendar", Event.TYPE_GUTMANN_COLLEGE_HOUSE),
    ("https://radian.house.upenn.edu/calendar", Event.TYPE_RADIAN_COLLEGE_HOUSE),
    ("https://lauder.house.upenn.edu/calendar", Event.TYPE_LAUDER_COLLEGE_HOUSE),
    ("https://hill.house.upenn.edu/calendar", Event.TYPE_HILL_COLLEGE_HOUSE),
    ("https://kcech.house.upenn.edu/calendar", Event.TYPE_KCECH_COLLEGE_HOUSE),
    ("https://ware.house.upenn.edu/calendar", Event.TYPE_WARE_COLLEGE_HOUSE),
    ("https://fh.house.upenn.edu/calendar", Event.TYPE_FH_COLLEGE_HOUSE),
    ("https://riepe.house.upenn.edu/calendar", Event.TYPE_RIEPE_COLLEGE_HOUSE),
    ("https://dubois.house.upenn.edu/calendar", Event.TYPE_DUBOIS_COLLEGE_HOUSE),
    ("https://gregory.house.upenn.edu/calendar", Event.TYPE_GREGORY_COLLEGE_HOUSE),
    ("https://stouffer.house.upenn.edu/calendar", Event.TYPE_STOUFFER_COLLEGE_HOUSE),
]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for site, event_type in EVENT_TYPE_MAP:
            self.scrape_calendar_page(f"{site}", event_type)
        now = timezone.localtime()
        if now.day > 25:
            next = now + datetime.timedelta(days=30)
            next_month, next_year = next.month, next.year
            for site, event_type in EVENT_TYPE_MAP:
                self.scrape_calendar_page(f"{site}/{next_year}-{next_month:02d}", event_type)

        self.stdout.write("Uploaded College House Events!")

    def scrape_details(self, event_url):
        try:
            resp = requests.get(event_url, verify=False)
        except ConnectionError:
            print("Error:", ConnectionError)
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        location = (
            soup.find("div", class_="field-name-field-public-display-location").text.strip()
            if soup.find("div", class_="field-name-field-public-display-location")
            else None
        )
        start_time_str = (
            soup.select_one(".date-display-start").get("content")
            if soup.select_one(".date-display-start")
            else ""
        )
        end_time_str = (
            soup.select_one(".date-display-end").get("content")
            if soup.select_one(".date-display-end")
            else ""
        )
        start_time = (
            datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S%z")
            if start_time_str
            else None
        )
        end_time = (
            datetime.datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S%z")
            if end_time_str
            else None
        )
        description = (
            soup.select_one(".field-name-body").text.strip()
            if soup.select_one(".field-name-body")
            else None
        )
        image_url = (
            soup.select_one(".field-name-field-image img")["src"]
            if soup.select_one(".field-name-field-image img")
            else None
        )
        return location, start_time, end_time, description, image_url

    def scrape_calendar_page(self, calendar_url, event_type):
        try:
            resp = requests.get(calendar_url, verify=False)
        except ConnectionError:
            print("Error:", ConnectionError)
            return
        soup = BeautifulSoup(resp.text, "html.parser")

        event_cells = soup.find_all("td", class_="single-day future")

        email_element = soup.find("div", class_="views-field-field-office-email-contact").find("a")
        email = email_element["href"].split(":")[1] if email_element else None

        for cell in event_cells:
            if not (item := cell.find("div", class_="item")):
                continue
            if not (event_link := item.find("a", href=True)):
                continue
            name = event_link.text.strip()
            if not (url := event_link.get("href")):
                continue
            index = calendar_url.find("/", calendar_url.find("://") + 3)
            base_url = calendar_url[:index]
            url = f"{base_url}{url}"

            location, start_time, end_time, description, image_url = self.scrape_details(url)
            print(url + " " + name)
            Event.objects.update_or_create(
                name=name,
                defaults={
                    "event_type": event_type,
                    "image_url": image_url,
                    "start": start_time,
                    "end": end_time,
                    "location": location,
                    "website": url,
                    "description": description,
                    "email": email,
                },
            )
            if start_time and start_time > timezone.localtime() + datetime.timedelta(days=30):
                break
