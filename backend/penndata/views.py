import datetime

import requests
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from django.utils import timezone
from pytz.exceptions import NonExistentTimeError
from requests.exceptions import ConnectionError
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from penndata.models import AnalyticsEvent, Event, FitnessRoom, FitnessSnapshot, HomePageOrder
from penndata.serializers import (
    AnalyticsEventSerializer,
    EventSerializer,
    FitnessSnapshotSerializer,
    HomePageOrderSerializer,
)


class News(APIView):
    """
    GET: Get's news article from the DP
    """

    def get_article(self):
        article = {"source": "The Daily Pennsylvanian"}
        try:
            resp = requests.get("https://www.thedp.com/")
        except ConnectionError:
            return None

        html = resp.content.decode("utf8")

        soup = BeautifulSoup(html, "html5lib")

        frontpage = soup.find("div", {"class": "col-lg-6 col-md-5 col-sm-12 frontpage-carousel"})

        # adds all variables for news object
        if frontpage:
            title_html = frontpage.find("a", {"class": "frontpage-link large-link"})
        if title_html:
            article["link"] = title_html["href"]
            article["title"] = title_html.get_text()

        subtitle_html = frontpage.find("p")
        if subtitle_html:
            article["subtitle"] = subtitle_html.get_text()

        timestamp_html = frontpage.find("div", {"class": "timestamp"})
        if timestamp_html:
            article["timestamp"] = timestamp_html.get_text().strip()

        image_html = frontpage.find("img")
        if image_html:
            article["imageurl"] = image_html["src"]

        # checks if all variables are there
        if all(v in article for v in ["title", "subtitle", "timestamp", "imageurl", "link"]):
            return article
        else:
            return None

    def get(self, request):
        article = self.get_article()
        if article:
            return Response(article)
        else:
            return Response({"error": "Site could not be reached or could not be parsed."})


class Calendar(APIView):
    """
    GET: Returns upcoming university events (within 2 weeks away)
    """

    def get_calendar(self):
        # scapes almanac from upenn website
        try:
            resp = requests.get("https://almanac.upenn.edu/penn-academic-calendar")
        except ConnectionError:
            return None
        soup = BeautifulSoup(resp.content.decode("utf8"), "html5lib")
        # finds table with all information and gets the rows
        table = soup.find(
            "table",
            {
                "class": (
                    "table table-bordered table-striped "
                    "table-condensed table-responsive calendar-table"
                )
            },
        )
        rows = table.find_all("tr")
        calendar = []
        current_year = timezone.localtime().year
        row_year = 0

        # collect end dates on all events and filter based on that
        for row in rows:
            header = row.find_all("th")
            if len(header) > 0:
                row_year = header[0].get_text().split(" ")[0]
            # skips calculation if years don't align
            if int(row_year) != current_year:
                continue
            if len(header) == 0:
                data = row.find_all("td")
                date_info = data[1].get_text()
                date = None
                try:
                    # handles case for date ex. August 31
                    date = datetime.datetime.strptime(
                        date_info + str(current_year) + "-04:00", "%B %d%Y%z"
                    )
                except ValueError:
                    try:
                        # handles case for date ex. August 1-3
                        month = date_info.split(" ")[0]
                        day = date_info.split("-")[1]
                        date = datetime.datetime.strptime(
                            month + day + str(current_year) + "-04:00", "%B%d%Y%z"
                        )
                    except (ValueError, IndexError):
                        try:
                            # handles case for date ex. August 1-September 31
                            last_date = date_info.split("-")[0].split(" ")
                            month = last_date[0]
                            day = last_date[1]
                            date = datetime.datetime.strptime(
                                month + day + str(current_year) + "-04:00", "%B%d%Y%z"
                            )
                        except (ValueError, IndexError):
                            pass

                # TODO: add this: and date < timezone.localtime() + datetime.timedelta(days=14)
                if date and date > timezone.localtime():
                    calendar.append({"event": data[0].get_text(), "date": data[1].get_text()})
                # only returns the 3 most recent events
                if len(calendar) == 3:
                    break
        return calendar

    def get(self, request):
        return Response(self.get_calendar())


class Events(generics.ListAPIView):
    """
    list:
    Return a list of events belonging to the type
    """

    permission_classes = [AllowAny]
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(event_type=self.kwargs.get("type", ""))


class Analytics(generics.CreateAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsEventSerializer


class HomePageOrdering(generics.ListAPIView):
    """
    list:
    Return a list of orderings for homepage
    """

    permission_classes = [AllowAny]
    serializer_class = HomePageOrderSerializer

    def get_queryset(self):
        return HomePageOrder.objects.all()


class HomePage(APIView):
    """
    GET: provides homepage Cells for mobile
    """

    permission_classes = [IsAuthenticated]

    class Cell:
        def __init__(self, myType, myInfo=None, myWeight=0):
            self.type = myType
            self.info = myInfo
            self.weight = myWeight

        def getCell(self):
            return {"type": self.type, "info": self.info}

    def get(self, request):

        # NOTE: accept arguments: ?version=

        profile = request.user.profile

        # TODO: add user's GSR reservations to Response
        # TODO: add user's courses to Response
        # TODO: add GSR locations to Response
        # TODO: add features (new Penn Mobile features) to Response
        # TODO: add portal posts to Response
        # TODO: add groups_enabled for studyspaces to Response

        cells = []

        # adds laundry preference to home, defaults to Bishop if no preference
        laundry_preference = profile.laundry_preferences.first()
        if laundry_preference:
            cells.append(self.Cell("laundry", {"room_id": laundry_preference.hall_id}, 5))
        else:
            cells.append(self.Cell("laundry", {"room_id": 0}, 5))

        # adds dining preference to home with high priority, defaults to 1920's, Hill, NCH
        dining_preferences = [
            x for x in profile.dining_preferences.values_list("venue_id", flat=True)
        ]

        default_ids = [593, 1442, 636]
        if dining_preferences:
            dining_preferences.extend(default_ids)
            cells.append(self.Cell("dining", {"venues": dining_preferences[:3]}, 100))
        else:
            cells.append(self.Cell("dining", {"venues": default_ids}, 100))

        # gives an update banner if Penn Mobile needs an update
        current_version = request.GET.get("version")
        actual_version = requests.get(
            url="http://itunes.apple.com/lookup?bundleId=org.pennlabs.PennMobile"
        ).json()["results"][0]["version"]
        if current_version and current_version < actual_version:
            cells.append(self.Cell("new-version-released", None, 10000))

        # adds events up to 2 weeks
        cells.append(self.Cell("calendar", {"calendar": Calendar.get_calendar(self)}, 40))

        # adds front page article of DP
        cells.append(self.Cell("news", {"article": News.get_article(self)}, 50))

        # sorts by cell weight
        cells.sort(key=lambda x: x.weight, reverse=True)

        return Response({"cells": [x.getCell() for x in cells]})


class Fitness(generics.ListAPIView):
    """
    GET: Get Fitness Usage
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FitnessSnapshotSerializer

    def get_queryset(self):
        # recent snapshots initialized to empty set
        recent_snapshots = FitnessSnapshot.objects.none()

        # query for all snapshots intiailly, sorted decreasing order of date
        snapshots = FitnessSnapshot.objects.all().order_by("-date")
        rooms = FitnessRoom.objects.all()
        for room in rooms:
            # append to recent snapshots to most recent snapshot for particular room
            recent_snapshots |= snapshots.filter(room=room)[:1]
        return recent_snapshots


class FitnessUsage(APIView):
    def safe_add(self, a, b):
        if a is None:
            return b
        if b is None:
            return a
        return a + b

    def get_usage_on_date(self, room, date, field):
        """
        Returns the number of people in the fitness center on a given date per hour
        """

        # get all snapshots for a given room on a given date and the days before and after
        snapshots = FitnessSnapshot.objects.filter(
            room=room,
            date__gte=date - datetime.timedelta(days=1),
            date__lte=date + datetime.timedelta(days=1),
        )

        usage = [None] * 24  # None represents no data so initialize to all None
        for hour in range(24):
            try:
                # consider the :30 mark of each hour
                hour_date = timezone.make_aware(
                    datetime.datetime.combine(date, datetime.time(hour)), is_dst=None
                ) + datetime.timedelta(minutes=30)
            except NonExistentTimeError:
                # daylight savings time
                continue

            # use snapshots before and after the hour_date to interpolate
            before = snapshots.filter(date__lte=hour_date).order_by("-date").first()
            after = snapshots.filter(date__gte=hour_date).order_by("date").first()

            before_val = getattr(before, field, None)
            after_val = getattr(after, field, None)

            if before_val is None or after_val is None:
                usage[hour] = self.safe_add(before_val, after_val)
                # set to None if latest entry was more than an hour ago (to avoid extrapolation)
                if (
                    after_val is None
                    and before
                    and hour_date - datetime.timedelta(hours=1) > before.date
                ):
                    usage[hour] = None
            else:
                # linear interpolation
                usage[hour] = (
                    before_val
                    + (after_val - before_val)
                    * (hour_date - before.date).total_seconds()
                    / (after.date - before.date).total_seconds()
                )

        if all(x == 0 for x in usage):  # location probably closed - don't count in aggregate
            return [None] * 24
        return usage

    def get_usage(self, room, date, per_hour, group_by, field):
        unit = 1 if group_by == "day" else 7  # skip by 1 or 7 days
        usage_agg = [(None, 0)] * 24  # (sum, count) for each hour
        min_date = timezone.localtime().date()
        max_date = timezone.localtime().date() - datetime.timedelta(days=unit * (per_hour - 1))

        for i in range(per_hour):
            curr = date - datetime.timedelta(days=i * unit)
            usage = self.get_usage_on_date(room, curr, field)  # usage for curr
            # incoporate usage safely considering None (no data) values
            usage_agg = [
                (self.safe_add(acc[0], val), acc[1] + (1 if val is not None else 0))
                for acc, val in zip(usage_agg, usage)
            ]
            # update min and max date if any data was logged
            if any(usage):
                min_date = min(min_date, curr)
                max_date = max(max_date, curr)

        ret = [x[0] / x[1] if x[0] and x[1] else 0 for x in usage_agg]
        return ret, min_date, max_date

    def get(self, request, room_id):
        room = get_object_or_404(FitnessRoom, pk=room_id)
        try:
            if (date := request.query_params.get("date")) is None:
                date = timezone.localtime().date()
            else:
                date = timezone.make_aware(datetime.datetime.strptime(date, "%Y-%m-%d")).date()
        except ValueError:
            return Response({"detail": "date must be in the format YYYY-MM-DD"}, status=400)

        try:
            per_hour = int(request.query_params.get("per_hour", 1))
        except ValueError:
            return Response({"detail": "per_hour must be an integer"}, status=400)

        if (group_by := request.query_params.get("group_by", "day")) not in ("day", "week"):
            return Response({"detail": "group_by must be either 'day' or 'week'"}, status=400)

        if (field := request.query_params.get("field", "count")) not in ("count", "capacity"):
            return Response({"detail": "field must be either 'count' or 'capacity'"}, status=400)

        res, min_date, max_date = self.get_usage(room, date, per_hour, group_by, field)
        return Response(
            {
                "room_name": room.name,
                "start_date": min_date,
                "end_date": max_date,
                "usage": {i: x for i, x in enumerate(res)},
            }
        )


class UniqueCounterView(APIView):
    """
    get: determines number of unique visits for a given post or poll
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = dict()
        if "post_id" in request.query_params:
            query["post__id"] = request.query_params["post_id"]
        if "poll_id" in request.query_params:
            query["poll__id"] = request.query_params["poll_id"]
        if len(query) != 1:
            return Response({"detail": "require 1 id out of post_id or poll_id"}, status=400)
        query["is_interaction"] = (
            request.query_params.get("is_interaction", "false").lower() == "true"
        )
        return Response({"count": AnalyticsEvent.objects.filter(**query).count()})