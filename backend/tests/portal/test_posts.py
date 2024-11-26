import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Post, TargetPopulation
from utils.email import get_backend_manager_emails


User = get_user_model()


def mock_get_user_clubs(*args, **kwargs):
    with open("tests/portal/get_user_clubs.json") as data:
        return json.load(data)


def mock_get_no_clubs(*args, **kwargs):
    return []


def mock_get_user_info(*args, **kwargs):
    with open("tests/portal/get_user_info.json") as data:
        return json.load(data)


def mock_get_club_info(*args, **kwargs):
    with open("tests/portal/get_club_info.json") as data:
        return json.load(data)


class TestPosts(TestCase):
    """Tests Created/Update/Retrieve for Posts"""

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    def setUp(self):
        call_command("load_target_populations", "--years", "2022, 2023, 2024, 2025")
        self.target_id = TargetPopulation.objects.get(population="2024").id
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

        payload = {
            "club_code": "pennlabs",
            "title": "Test Title 1",
            "subtitle": "Test Subtitle 1",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "club_comment": "hello!",
            "admin_comment": "comment 1",
        }
        self.client.post("/portal/posts/", payload)
        post_1 = Post.objects.all().first()
        post_1.status = Post.STATUS_APPROVED
        post_1.save()
        self.post_id = post_1.id

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    def test_create_post(self):
        # Creates an unapproved post
        payload = {
            "club_code": "pennlabs",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "comment 2",
        }
        response = self.client.post("/portal/posts/", payload)
        res_json = json.loads(response.content)
        # asserts that post was created and that the admin comment cannot be made
        self.assertEqual(2, Post.objects.all().count())
        self.assertEqual("pennlabs", res_json["club_code"])
        self.assertEqual(None, Post.objects.get(id=res_json["id"]).admin_comment)

    @mock.patch("portal.serializers.get_user_clubs", mock_get_no_clubs)
    def test_fail_post(self):
        # Creates an unapproved post
        payload = {
            "club_code": "pennlabs",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "comment 2",
        }
        response = self.client.post("/portal/posts/", payload)
        res_json = json.loads(response.content)
        # should not create post under pennlabs if not aprt of pennlabs
        self.assertEqual(
            "You do not have access to create a Post under this club.", res_json["detail"]
        )

    @mock.patch("portal.views.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    def test_update_post(self):
        payload = {"title": "New Test Title 3"}
        response = self.client.patch(f"/portal/posts/{self.post_id}/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(self.post_id, res_json["id"])
        self.assertEqual("New Test Title 3", Post.objects.get(id=self.post_id).title)
        # since the user is not an admin, approved should be set to false after update
        self.assertEqual(Post.STATUS_DRAFT, res_json["status"])

    @mock.patch("portal.views.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    def test_update_post_admin(self):
        admin = User.objects.create_superuser("admin@upenn.edu", "admin", "admin")
        self.client.force_authenticate(user=admin)
        payload = {"title": "New Test Title 3"}
        response = self.client.patch(f"/portal/posts/{self.post_id}/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(self.post_id, res_json["id"])
        self.assertEqual(Post.STATUS_APPROVED, res_json["status"])

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.logic.get_user_info", mock_get_user_info)
    def test_browse(self):
        payload = {
            "club_code": "pennlabs",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "not approved",
        }
        self.client.post("/portal/posts/", payload)
        response = self.client.get("/portal/posts/browse/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual(2, Post.objects.all().count())

    def test_review_post_no_admin_comment(self):
        # No admin comment
        Post.objects.create(
            club_code="notpennlabs",
            title="Test title 2",
            subtitle="Test subtitle 2",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
        )
        admin = User.objects.create_superuser("admin@upenn.edu", "admin", "admin")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/portal/posts/review/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("notpennlabs", res_json[0]["club_code"])
        self.assertEqual(2, Post.objects.all().count())

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("utils.email.send_automated_email.delay_on_commit")
    def test_send_email_on_create(self, mock_send_email):
        payload = {
            "club_code": "pennlabs",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "comment 2",
        }
        self.client.post("/portal/posts/", payload)
        mock_send_email.assert_called_once()
        self.assertEqual(mock_send_email.call_args[0][1], get_backend_manager_emails())

    @mock.patch("portal.serializers.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("utils.email.send_automated_email.delay_on_commit")
    def test_send_email_on_status_change(self, mock_send_email):
        payload = {
            "club_code": "pennlabs",
            "title": "Test Title 2",
            "subtitle": "Test Subtitle 2",
            "target_populations": [self.target_id],
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "created_at": timezone.localtime(),
            "admin_comment": "comment 2",
        }
        self.client.force_authenticate(user=self.test_user)
        self.client.post("/portal/posts/", payload)
        mock_send_email.assert_called_once()

        post = Post.objects.last()
        post.status = Post.STATUS_APPROVED
        post.save()

        self.assertEqual(mock_send_email.call_count, 2)
        self.assertEqual(mock_send_email.call_args[0][1], [post.creator.email])
