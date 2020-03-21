from datetime import datetime, timedelta

from dining.constants import map_to_pretty
from django.db.models import Sum
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from legacy.models import Account, DiningBalance, DiningTransaction
from options.models import Option, get_option, get_value
from pytz import timezone
from rest_framework.views import APIView

from studentlife.utils import date_iso_eastern, get_new_start_end


class Dashboard(APIView):
    def get(self, request, format=None):
        if not self.request.user.is_authenticated:
            return HttpResponseForbidden()

        pennid = request.user.username

        try:
            uid = Account.objects.get(pennid=pennid).id
        except Account.DoesNotExist:
            return HttpResponseBadRequest()

        json = self.balance(uid)

        start, end = self.get_semester_start_end()

        eastern = timezone("US/Eastern")
        start = start.replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        json["start-of-semester"] = date_iso_eastern(start)
        json["end-of-semester"] = date_iso_eastern(end)

        json["cards"] = {"recent-transactions": self.recent_transactions_card(uid)}

        average_balances = self.get_average_balances(uid, start)

        if average_balances:
            json["cards"].update({"daily-average": average_balances})

        dollar_prediction = self.get_prediction_dollars(uid, start, end)

        if dollar_prediction:
            json["cards"].update({"predictions-graph-dollars": dollar_prediction})

        swipes_prediction = self.get_prediction_swipes(uid, start, end)

        if swipes_prediction:
            json["cards"].update({"predictions-graph-swipes": swipes_prediction})

        frequent_locations = self.get_frequent_locations(uid, start, end)

        if frequent_locations:
            json["cards"].update({"frequent-locations": frequent_locations})

        return JsonResponse(json)

    def balance(self, uid):
        balance = DiningBalance.objects.filter(account=uid).order_by("-created_at")
        latest = balance[0]
        return {
            "swipes": latest.swipes,
            "dining-dollars": latest.dining_dollars,
            "guest-swipes": latest.guest_swipes,
        }

    def recent_transactions_card(self, uid):

        card = {
            "type": "recent-transactions",
            "data": [],
        }

        transactions = DiningTransaction.objects.filter(account=uid).order_by("-date")

        transactions = transactions[0:5]

        eastern = timezone("US/Eastern")

        for transaction in transactions:
            card["data"].append(
                {
                    "location": map_to_pretty(transaction.description),
                    "date": transaction.date.replace(tzinfo=eastern).isoformat(),
                    "balance": transaction.balance,
                    "amount": transaction.amount,
                }
            )

        return card

    def get_semester_start_end(self):

        current_start = get_value("semester_start")
        current_end = get_value("semester_end")

        try:
            current_start = datetime.strptime(current_start, "%Y-%m-%d")
            current_end = datetime.strptime(current_end, "%Y-%m-%d")
        except ValueError:
            pass

        if current_start is not None and current_end is not None and current_end > datetime.now():
            return current_start, current_end
        else:
            if current_start is None or current_end is None:
                new_start_option = Option(key="semester_start", value="")
                new_end_option = Option(key="semester_end", value="")
            else:
                new_start_option = get_option("semester_start")
                new_end_option = get_option("semester_end")

            new_start, new_end = get_new_start_end()

            new_start_option.value = new_start.strftime("%Y-%m-%d")
            new_start_option.save()

            new_end_option.value = new_end.strftime("%Y-%m-%d")
            new_end_option.save()

            return (
                datetime.strptime(get_value("semester_start"), "%Y-%m-%d"),
                datetime.strptime(get_value("semester_end"), "%Y-%m-%d"),
            )

    def get_average_balances(self, uid, start_of_semester):

        two_weeks_ago = datetime.now() - timedelta(days=14)
        eastern = timezone("US/Eastern")
        two_weeks_ago = two_weeks_ago.replace(
            tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0
        )

        if two_weeks_ago < start_of_semester:
            return None

        transactions = DiningTransaction.objects.filter(
            account=uid, date__gte=two_weeks_ago
        ).order_by("date")

        transaction_dict = {}

        for transaction in transactions:
            date = transaction.date.replace(
                tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0
            )
            if date not in transaction_dict:
                transaction_dict[date] = []

            transaction_dict[date].append(transaction.amount)

        transaction_averages = {}

        for date, amounts in transaction_dict.items():
            amounts = [x for x in amounts if x < 0]
            if len(amounts) > 0:
                transaction_averages[date] = round(sum(amounts) / len(amounts), 2)

        for i in range(14):
            day = two_weeks_ago + timedelta(days=i + 1)

            if day not in transaction_averages.keys():
                transaction_averages[day] = 0

        card = {"type": "daily-average", "data": {"this-week": [], "last-week": []}}

        for i, (date, average) in enumerate(sorted(transaction_averages.items(), reverse=True)):
            if i < 7:
                card["data"]["this-week"].append({"date": date.isoformat(), "average": average})
            elif i < 14:
                card["data"]["last-week"].append({"date": date.isoformat(), "average": average})
            else:
                break

        return card

    def get_prediction_dollars(self, uid, start, end):

        transactions = (
            DiningTransaction.objects.filter(account=uid, date__gte=start,)
            .order_by("-date")
            .exclude(description__icontains="meal_plan")
        )

        if len(transactions) < 10:
            return None

        card = {
            "type": "predictions-graph-dollars",
            "start-of-semester": start.isoformat(),
            "end-of-semester": end.isoformat(),
            "data": [],
        }

        balance = transactions[0].balance

        if balance != 0:

            transactions_negative = transactions.filter(amount__lte=0)

            eastern = timezone("US/Eastern")
            now = datetime.now().replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
            days_since_start = (now - start).days
            spend_rate = (
                sum([-1 * x for x in transactions_negative.values_list("amount", flat=True)])
                / days_since_start
            )

            days_left = int(balance / spend_rate)

            broke_day = now + timedelta(days=days_left)

            card["predicted-zero-date"] = broke_day.isoformat()

            if broke_day > end:
                days_to_end = (end - now).days
                card["balance-at-semester-end"] = spend_rate * days_to_end

        for transaction in transactions:
            card["data"].append(
                {"date": transaction.date.isoformat(), "balance": transaction.balance}
            )

        card["data"] = sorted(card["data"], key=lambda k: k["date"])

        return card

    def get_prediction_swipes(self, uid, start, end):

        balances = DiningBalance.objects.filter(account_id=uid, created_at__gte=start,).order_by(
            "-created_at"
        )

        card = {
            "type": "predictions-graph-swipes",
            "start-of-semester": start.isoformat(),
            "end-of-semester": end.isoformat(),
            "data": [],
        }

        balance = balances[0].swipes

        if balance != 0:

            swipe_balances = []

            for balance in balances:
                swipe_balances.append(balance.swipes)

            spent = 0

            for i, balance in enumerate(swipe_balances):
                if i == 0:
                    continue
                else:
                    if swipe_balances[i] < swipe_balances[i - 1]:
                        continue
                    else:
                        spent += swipe_balances[i] - swipe_balances[i - 1]

            eastern = timezone("US/Eastern")
            now = datetime.now().replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
            days_since_start = (now - start).days
            spend_rate = spent / days_since_start

            days_left = int(balance / spend_rate)

            broke_day = now + timedelta(days=days_left)

            card["predicted-zero-date"] = broke_day.isoformat()

            if broke_day > end:
                days_to_end = (end - now).days
                card["balance-at-semester-end"] = round(spend_rate * days_to_end, 0)

        for balance in balances:
            card["data"].append({"date": balance.created_at.isoformat(), "balance": balance.swipes})

        card["data"] = sorted(card["data"], key=lambda k: k["date"])

        return card

    def get_frequent_locations(self, uid, start, end):

        transactions = DiningTransaction.objects.filter(
            account=uid, date__gte=start, amount__lt=0
        ).exclude(description__icontains="meal_plan")

        if len(transactions) < 10:
            return None

        venue_spends = (
            transactions.values("description")
            .annotate(total_spend_venue=Sum("amount"))
            .order_by("total_spend_venue")
        )

        card = {
            "type": "frequent-locations",
            "data": [],
        }

        venues = [
            {
                "location": map_to_pretty(venue["description"]),
                "week": 0,
                "month": 0,
                "semester": venue["total_spend_venue"] * -1,
            }
            for venue in venue_spends
        ][:5]

        eastern = timezone("US/Eastern")
        now = datetime.now().replace(tzinfo=eastern, hour=0, minute=0, second=0, microsecond=0)
        for transaction in transactions:

            days_since_transaction = (now - transaction.date).days
            venue_index = next(
                (
                    index
                    for (index, d) in enumerate(venues)
                    if d["location"] == map_to_pretty(transaction.description)
                ),
                None,
            )

            if venue_index is None:
                continue

            transaction.amount *= -1

            if days_since_transaction <= 7:
                venues[venue_index]["week"] += transaction.amount
            elif days_since_transaction <= 30:
                venues[venue_index]["month"] += transaction.amount

        for venue in venues:
            venue["week"] = round(venue["week"], 2)
            venue["month"] = round(venue["month"], 2)
            venue["semester"] = round(venue["semester"], 2)

        card["data"] = venues

        return card
