from phonenumber_field.serializerfields import PhoneNumberField
from profanity_check import predict
from rest_framework import serializers

from market.models import Amenity, Offer, Sublet, SubletImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = "__all__"


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
class SubletImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = SubletImage
        fields = ["sublet", "image"]


# Browse images
class SubletImageURLSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField("get_image_url")

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
        model = SubletImage
        fields = ["id", "image_url"]


# complex sublet serializer for use in C/U/D + getting info about a singular sublet
class SubletSerializer(serializers.ModelSerializer):
    # amenities = AmenitySerializer(many=True, required=False)
    # images = SubletImageURLSerializer(many=True, required=False)
    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )

    class Meta:
        model = Sublet
        read_only_fields = [
            "id",
            "created_at",
            "subletter",
            "sublettees",
            # "images"
        ]
        fields = [
            "id",
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "description",
            "external_link",
            "price",
            "negotiable",
            "start_date",
            "end_date",
            "expires_at",
            # "images",
            # images are now created/deleted through a separate endpoint (see urls.py)
            # this serializer isn't used for getting,
            # but gets on sublets will include ids/urls for images
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
        validated_data["subletter"] = self.context["request"].user
        instance = super().create(validated_data)
        instance.save()
        return instance

    # delete_images is a list of image ids to delete
    def update(self, instance, validated_data):
        # Check if the user is the subletter before allowing the update
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            instance = super().update(instance, validated_data)
            instance.save()
            return instance
        else:
            raise serializers.ValidationError("You do not have permission to update this sublet.")

    def destroy(self, instance):
        # Check if the user is the subletter before allowing the delete
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            instance.delete()
        else:
            raise serializers.ValidationError("You do not have permission to delete this sublet.")


class SubletSerializerRead(serializers.ModelSerializer):
    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )
    images = SubletImageURLSerializer(many=True, required=False)

    class Meta:
        model = Sublet
        read_only_fields = ["id", "created_at", "subletter", "sublettees"]
        fields = [
            "id",
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "description",
            "external_link",
            "price",
            "negotiable",
            "start_date",
            "end_date",
            "expires_at",
            "images",
        ]


# simple sublet serializer for use when pulling all serializers/etc
class SubletSerializerSimple(serializers.ModelSerializer):
    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False
    )
    images = SubletImageURLSerializer(many=True, required=False)

    class Meta:
        model = Sublet
        fields = [
            "id",
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "price",
            "negotiable",
            "start_date",
            "end_date",
            "images",
        ]
        read_only_fields = ["id", "subletter"]
