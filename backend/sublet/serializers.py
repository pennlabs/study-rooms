from rest_framework import serializers

from sublet.models import Amenity, Favorite, Offer, Sublet, SubletImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = "__all__"


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = "__all__"


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = ["id", "created_date", "user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# complex sublet serializer for use in creation/updating/deletion + getting info about a singular sublet
class SubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)
    # favorites = FavoriteSerializer(many=True, required=False, read_only=True)
    # sublettees = OfferSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Sublet
        exclude = ["favorites"]
        read_only_fields = ["id", "created_date", "subletter", "sublettees"]

    def create(self, validated_data):
        validated_data["subletter"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Check if the user is the subletter before allowing the update
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            instance = super().update(instance, validated_data)
        else:
            raise serializers.ValidationError("You do not have permission to update this sublet.")

        return instance

    def destroy(self, instance):
        # Check if the user is the subletter before allowing the delete
        if (
            self.context["request"].user == instance.subletter
            or self.context["request"].user.is_superuser
        ):
            instance.delete()
        else:
            raise serializers.ValidationError("You do not have permission to delete this sublet.")


# simple sublet serializer for use when pulling all serializers/etc
class SimpleSubletSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, required=False)

    class Meta:
        model = Sublet
        fields = [
            "subletter",
            "amenities",
            "title",
            "address",
            "beds",
            "baths",
            "min_price",
            "max_price",
            "start_date",
            "end_date",
        ]
        read_only_fields = []


class FavoritesListSerializer(serializers.ModelSerializer):
    sublet = SubletSerializer()

    class Meta:
        model = Favorite
        fields = ["sublet"]
        read_only_fields = ["id"]
