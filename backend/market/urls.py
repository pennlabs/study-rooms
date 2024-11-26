from django.urls import path
from rest_framework import routers

from market.views import (
    Amenities,
    CreateImages,
    DeleteImage,
    Favorites,
    Offers,
    Properties,
    UserFavorites,
    UserOffers,
)


app_name = "sublet"

router = routers.DefaultRouter()
router.register(r"properties", Properties, basename="properties")

additional_urls = [
    # List of all amenities
    path("amenities/", Amenities.as_view(), name="amenities"),
    # All favorites for user
    path("favorites/", UserFavorites.as_view(), name="user-favorites"),
    # All offers made by user
    path("offers/", UserOffers.as_view(), name="user-offers"),
    # Favorites
    # post: add a sublet to the user's favorites
    # delete: remove a sublet from the user's favorites
    path(
        "properties/<sublet_id>/favorites/",
        Favorites.as_view({"post": "create", "delete": "destroy"}),
    ),
    # Offers
    # get: list all offers for a sublet
    # post: create an offer for a sublet
    # delete: delete an offer for a sublet
    path(
        "properties/<sublet_id>/offers/",
        Offers.as_view({"get": "list", "post": "create", "delete": "destroy"}),
    ),
    # Image Creation
    path("properties/<sublet_id>/images/", CreateImages.as_view()),
    # Image Deletion
    path("properties/images/<image_id>/", DeleteImage.as_view()),
]

urlpatterns = router.urls + additional_urls
