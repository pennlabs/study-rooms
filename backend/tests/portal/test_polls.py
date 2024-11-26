import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Poll, PollOption, PollVote, TargetPopulation
from utils.email import get_backend_manager_emails


User = get_user_model()


def mock_get_user_clubs(*args, **kwargs):
    with open("tests/portal/get_user_clubs.json") as data:
        return json.load(data)


def mock_get_user_info(*args, **kwargs):
    with open("tests/portal/get_user_info.json") as data:
        return json.load(data)


def mock_get_null_user_info(*args, **kwargs):
    with open("tests/portal/get_null_user_info.json") as data:
        return json.load(data)


def mock_get_club_info(*args, **kwargs):
    with open("tests/portal/get_club_info.json") as data:
        return json.load(data)


class TestUserClubs(TestCase):
    """Test User and Club information"""

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

    @mock.patch("portal.views.get_user_info", mock_get_user_info)
    def test_user_info(self):
        response = self.client.get("/portal/user/")
        res_json = json.loads(response.content)
        self.assertEqual(12345678, res_json["user"]["pennid"])

    @mock.patch("portal.views.get_club_info", mock_get_club_info)
    @mock.patch("portal.views.get_user_clubs", mock_get_user_clubs)
    def test_user_clubs(self):
        response = self.client.get("/portal/clubs/")
        res_json = json.loads(response.content)
        self.assertEqual("pennlabs", res_json["clubs"][0]["code"])


class TestPolls(TestCase):
    """Tests Create/Update/Retrieve for Polls and Poll Options"""

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    def setUp(self):
        call_command("load_target_populations", "--years", "2022, 2023, 2024, 2025")
        self.target_id = TargetPopulation.objects.get(population="2024").id
        year = TargetPopulation.objects.get(population="2024").id
        major = TargetPopulation.objects.get(population="Computer Science, BSE").id
        school = TargetPopulation.objects.get(
            population="School of Engineering and Applied Science"
        ).id
        degree = TargetPopulation.objects.get(population="BACHELORS").id
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)
        # creates an approved poll to work with
        payload = {
            "club_code": "pennlabs",
            "question": "How is your day",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "club_comment": "hello!",
            "target_populations": [year, major, school, degree],
        }
        self.client.post("/portal/polls/", payload)

        bad_year = TargetPopulation.objects.get(population="2025").id
        payload = {
            "club_code": "pennlabs",
            "question": "Bad poll",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "club_comment": "hello not hello!!",
            "target_populations": [bad_year, major, school, degree],
        }
        self.client.post("/portal/polls/", payload)

        for poll in Poll.objects.all():
            poll.status = Poll.STATUS_APPROVED
            poll.save()

        poll_1 = Poll.objects.get(question="How is your day")
        self.poll_id = poll_1.id

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    def test_create_poll(self):
        # creates an unapproved poll
        payload = {
            "club_code": "pennlabs",
            "question": "How is this question? 2",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 2",
            "target_populations": [],
        }
        response = self.client.post("/portal/polls/", payload)
        res_json = json.loads(response.content)
        # asserts that poll was created and that the admin comment cannot be made
        self.assertEqual(3, Poll.objects.all().count())
        self.assertEqual("pennlabs", res_json["club_code"])
        self.assertEqual(None, Poll.objects.get(id=res_json["id"]).admin_comment)

    @mock.patch("portal.views.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    def test_update_poll(self):
        payload = {
            "question": "New question",
        }
        response = self.client.patch(f"/portal/polls/{self.poll_id}/", payload)
        res_json = json.loads(response.content)
        # asserts that the update worked
        self.assertEqual(self.poll_id, res_json["id"])
        self.assertEqual("New question", Poll.objects.get(id=self.poll_id).question)

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    def test_browse(self):
        payload = {
            "club_code": "pennlabs",
            "question": "How is this question? 2",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 2",
            "target_populations": [],
        }
        self.client.post("/portal/polls/", payload)
        # asserts that you can only see approved polls
        response = self.client.post("/portal/polls/browse/", {"id_hash": 1})
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual(3, Poll.objects.all().count())

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.logic.get_user_info", mock_get_null_user_info)
    def test_null_user_info_browse(self):
        # Asserts that a user with empty user info can access all available polls
        response = self.client.post("/portal/polls/browse/", {"id_hash": 1})
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        self.assertEqual(2, Poll.objects.all().count())

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    def test_create_option(self):
        payload_1 = {"poll": self.poll_id, "choice": "yes!"}
        payload_2 = {"poll": self.poll_id, "choice": "no!"}
        self.client.post("/portal/options/", payload_1)
        self.client.post("/portal/options/", payload_2)
        self.assertEqual(2, PollOption.objects.all().count())
        # asserts options were created and were placed to right poll
        for poll_option in PollOption.objects.all():
            self.assertEqual(Poll.objects.get(id=self.poll_id), poll_option.poll)
        response = self.client.post("/portal/polls/browse/", {"id_hash": 1})
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json[0]["options"]))

    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.views.get_user_clubs", mock_get_user_clubs)
    def test_update_option(self):
        payload_1 = {"poll": self.poll_id, "choice": "yes!"}
        response = self.client.post("/portal/options/", payload_1)
        res_json = json.loads(response.content)
        self.assertEqual("yes!", PollOption.objects.get(id=res_json["id"]).choice)
        payload_2 = {"poll": self.poll_id, "choice": "no!"}
        # checks that poll's option was changed
        self.client.patch(f'/portal/options/{res_json["id"]}/', payload_2)
        self.assertEqual("no!", PollOption.objects.get(id=res_json["id"]).choice)

    def test_review_poll(self):
        Poll.objects.create(
            club_code="pennlabs",
            question="hello?",
            expire_date=timezone.now() + datetime.timedelta(days=3),
        )
        admin = User.objects.create_superuser("admin@example.com", "admin", "admin")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/portal/polls/review/")
        res_json = json.loads(response.content)
        # checks that admin can see unapproved polls
        self.assertEqual(1, len(res_json))
        self.assertEqual(3, Poll.objects.all().count())

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    def test_more_than_five_options(self):
        payload_1 = {"poll": self.poll_id, "choice": "1"}
        payload_2 = {"poll": self.poll_id, "choice": "2"}
        payload_3 = {"poll": self.poll_id, "choice": "3"}
        payload_4 = {"poll": self.poll_id, "choice": "4"}
        payload_5 = {"poll": self.poll_id, "choice": "5"}
        self.client.post("/portal/options/", payload_1)
        self.client.post("/portal/options/", payload_2)
        self.client.post("/portal/options/", payload_3)
        self.client.post("/portal/options/", payload_4)
        self.client.post("/portal/options/", payload_5)
        self.assertEqual(5, PollOption.objects.all().count())
        # asserts options were created and were placed to right poll
        for poll_option in PollOption.objects.all():
            self.assertEqual(Poll.objects.get(id=self.poll_id), poll_option.poll)
        response = self.client.post("/portal/polls/browse/", {"id_hash": 1})
        res_json = json.loads(response.content)
        self.assertEqual(5, len(res_json[0]["options"]))
        # adding more than 5 options to same poll should not be allowed
        payload_6 = {"poll": self.poll_id, "choice": "6"}
        response = self.client.post("/portal/options/", payload_6)
        self.assertEqual(5, PollOption.objects.all().count())

    def test_option_vote_view(self):
        response = self.client.get(f"/portal/polls/{self.poll_id}/option_view/")
        res_json = json.loads(response.content)
        self.assertEqual("pennlabs", res_json["club_code"])
        # test that options key is in response
        self.assertIn("options", res_json)

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("utils.email.send_automated_email.delay_on_commit")
    def test_send_email_on_create(self, mock_send_email):
        payload = {
            "club_code": "pennlabs",
            "question": "How is this question? 2",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 2",
            "target_populations": [],
        }
        self.client.post("/portal/polls/", payload)

        mock_send_email.assert_called_once()
        self.assertEqual(mock_send_email.call_args[0][1], get_backend_manager_emails())

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("utils.email.send_automated_email.delay_on_commit")
    def test_send_email_on_status_change(self, mock_send_email):
        payload = {
            "club_code": "pennlabs",
            "question": "How is this question? 2",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 2",
            "target_populations": [],
        }
        self.client.force_authenticate(user=self.test_user)
        self.client.post("/portal/polls/", payload)
        mock_send_email.assert_called_once()

        poll = Poll.objects.last()
        poll.status = Poll.STATUS_REVISION
        poll.save()

        self.assertEqual(mock_send_email.call_count, 2)
        self.assertEqual(mock_send_email.call_args[0][1], [self.test_user.email])


class TestPollVotes(TestCase):
    """Tests Create/Update Polls and History"""

    def setUp(self):
        call_command("load_target_populations", "--years", "2022, 2023, 2024, 2025")
        self.target_id = TargetPopulation.objects.get(population="2024").id

        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

        # creates 4 polls, each with 3 options
        # p1, p4 user is in target population
        p1 = Poll.objects.create(
            club_code="pennlabs",
            question="poll question 1",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            status=Poll.STATUS_APPROVED,
        )
        p1.target_populations.set(TargetPopulation.objects.all())
        p1.save()
        self.p1_id = p1.id
        p1_op1 = PollOption.objects.create(poll=p1, choice="choice 1")
        self.p1_op1_id = p1_op1.id
        PollOption.objects.create(poll=p1, choice="choice 2")
        p1_op3 = PollOption.objects.create(poll=p1, choice="choice 3")
        self.p1_op3_id = p1_op3.id
        p2 = Poll.objects.create(
            club_code="pennlabs",
            question="poll question 2",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            status=Poll.STATUS_APPROVED,
        )
        self.p2_id = p2.id
        PollOption.objects.create(poll=p2, choice="choice 4")
        PollOption.objects.create(poll=p2, choice="choice 5")
        PollOption.objects.create(poll=p2, choice="choice 6")
        p3 = Poll.objects.create(
            club_code="pennlabs",
            question="poll question 3",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            status=Poll.STATUS_APPROVED,
        )
        self.p3_id = p3.id
        PollOption.objects.create(poll=p3, choice="choice 7")
        PollOption.objects.create(poll=p3, choice="choice 8")
        PollOption.objects.create(poll=p3, choice="choice 9")
        p4 = Poll.objects.create(
            club_code="pennlabs",
            question="poll question 4",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            status=Poll.STATUS_APPROVED,
        )
        p4.target_populations.set(TargetPopulation.objects.all())
        p4.save()
        self.p4_id = p4.id
        p4_op1 = PollOption.objects.create(poll=p4, choice="choice 10")
        self.p4_op1_id = p4_op1.id
        PollOption.objects.create(poll=p4, choice="choice 11")
        PollOption.objects.create(poll=p4, choice="choice 12")

    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    def test_create_vote(self):
        payload_1 = {"id_hash": 1, "poll_options": [self.p1_op1_id]}
        response = self.client.post("/portal/votes/", payload_1)
        res_json = json.loads(response.content)
        # tests that voting works
        self.assertIn(self.p1_op1_id, res_json["poll_options"])
        self.assertEqual(1, PollVote.objects.all().count())
        self.assertEqual("1", PollVote.objects.all().first().id_hash)
        self.assertIn(
            TargetPopulation.objects.get(id=self.target_id),
            PollVote.objects.all().first().target_populations.all(),
        )

    def test_recent_poll_empty(self):
        response = self.client.post("/portal/votes/recent/", {"id_hash": 1})
        res_json = json.loads(response.content)
        self.assertIsNone(res_json["created_date"])
        self.assertIsNone(res_json["poll"]["created_date"])

    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    def test_recent_poll(self):
        # answer poll
        payload_1 = {"id_hash": 1, "poll_options": [self.p1_op1_id]}
        self.client.post("/portal/votes/", payload_1)
        response = self.client.post("/portal/votes/recent/", {"id_hash": 1})
        res_json = json.loads(response.content)
        # assert that payload1 poll answered is most recent
        self.assertEquals(self.p1_id, res_json["poll"]["id"])
        # answer another poll
        payload_2 = {"id_hash": 1, "poll_options": [self.p4_op1_id]}
        self.client.post("/portal/votes/", payload_2)
        response2 = self.client.post("/portal/votes/recent/", {"id_hash": 1})
        res_json2 = json.loads(response2.content)
        # assert newly answered poll is most recent
        self.assertEquals(self.p4_id, res_json2["poll"]["id"])

    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    def test_all_votes(self):
        payload_1 = {"id_hash": 1, "poll_options": [self.p1_op1_id]}
        self.client.post("/portal/votes/", payload_1)
        payload_2 = {"id_hash": 1, "poll_options": [self.p4_op1_id]}
        self.client.post("/portal/votes/", payload_2)
        # Assert there are exactly 2 votes, and that the first id is greater
        # than the second, because we sort in decreasing order of created date
        response = self.client.post("/portal/votes/all/", {"id_hash": 1})
        res_json = json.loads(response.content)
        self.assertEquals(2, len(res_json))
        self.assertGreater(res_json[0]["id"], res_json[1]["id"])

    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    def test_demographic_breakdown(self):
        # plugging in votes for breakdown
        payload_1 = {"id_hash": 1, "poll_options": [self.p1_op1_id]}
        self.client.post("/portal/votes/", payload_1)
        payload_2 = {"id_hash": 2, "poll_options": [self.p1_op1_id]}
        self.client.post("/portal/votes/", payload_2)
        payload_3 = {"id_hash": 3, "poll_options": [self.p1_op1_id]}
        self.client.post("/portal/votes/", payload_3)

        response = self.client.get(f"/portal/vote-statistics/{self.p1_id}/")
        res_json = json.loads(response.content)

        self.assertIn("time_series", res_json)
        self.assertEqual(1, len(res_json["time_series"]))
        self.assertIn("poll_statistics", res_json)
        self.assertEqual(3, len(res_json["poll_statistics"]))
        self.assertIn("Computer Science, BSE", res_json["poll_statistics"][0]["breakdown"]["MAJOR"])
        self.assertEquals(
            3, res_json["poll_statistics"][0]["breakdown"]["MAJOR"]["Computer Science, BSE"]
        )

        self.assertIn(
            "School of Engineering and Applied Science",
            res_json["poll_statistics"][0]["breakdown"]["SCHOOL"],
        )
