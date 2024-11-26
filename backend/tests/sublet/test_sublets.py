import json
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.core.files.storage import Storage
from django.test import TestCase
from rest_framework.test import APIClient

from sublet.models import Amenity, Offer, Sublet, SubletImage


User = get_user_model()


class TestSublets(TestCase):
    """Tests Create/Update/Retrieve/List for sublets"""

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        test_user = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            self.test_sublet1 = Sublet.objects.create(subletter=self.user, **data[0])
            self.test_sublet2 = Sublet.objects.create(subletter=test_user, **data[1])

        storage_mock = MagicMock(spec=Storage, name="StorageMock")
        storage_mock.generate_filename = lambda filename: filename
        storage_mock.save = MagicMock(side_effect=lambda name, *args, **kwargs: name)
        storage_mock.url = MagicMock(name="url")
        storage_mock.url.return_value = "http://penn-mobile.com/mock-image.png"
        SubletImage._meta.get_field("image").storage = storage_mock

    def test_create_sublet(self):
        # Create a new sublet using the serializer
        payload = {
            "title": "Test Sublet1",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": "1.5",
            "description": "This is a test sublet.",
            "external_link": "https://example.com",
            "price": 1000,
            "negotiable": True,
            "expires_at": "3000-02-01T10:48:02-05:00",
            "start_date": "3000-04-09",
            "end_date": "3000-08-07",
            "amenities": ["Amenity1", "Amenity2"],
            "is_published": True,
        }
        response = self.client.post("/sublet/properties/", payload)
        res_json = json.loads(response.content)
        match_keys = [
            "title",
            "address",
            "beds",
            "baths",
            "description",
            "external_link",
            "price",
            "negotiable",
            "expires_at",
            "start_date",
            "end_date",
            "amenities",
            "is_published",
        ]
        [self.assertEqual(payload[key], res_json[key]) for key in match_keys]
        self.assertIn("id", res_json)
        self.assertEqual(self.user.id, res_json["subletter"])
        self.assertEqual(2, len(res_json["amenities"]))
        self.assertIn("images", res_json)

    def test_create_sublet_with_profanity(self):
        # Payload with profanity in the title and description
        payload_with_profanity = {
            "title": "fuck",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": "1.5",
            "description": "shit.",
            "external_link": "https://example.com",
            "price": 1000,
            "negotiable": True,
            "expires_at": "3000-02-01T10:48:02-05:00",
            "start_date": "3000-01-01",
            "end_date": "3000-12-31",
            "amenities": ["Amenity1", "Amenity2"],
        }

        response = self.client.post("/sublet/properties/", payload_with_profanity)

        self.assertEqual(response.status_code, 400)

        res_json = response.json()
        self.assertIn("title", res_json)
        self.assertIn("description", res_json)
        self.assertEqual(res_json["title"][0], "The title contains inappropriate language.")
        self.assertEqual(
            res_json["description"][0], "The description contains inappropriate language."
        )

    def test_update_sublet(self):
        # Create a sublet to be updated
        payload = {
            "title": "Test Sublet2",
            "address": "1234 Old Street",
            "beds": 2,
            "baths": 1,
            "description": "This is an old sublet.",
            "external_link": "https://example.com",
            "price": 1000,
            "negotiable": True,
            "expires_at": "3000-02-01T10:48:02-05:00",
            "start_date": "3000-04-09",
            "end_date": "3000-08-07",
            "amenities": ["Amenity1", "Amenity2"],
        }
        response = self.client.post("/sublet/properties/", payload)
        old_id = json.loads(response.content)["id"]
        # Update the sublet using the serializer
        data = {"title": "New Title", "beds": 3, "amenities": ["Amenity1"], "address": ""}
        response = self.client.patch(f"/sublet/properties/{str(old_id)}/", data)
        res_json = json.loads(response.content)
        self.assertEqual(3, res_json["beds"])
        self.assertEqual(old_id, Sublet.objects.all().last().id)
        self.assertEqual("New Title", Sublet.objects.get(id=old_id).title)
        self.assertEqual("New Title", res_json["title"])
        self.assertEqual(1, len(res_json["amenities"]))
        payload["address"] = ""
        payload["is_published"] = True
        response = self.client.patch(f"/sublet/properties/{str(old_id)}/", payload)
        self.assertEqual(400, response.status_code)
        payload["is_published"] = False
        response = self.client.patch(f"/sublet/properties/{str(old_id)}/", payload)
        self.assertEqual(200, response.status_code)
        response = self.client.patch(f"/sublet/properties/{str(old_id)}/", {"is_published": True})
        self.assertEqual(400, response.status_code)

    def test_browse_sublets(self):
        response = self.client.get("/sublet/properties/")
        res_json = json.loads(response.content)
        first_length = len(res_json)
        payload = {
            "title": "Test Sublet1",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": 1,
            "description": "This is a test sublet.",
            "external_link": "https://example.com",
            "price": 1000,
            "negotiable": True,
            "expires_at": "3000-02-01T10:48:02-05:00",
            "start_date": "3000-04-09",
            "end_date": "3000-08-07",
            "amenities": ["Amenity1", "Amenity2"],
            "is_published": True,
        }
        response = self.client.post("/sublet/properties/", payload)
        old_id = json.loads(response.content)["id"]
        response = self.client.get("/sublet/properties/")
        res_json = json.loads(response.content)
        self.assertEqual(1 + first_length, len(res_json))
        sublet = Sublet.objects.get(id=old_id)
        self.assertEqual(sublet.title, "Test Sublet1")
        self.assertEqual(sublet.address, "1234 Test Street")
        self.assertEqual(sublet.beds, 2)
        self.assertEqual(sublet.baths, 1)

    def test_browse_filtered(self):
        payload = {
            "title": "Test Sublet2",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": 1,
            "description": "This is a test sublet.",
            "external_link": "https://example.com",
            "price": 500,
            "negotiable": True,
            "expires_at": "3000-02-01T10:48:02-05:00",
            "start_date": "3000-04-09",
            "end_date": "3000-08-07",
            "amenities": ["Amenity1", "Amenity2"],
            "is_published": True,
        }
        response = self.client.post("/sublet/properties/", payload)
        old_id = json.loads(response.content)["id"]
        payload = {
            "title": "Sublet2",
            "max_price": 999,
            "min_price": 499,
        }
        response = self.client.get("/sublet/properties/", payload)
        res_json = json.loads(response.content)
        sublet = res_json[0]
        self.assertEqual(1, len(res_json))
        self.assertEqual(old_id, sublet["id"])
        self.assertEqual("1234 Test Street", sublet["address"])
        self.assertEqual("Test Sublet2", sublet["title"])
        response = self.client.get("/sublet/properties/", {"ends_before": "2025-05-01"})
        old_length = len(json.loads(response.content))
        payload = {
            "title": "Test Sublet1",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": 1,
            "description": "This is a test sublet.",
            "external_link": "https://example.com",
            "price": 1000,
            "negotiable": True,
            "expires_at": "3000-02-01T10:48:02-05:00",
            "start_date": "3000-04-09",
            "end_date": "5000-08-07",
            "amenities": ["Amenity1", "Amenity2"],
        }
        self.client.post("/sublet/properties/", payload)
        response = self.client.get("/sublet/properties/", {"ends_before": "2025-05-01"})
        res_json = json.loads(response.content)
        self.assertEqual(old_length, len(res_json))

    def test_browse_sublet(self):
        # browse single sublet by id
        payload = {
            "title": "Test Sublet2",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": "1.5",
            "description": "This is a test sublet.",
            "external_link": "https://example.com",
            "price": 1000,
            "negotiable": True,
            "expires_at": "3000-02-01T10:48:02-05:00",
            "start_date": "3000-04-09",
            "end_date": "3000-08-07",
            "amenities": ["Amenity1", "Amenity2"],
        }
        self.client.post("/sublet/properties/", payload)
        test_sublet = Sublet.objects.get(subletter=self.user, title="Test Sublet2")
        response = self.client.get(f"/sublet/properties/{str(test_sublet.id)}/")
        res_json = json.loads(response.content)
        self.assertEqual(res_json["title"], "Test Sublet2")
        self.assertEqual(res_json["address"], "1234 Test Street")
        self.assertEqual(res_json["beds"], 2)
        self.assertEqual(res_json["baths"], "1.5")
        self.assertEqual(res_json["amenities"], ["Amenity1", "Amenity2"])

    def test_delete_sublet(self):
        sublets_count = Sublet.objects.all().count()
        self.client.delete(f"/sublet/properties/{str(self.test_sublet1.id)}/")
        self.assertEqual(sublets_count - 1, Sublet.objects.all().count())
        self.assertFalse(Sublet.objects.filter(id=1).exists())

    def test_amenities(self):
        response = self.client.get("/sublet/amenities/")
        res_json = json.loads(response.content)
        for i in range(1, 6):
            self.assertIn(f"Amenity{i}", res_json)

    def test_create_image(self):
        with open("tests/sublet/mock_image.jpg", "rb") as image:
            response = self.client.post(
                f"/sublet/properties/{str(self.test_sublet1.id)}/images/", {"images": image}
            )
            self.assertEqual(response.status_code, 201)
            images = Sublet.objects.get(id=self.test_sublet1.id).images.all()
            self.assertTrue(images.exists())
            self.assertEqual(self.test_sublet1.id, images.first().sublet.id)

    def test_create_delete_images(self):
        with open("tests/sublet/mock_image.jpg", "rb") as image:
            with open("tests/sublet/mock_image.jpg", "rb") as image2:
                response = self.client.post(
                    f"/sublet/properties/{str(self.test_sublet1.id)}/images/",
                    {"images": [image, image2]},
                    "multipart",
                )
                self.assertEqual(response.status_code, 201)
                images = Sublet.objects.get(id=self.test_sublet1.id).images.all()
                image_id1 = images.first().id
                self.assertTrue(images.exists())
                self.assertEqual(2, images.count())
                self.assertEqual(self.test_sublet1.id, images.first().sublet.id)
                response = self.client.delete(f"/sublet/properties/images/{image_id1}/")
                self.assertEqual(response.status_code, 204)
                self.assertFalse(SubletImage.objects.filter(id=image_id1).exists())
                self.assertEqual(1, SubletImage.objects.all().count())


class TestOffers(TestCase):
    """Tests Create/Delete/List for offers"""

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.test_user = User.objects.create_user("user1", "user")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        # TODO: Not sure how to add these amenities to the sublets, but not important for now
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            self.first_sublet = Sublet.objects.create(subletter=self.user, **data[0])
            self.second_sublet = Sublet.objects.create(subletter=self.test_user, **data[1])

    def test_create_offer(self):
        prop_url = f"/sublet/properties/{str(self.second_sublet.id)}/offers/"
        payload = {
            "email": "offer@seas.upenn.edu",
            # This is the MERT number, please DO NOT call ;-;
            "phone_number": "+12155733333",
            "message": "Message",
        }
        response = self.client.post(prop_url, payload)
        # test duplicate prevention
        self.assertEqual(self.client.post(prop_url, payload).status_code, 406)
        offer = Offer.objects.get(id=response.data["id"])
        offer_list = [offer.email, offer.phone_number, offer.message, offer.user, offer.sublet]
        payload_list = [
            payload["email"],
            payload["phone_number"],
            payload["message"],
            self.user,
            self.second_sublet,
        ]
        for o, p in zip(offer_list, payload_list):
            self.assertEqual(o, p)
        self.assertIsNotNone(offer.id)
        self.assertIsNotNone(offer.created_date)

    def test_delete_offer(self):
        prop_url1 = f"/sublet/properties/{str(self.first_sublet.id)}/offers/"
        prop_url2 = f"/sublet/properties/{str(self.second_sublet.id)}/offers/"
        payload = {
            "email": "offer@seas.upenn.edu",
            # This is the MERT number, please DO NOT call ;-;
            "phone_number": "+12155733333",
            "message": "Message",
        }
        self.client.post(prop_url2, payload)
        offers_count = Offer.objects.all().count()
        self.assertEqual(self.client.delete(prop_url1).status_code, 404)
        offers_count_new = Offer.objects.all().count()
        self.assertEqual(offers_count, offers_count_new)
        self.client.delete(prop_url2)
        self.assertFalse(Offer.objects.filter(user=self.user, sublet=self.second_sublet).exists())

    def test_get_offers_property(self):
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(0, len(res_json))
        payload = {
            "email": "offer@seas.upenn.edu",
            # This is the MERT number, please DO NOT call ;-;
            "phone_number": "+12155733333",
            "message": "Message",
        }
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/offers/", payload)
        response = self.client.get(f"/sublet/properties/{str(self.first_sublet.id)}/offers/")
        self.assertEqual(1, len(json.loads(response.content)))
        Offer.objects.create(
            user=self.test_user,
            sublet=self.first_sublet,
            email="offer2@seas.upenn.edu",
            phone_number="+12155733334",
            message="Message2",
        )
        response = self.client.get(f"/sublet/properties/{str(self.first_sublet.id)}/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        # TODO: this is really ugly, maybe clean up later haha
        offer = res_json[0]
        self.assertEqual(offer["email"], "offer@seas.upenn.edu")
        # This is the MERT number, please DO NOT call ;-;
        self.assertEqual(offer["phone_number"], "+12155733333")
        self.assertEqual(offer["message"], "Message")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], self.first_sublet.id)
        self.assertIsNotNone(offer["id"])
        self.assertIsNotNone(offer["created_date"])
        offer = res_json[1]
        self.assertEqual(offer["email"], "offer2@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "+12155733334")
        self.assertEqual(offer["message"], "Message2")
        self.assertEqual(offer["user"], self.test_user.id)
        self.assertEqual(offer["sublet"], self.first_sublet.id)
        self.assertIsNotNone(offer["id"])
        self.assertIsNotNone(offer["created_date"])

    def test_get_offer_user(self):
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(0, len(res_json))
        payload = {
            "email": "offer@seas.upenn.edu",
            # This is the MERT number, please DO NOT call ;-;
            "phone_number": "+12155733333",
            "message": "Message",
        }
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/offers/", payload)
        response = self.client.get("/sublet/offers/")
        self.assertEqual(1, len(json.loads(response.content)))
        payload = {
            "email": "offer2@seas.upenn.edu",
            "phone_number": "+12155733334",
            "message": "Message2",
        }
        self.client.post(f"/sublet/properties/{str(self.second_sublet.id)}/offers/", payload)
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        offer = res_json[0]
        self.assertEqual(offer["email"], "offer@seas.upenn.edu")
        # This is the MERT number, please DO NOT call ;-;
        self.assertEqual(offer["phone_number"], "+12155733333")
        self.assertEqual(offer["message"], "Message")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], self.first_sublet.id)
        self.assertIsNotNone(offer["id"])
        self.assertIsNotNone(offer["created_date"])
        offer = res_json[1]
        self.assertEqual(offer["email"], "offer2@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "+12155733334")
        self.assertEqual(offer["message"], "Message2")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], self.second_sublet.id)
        self.assertIsNotNone(offer["id"])
        self.assertIsNotNone(offer["created_date"])


class TestFavorites(TestCase):
    """Tests Create/Delete/List for favorites"""

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        test_user = User.objects.create_user("user1", "user")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        # TODO: Not sure how to add these amenities to the sublets, but not important for now
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            self.first_sublet = Sublet.objects.create(subletter=self.user, **data[0])
            self.second_sublet = Sublet.objects.create(subletter=test_user, **data[1])

    def test_create_favorite(self):
        prop_url1 = f"/sublet/properties/{str(self.first_sublet.id)}/favorites/"
        prop_url2 = f"/sublet/properties/{str(self.second_sublet.id)}/favorites/"
        self.client.post(prop_url2)
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.post(prop_url1)
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.assertEqual(self.client.post(prop_url1).status_code, 406)

    def test_delete_favorite(self):
        self.client.post(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.client.delete(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.delete(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.delete(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())

    def test_get_favorite_user(self):
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 0)
        self.client.post(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 1)
        self.assertEqual(res_json[0]["id"], self.second_sublet.id)
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 2)
        self.client.delete(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 1)
        self.assertEqual(res_json[0]["id"], self.first_sublet.id)
