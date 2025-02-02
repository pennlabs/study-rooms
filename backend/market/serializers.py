from django.contrib.auth import get_user_model
from django.core import exceptions
from phonenumber_field.serializerfields import PhoneNumberField
from profanity_check import predict
from rest_framework import serializers

from market.models import Category, Item, ItemImage, Offer, Sublet, Tag


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]


# TODO: We could make a Read-Only Serializer in a PennLabs core library.
# This could inherit from that.
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]


class OfferSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField()

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["id", "created_date", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# Create/Update Image Serializer
class ItemImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = ItemImage
        fields = "__all__"


# Browse images
class ItemImageURLSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        image = obj.image

        if not image:
            return None
        if image.url.startswith("http"):
            return image.url
        elif "request" in self.context:
            return self.context["request"].build_absolute_uri(image.url)
        else:
            return image.url

    class Meta:
        model = ItemImage
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]


# complex item serializer for use in C/U/D + getting info about a singular item
class ItemSerializer(serializers.ModelSerializer):
    images = ItemImageSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Item
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "seller",
            "buyers",
            "images",
            "favorites",
        ]

    def validate_title(self, value):
        if self.contains_profanity(value):
            raise serializers.ValidationError("The title contains inappropriate language.")
        return value

    def validate_description(self, value):
        if self.contains_profanity(value):
            raise serializers.ValidationError("The description contains inappropriate language.")
        return value

    def contains_profanity(self, text):
        return predict([text])[0]

    def create(self, validated_data):
        self.validate(validated_data)
        validated_data["seller"] = self.context["request"].user
        return super().create(validated_data)


# Read-only serializer for use when reading a single item
class ItemSerializerPublic(serializers.ModelSerializer):
    buyer_count = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    images = ItemImageURLSerializer(many=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "seller",
            "buyer_count",
            "tags",
            "category",
            "title",
            "description",
            "price",
            "negotiable",
            "expires_at",
            "images",
            "favorite_count",
        ]
        read_only_fields = fields

    def get_buyer_count(self, obj):
        return obj.buyers.count()

    def get_favorite_count(self, obj):
        return obj.favorites.count()


# Read-only serializer for use when pulling all items/etc
class ItemSerializerList(serializers.ModelSerializer):
    images = ItemImageURLSerializer(many=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "seller",
            "tags",
            "category",
            "title",
            "price",
            "negotiable",
            "expires_at",
            "images",
            "favorites",
        ]
        read_only_fields = fields


class SubletSerializer(serializers.ModelSerializer):
    item = ItemSerializer(required=True)

    class Meta:
        model = Sublet
        fields = "__all__"
        read_only_fields = ["id"]

    def create(self, validated_data):
        item_serializer = ItemSerializer(data=validated_data.pop("item"), context=self.context)
        item_serializer.is_valid(raise_exception=True)
        validated_data["item"] = item_serializer.save()
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        if item_data := validated_data.pop("item", None):
            item_serializer = ItemSerializer(
                instance=instance.item, data=item_data, context=self.context, partial=True
            )
            item_serializer.is_valid(raise_exception=True)
            validated_data["item"] = item_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    def destroy(self, instance):
        # Could check if instance.item is None, but it should never be.
        instance.item.delete()
        instance.delete()


class SubletSerializerPublic(serializers.ModelSerializer):
    item = ItemSerializerPublic(required=True)

    class Meta:
        model = Sublet
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]


class SubletSerializerList(serializers.ModelSerializer):
    item = ItemSerializerList(required=True)

    class Meta:
        model = Sublet
        fields = "__all__"
        read_only_fields = [field.name for field in model._meta.fields]
