from django.urls import path
from rest_framework import routers

from market.views import (
    Categories,
    CreateImages,
    DeleteImage,
    Favorites,
    Items,
    Offers,
    Sublets,
    Tags,
    UserFavorites,
    UserOffers,
)


app_name = "market"

router = routers.DefaultRouter()
router.register(r"items", Items, basename="items")
router.register(r"sublets", Sublets, basename="sublets")

additional_urls = [
    # List of all amenities
    path("tags/", Tags.as_view(), name="tags"),
    # List of all categories
    path("categories/", Categories.as_view(), name="categories"),
    # All favorites for user
    path("favorites/", UserFavorites.as_view(), name="user-favorites"),
    # All offers made by user
    path("offers/", UserOffers.as_view(), name="user-offers"),
    # Favorites
    # post: add an item to the user's favorites
    # delete: remove an item from the user's favorites
    path(
        "items/<item_id>/favorites/",
        Favorites.as_view({"post": "create", "delete": "destroy"}),
    ),
    # Offers
    # get: list all offers for an item
    # post: create an offer for an item
    # delete: delete an offer for an item
    path(
        "items/<item_id>/offers/",
        Offers.as_view({"get": "list", "post": "create", "delete": "destroy"}),
    ),
    # Image Creation
    path("items/<item_id>/images/", CreateImages.as_view()),
    # Image Deletion
    path("items/images/<image_id>/", DeleteImage.as_view()),
]

urlpatterns = router.urls + additional_urls
