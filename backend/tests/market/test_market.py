import datetime
import json
from unittest.mock import MagicMock

import pytz
from django.contrib.auth import get_user_model
from django.core.files.storage import Storage
from django.test import TestCase
from django.utils.timezone import now
from rest_framework.test import APIClient

from market.models import Category, Item, ItemImage, Offer, Sublet, Tag


User = get_user_model()


# To run: python manage.py test ./tests/market
class TestMarket(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        tags = ["New", "Used", "Couch", "Laptop", "Textbook", "Chair", "Apartment", "House"]
        categories = ["Book", "Electronics", "Furniture", "Food", "Sublet", "Other"]
        for tag in tags:
            Tag.objects.create(name=tag)
        for category in categories:
            Category.objects.create(name=category)
        # "backend/tests/market/mock_items.json" if debugging
        # "tests/market/mock_items.json" if from backend directory
        # item 1, 5 are self.user. item 3, 4 are user1. item 2, 6 are user2
        with open("tests/market/mock_items.json") as data:
            data = json.load(data)
            for item_number, item in enumerate(data):
                if item_number == 0:
                    seller = self.user
                elif item_number == 2 or item_number == 3:
                    seller = user1
                else:
                    seller = user2
                created_item = Item.objects.create(
                    seller=seller,
                    category=Category.objects.get(name=item["category"]),
                    title=item["title"],
                    description=item["description"],
                    external_link=item["external_link"],
                    price=item["price"],
                    negotiable=item["negotiable"],
                    created_at=now(),
                    expires_at=item["expires_at"],
                )
                created_item.tags.set(Tag.objects.filter(name__in=item["tags"]))
                created_item.save()
        with open("tests/market/mock_sublets.json") as data:
            data = json.load(data)
            for sublet_number, sublet in enumerate(data):
                if sublet_number == 0:
                    seller = self.user
                elif sublet_number == 1:
                    seller = user2
                created_item = Item.objects.create(
                    seller=seller,
                    category=Category.objects.get(name="Sublet"),
                    title=sublet["item"]["title"],
                    description=sublet["item"]["description"],
                    price=sublet["item"]["price"],
                    negotiable=sublet["item"]["negotiable"],
                    created_at=now(),
                    expires_at=sublet["item"]["expires_at"],
                )
                created_sublet = Sublet.objects.create(
                    item=created_item,
                    address=sublet["address"],
                    beds=sublet["beds"],
                    baths=sublet["baths"],
                    start_date=sublet["start_date"],
                    end_date=sublet["end_date"],
                )
                created_item.tags.set(Tag.objects.filter(name__in=sublet["item"]["tags"]))
                created_item.save()
                created_sublet.save()
        self.user.items_favorited.set(Item.objects.filter(id__in=[1, 2, 3, 6]))
        created_offer_1 = Offer.objects.create(
            user=self.user, item=Item.objects.get(id=1), email="self_user@gmail.com"
        )
        created_offer_1.save()
        created_offer_2 = Offer.objects.create(
            user=self.user, item=Item.objects.get(id=5), email="self_user@gmail.com"
        )
        created_offer_2.save()
        created_offer_3 = Offer.objects.create(
            user=user1, item=Item.objects.get(id=5), email="user_1@gmail.com"
        )
        created_offer_3.save()

        storage_mock = MagicMock(spec=Storage, name="StorageMock")
        storage_mock.generate_filename = lambda filename: filename
        storage_mock.save = MagicMock(side_effect=lambda name, *args, **kwargs: name)
        storage_mock.url = MagicMock(name="url")
        storage_mock.url.return_value = "http://penn-mobile.com/mock-image.png"
        ItemImage._meta.get_field("image").storage = storage_mock

    def test_get_items(self):
        response = self.client.get("/market/items/")
        expected_response = [
            {
                "id": 1,
                "seller": 1,
                "tags": ["Textbook", "Used"],
                "category": "Book",
                "title": "Math Textbook",
                "price": 20.0,
                "negotiable": True,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "images": [],
                "favorites": [1],
            },
            {
                "id": 2,
                "seller": 3,
                "tags": ["New"],
                "category": "Food",
                "title": "Bag of Doritos",
                "price": 5.0,
                "negotiable": False,
                "expires_at": "2025-10-12T01:00:00-04:00",
                "images": [],
                "favorites": [1],
            },
            {
                "id": 3,
                "seller": 2,
                "tags": ["Laptop", "New"],
                "category": "Electronics",
                "title": "Macbook Pro",
                "price": 2000.0,
                "negotiable": True,
                "expires_at": "2025-08-12T01:00:00-04:00",
                "images": [],
                "favorites": [1],
            },
            {
                "id": 4,
                "seller": 2,
                "tags": ["Couch"],
                "category": "Furniture",
                "title": "Couch",
                "price": 400.0,
                "negotiable": True,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "images": [],
                "favorites": [],
            },
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)
        self.assertEqual(response.json(), expected_response)

    def test_get_single_item_own(self):
        response = self.client.get("/market/items/1/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 1,
            "images": [],
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/book",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2025-12-12T00:00:00-05:00",
            "seller": 1,
            "category": "Book",
            "buyers": [1],
            "tags": ["Textbook", "Used"],
            "favorites": [1],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_get_single_item_other(self):
        response = self.client.get("/market/items/2/")
        expected_response = {
            "id": 2,
            "seller": 3,
            "buyer_count": 0,
            "tags": ["New"],
            "category": "Food",
            "title": "Bag of Doritos",
            "description": "Cool Ranch",
            "price": 5.0,
            "negotiable": False,
            "expires_at": "2025-10-12T01:00:00-04:00",
            "images": [],
            "favorite_count": 1,
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    def test_get_item_of_sublet(self):
        response = self.client.get("/market/items/5/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'detail': 'No Item matches the given query.'})

    def test_create_item_all_fields(self):
        payload = {
            "id": 88,
            "seller": 2,
            "buyers": [],
            "tags": ["New"],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "created_at": "2024-11-26T00:50:03.217587-05:00",
            "expires_at": "2025-12-12T00:00:00-05:00",
            "images": [],
        }
        response = self.client.post("/market/items/", payload, format="json")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response_without_created_at = {
            "id": 7,
            "seller": 1,
            "buyers": [],
            "tags": ["New"],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2025-12-12T00:00:00-05:00",
            "images": [],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response_without_created_at)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )
        response = self.client.get("/market/items/7/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response_without_created_at)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_create_item_exclude_unrequired(self):
        payload = {
            "tags": ["New"],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response_without_created_at = {
            "id": 7,
            "seller": 1,
            "buyers": [],
            "tags": ["New"],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": None,
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
            "images": [],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response_without_created_at)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )
        response = self.client.get("/market/items/7/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response_without_created_at)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_create_item_invalid_category(self):
        payload = {
            "tags": ["New"],
            "category": "Textbook",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"category": ['Invalid pk "Textbook" - object does not exist.']})

    def test_create_item_invalid_tag(self):
        payload = {
            "tags": ["Not a tag"],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"tags": ['Invalid pk "Not a tag" - object does not exist.']})

    def test_create_item_with_profanity_title(self):
        payload = {
            "tags": ["New"],
            "category": "Book",
            "title": "Fuck Textbook",
            "description": "Fuck 2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        self.assertEqual(response.status_code, 400)

        res_json = response.json()
        self.assertIn("title", res_json)
        self.assertIn("description", res_json)
        self.assertEqual(res_json["title"][0], "The title contains inappropriate language.")
        self.assertEqual(
            res_json["description"][0], "The description contains inappropriate language."
        )

    def test_create_item_sublet_category(self):
        payload = {
            "tags": ["New"],
            "category": "Sublet",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        res_json = json.loads(response.content)
        response_without_created_at = res_json.copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response_without_created_at = {
            "id": 7,
            "seller": 1,
            "buyers": [],
            "tags": ["New"],
            "category": "Sublet",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
            "images": [],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response_without_created_at)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_update_item_minimum_required(self):
        # All fields included are strictly required.
        payload = {
            "category": "Book",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "2024-12-13T00:00:00-05:00",
        }
        response = self.client.patch("/market/items/1/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 1,
            "seller": 1,
            "buyers": [1],
            "tags": ["Textbook", "Used"],
            "category": "Book",
            "title": "Physics Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/book",
            "price": 25.0,
            "negotiable": True,
            "expires_at": "2024-12-13T00:00:00-05:00",
            "images": [],
            "favorites": [1],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )
        response = self.client.get("/market/items/1/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_update_item_all_fields(self):
        payload = {
            "id": 7,
            "seller": 1,
            "buyers": [],
            "tags": ["New"],
            "category": "Food",
            "title": "5 meal swipes",
            "description": "5 meal swipes for sale",
            "external_link": "https://example.com/meal-swipes",
            "price": 25.0,
            "negotiable": False,
            "created_at": "2024-11-26T00:50:03.217587-05:00",
            "expires_at": "2024-12-14T00:00:00-05:00",
            "images": [],
        }
        original_created_at = Item.objects.get(id=1).created_at
        response = self.client.patch("/market/items/1/", payload, format="json")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        expected_response = {
            "id": 1,
            "seller": 1,
            "buyers": [1],
            "tags": ["New"],
            "category": "Food",
            "title": "5 meal swipes",
            "description": "5 meal swipes for sale",
            "external_link": "https://example.com/meal-swipes",
            "price": 25.0,
            "negotiable": False,
            "expires_at": "2024-12-14T00:00:00-05:00",
            "images": [],
            "favorites": [1],
        }
        self.assertEqual(response_without_created_at, expected_response)
        self.assertEqual(original_created_at, created_at)
        response = self.client.get("/market/items/1/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertEqual(original_created_at, created_at)

    def test_update_item_invalid_category(self):
        payload = {
            "category": "Textbook",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "2024-12-13T00:00:00-05:00",
        }
        response = self.client.patch("/market/items/1/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"category": ['Invalid pk "Textbook" - object does not exist.']})

    def test_update_item_invalid_tag(self):
        payload = {
            "tags": ["Not a tag"],
            "category": "Book",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "2024-12-13T00:00:00-05:00",
        }
        response = self.client.patch("/market/items/1/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"tags": ['Invalid pk "Not a tag" - object does not exist.']})

    def test_update_item_to_sublet(self):
        payload = {"category": "Sublet"}
        response = self.client.patch("/market/items/1/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            'id': 1, 
            'images': [], 
            'title': 'Math Textbook', 
            'description': '2023 version', 
            'external_link': 'https://example.com/book', 
            'price': 20.0, 'negotiable': True, 
            'expires_at': '2025-12-12T00:00:00-05:00', 
            'seller': 1, 
            'category': 'Sublet', 
            'buyers': [1], 
            'tags': ['Textbook', 'Used'], 
            'favorites': [1]
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_delete_item(self):
        response = self.client.delete("/market/items/1/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Item.objects.filter(id=1).exists())

    def test_get_sublets(self):
        response = self.client.get("/market/sublets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        expected_response = [
            {
                "id": 1,
                "item": {
                    "id": 5,
                    "seller": 1,
                    "tags": ["New"],
                    "category": "Sublet",
                    "title": "Cira Green Sublet",
                    "price": 1350.0,
                    "negotiable": False,
                    "expires_at": "2025-12-12T00:00:00-05:00",
                    "images": [],
                    "favorites": [],
                },
                "address": "Cira Green, Philadelphia, PA",
                "beds": 3.0,
                "baths": 1.0,
                "start_date": "2024-01-01T00:00:00-05:00",
                "end_date": "2025-05-31T00:00:00-04:00",
            },
            {
                "id": 2,
                "item": {
                    "id": 6,
                    "seller": 3,
                    "tags": ["New"],
                    "category": "Sublet",
                    "title": "Rodin Quad",
                    "price": 1350.0,
                    "negotiable": False,
                    "expires_at": "2025-12-12T00:00:00-05:00",
                    "images": [],
                    "favorites": [1],
                },
                "address": "3901 Locust Walk, Philadelphia, PA",
                "beds": 4.0,
                "baths": 1.0,
                "start_date": "2024-01-01T00:00:00-05:00",
                "end_date": "2025-05-31T00:00:00-04:00",
            },
        ]
        self.assertEqual(response.json(), expected_response)

    def test_get_sublet_own(self):
        response = self.client.get("/market/sublets/1/")
        self.assertEqual(response.status_code, 200)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 1,
            "item": {
                "id": 5,
                "images": [],
                "title": "Cira Green Sublet",
                "description": (
                    "Fully furnished 3-bedroom apartment"
                    " available for sublet with all amenities included."
                ),
                "external_link": None,
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Sublet",
                "buyers": [1, 2],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "Cira Green, Philadelphia, PA",
            "beds": 3.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_get_sublet_other(self):
        response = self.client.get("/market/sublets/2/")
        self.assertEqual(response.status_code, 200)
        expected_response = {
            "id": 2,
            "item": {
                "id": 6,
                "seller": 3,
                "buyer_count": 0,
                "tags": ["New"],
                "category": "Sublet",
                "title": "Rodin Quad",
                "description": (
                    "Fully furnished 4-bedroom apartment available"
                    " for sublet with all amenities included."
                ),
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "images": [],
                "favorite_count": 1,
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.json(), expected_response)

    def test_get_single_sublet_invalid_id(self):
        response = self.client.get("/market/sublets/3/")
        self.assertEqual(response.status_code, 404)

    def test_create_sublet_required_fields(self):
        payload = {
            "item": {
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment available"
                    " for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "category": "Sublet",
                "tags": ["New"],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.post("/market/sublets/", payload, format="json")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment"
                    " available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )
        response = self.client.get("/market/sublets/3/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_create_sublet_all_fields(self):
        payload = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment available"
                    " for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.post("/market/sublets/", payload, format="json")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )
        response = self.client.get("/market/sublets/3/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_create_sublet_invalid_category(self):
        payload = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment"
                    " available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Invalid",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.post("/market/sublets/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"item": {"category": ['Invalid pk "Invalid" - object does not exist.']}},
        )

    def test_create_sublet_non_sublet_category(self):
        payload = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Book",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.post("/market/sublets/", payload, format="json")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Book",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_update_sublet(self):
        payload = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.patch("/market/sublets/1/", payload, format="json")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 1,
            "item": {
                "id": 5,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Sublet",
                "buyers": [1, 2],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )
        response = self.client.get("/market/sublets/1/")
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_update_sublet_non_sublet_category(self):
        payload = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": 1,
                "category": "Book",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.patch("/market/sublets/1/", payload, format="json")
        expected_response = {
            'id': 1, 
            'item': {
                'id': 5, 
                'images': [], 
                'title': 'Cira Green Sublet 2', 
                'description': 'Fully furnished 3-bedroom apartment available for sublet with all amenities included.', 
                'external_link': 'https://example.com/listing', 
                'price': 1350.0, 
                'negotiable': False, 
                'expires_at': '2025-12-12T00:00:00-05:00', 
                'seller': 1, 
                'category': 'Book', 
                'buyers': [1, 2], 
                'tags': ['New'], 
                'favorites': []}, 
            'address': '3901 Locust Walk, Philadelphia, PA', 
            'beds': 4.0, 
            'baths': 1.0, 
            'start_date': '2024-01-01T00:00:00-05:00', 
            'end_date': '2025-05-31T00:00:00-04:00'
        }
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at["item"].pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)

    def test_delete_sublet(self):
        response = self.client.delete("/market/sublets/1/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Sublet.objects.filter(id=1).exists())
        self.assertFalse(Item.objects.filter(id=5).exists())

    def test_get_all_tags(self):
        response = self.client.get("/market/tags/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            ["New", "Used", "Couch", "Laptop", "Textbook", "Chair", "Apartment", "House"],
        )

    def test_get_all_categories(self):
        response = self.client.get("/market/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), ["Book", "Electronics", "Furniture", "Food", "Sublet", "Other"]
        )

    def test_get_all_user_favorites(self):
        response = self.client.get("/market/favorites/")
        expected_response = [
            {
                "id": 1,
                "seller": 1,
                "tags": ["Textbook", "Used"],
                "category": "Book",
                "title": "Math Textbook",
                "price": 20.0,
                "negotiable": True,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "images": [],
                "favorites": [1],
            },
            {
                "id": 2,
                "seller": 3,
                "tags": ["New"],
                "category": "Food",
                "title": "Bag of Doritos",
                "price": 5.0,
                "negotiable": False,
                "expires_at": "2025-10-12T01:00:00-04:00",
                "images": [],
                "favorites": [1],
            },
            {
                "id": 3,
                "seller": 2,
                "tags": ["Laptop", "New"],
                "category": "Electronics",
                "title": "Macbook Pro",
                "price": 2000.0,
                "negotiable": True,
                "expires_at": "2025-08-12T01:00:00-04:00",
                "images": [],
                "favorites": [1],
            },
            {
                "id": 6,
                "seller": 3,
                "tags": ["New"],
                "category": "Sublet",
                "title": "Rodin Quad",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "images": [],
                "favorites": [1],
            },
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    def test_get_all_user_offers(self):
        response = self.client.get("/market/offers/")
        response_without_created_at = [offer.copy() for offer in response.json()]
        created_at_list = [
            datetime.datetime.fromisoformat(offer.pop("created_at"))
            for offer in response_without_created_at
        ]

        expected_response = [
            {
                "id": 1,
                "phone_number": None,
                "email": "self_user@gmail.com",
                "message": "",
                "user": 1,
                "item": 1,
            },
            {
                "id": 2,
                "phone_number": None,
                "email": "self_user@gmail.com",
                "message": "",
                "user": 1,
                "item": 5,
            },
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        for created_at in created_at_list:
            self.assertLessEqual(
                abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
                datetime.timedelta(minutes=1),
            )

    def test_favorite_item(self):
        response = self.client.post("/market/items/4/favorites/")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Item.objects.get(id=1).favorites.filter(id=1).exists())

    def test_favorite_favorited_item(self):
        response = self.client.post("/market/items/1/favorites/")
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.json(), {"detail": "Favorite already exists"})

    def test_unfavorite_item(self):
        response = self.client.delete("/market/items/1/favorites/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Item.objects.get(id=1).favorites.filter(id=1).exists())

    def test_unfavorite_unfavorited_item(self):
        response = self.client.delete("/market/items/4/favorites/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "No Item matches the given query."})

    def test_favorite_invalid_item(self):
        response = self.client.post("/market/items/100/favorites/")
        self.assertEqual(response.status_code, 404)

    def test_favorite_sublet(self):
        response = self.client.post("/market/items/5/favorites/")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Item.objects.get(id=6).favorites.filter(id=1).exists())

    def test_favorite_favorited_sublet(self):
        response = self.client.post("/market/items/1/favorites/")
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.json(), {"detail": "Favorite already exists"})

    def test_list_item_offers(self):
        response = self.client.get("/market/items/1/offers/")
        response_without_created_at = response.json().copy()
        created_at_list = [
            datetime.datetime.fromisoformat(offer.pop("created_at"))
            for offer in response_without_created_at
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response_without_created_at,
            [
                {
                    "id": 1,
                    "phone_number": None,
                    "email": "self_user@gmail.com",
                    "message": "",
                    "user": 1,
                    "item": 1,
                }
            ],
        )
        for created_at in created_at_list:
            self.assertLessEqual(
                abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
                datetime.timedelta(minutes=1),
            )

    def test_list_item_offers_invalid_item(self):
        response = self.client.get("/market/items/100/offers/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "No Item matches the given query"})

    def test_list_item_delete_and_offers_nonexistent(self):
        self.client.delete("/market/items/1/offers/")
        response = self.client.get("/market/items/1/offers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_offer(self):
        payload = {
            "phone_number": "+1 (425)-269-4412",
            "email": "self_user@gmail.com",
            "message": "I am interested in buying this item.",
        }
        response = self.client.post("/market/items/2/offers/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 4,
            "phone_number": "+14252694412",
            "email": "self_user@gmail.com",
            "message": "I am interested in buying this item.",
            "user": 1,
            "item": 2,
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response)
        self.assertLessEqual(
            abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))),
            datetime.timedelta(minutes=1),
        )

    def test_delete_offer(self):
        response = self.client.delete("/market/items/1/offers/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Offer.objects.filter(id=1).exists())

    def test_delete_offer_nonexistent(self):
        response = self.client.delete("/market/items/4/offers/")
        self.assertEqual(response.status_code, 404)

    def test_create_image(self):
        with open("tests/market/mock_image.jpg", "rb") as image:
            response = self.client.post("/market/items/1/images/", {"images": image})
            self.assertEqual(response.status_code, 201)
            images = Item.objects.get(id=1).images.all()
            self.assertTrue(images.exists())
            self.assertEqual(1, images.first().item.id)

    def test_create_delete_images(self):
        with open("tests/market/mock_image.jpg", "rb") as image:
            with open("tests/market/mock_image.jpg", "rb") as image2:
                response = self.client.post(
                    "/market/items/1/images/",
                    {"images": [image, image2]},
                    "multipart",
                )
                self.assertEqual(response.status_code, 201)
                images = Item.objects.get(id=1).images.all()
                self.assertTrue(images.exists())
                self.assertEqual(2, images.count())
                self.assertEqual(1, images.first().item.id)
                response = self.client.delete("/market/items/images/1/")
                self.assertEqual(response.status_code, 204)
                self.assertFalse(ItemImage.objects.filter(id=1).exists())
                self.assertTrue(ItemImage.objects.filter(id=2).exists())
                self.assertEqual(1, ItemImage.objects.all().count())
