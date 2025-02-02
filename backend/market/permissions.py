from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Grants permission if the current user is a superuser.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser

    def has_permission(self, request, view):
        return request.user.is_superuser


class ItemOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow the owner of a Item to edit or delete it.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the Item.
        return request.method in permissions.SAFE_METHODS or obj.seller == request.user


class SubletOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow the owner of a Item to edit or delete it.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the Item.
        return request.method in permissions.SAFE_METHODS or obj.item.seller == request.user


class ItemImageOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow the owner of a ItemImage to edit or delete it.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the Item.
        return (
            request.method in permissions.SAFE_METHODS
            or (hasattr(obj, "seller") and obj.seller == request.user)
            or (hasattr(obj, "item") and obj.item.seller == request.user)
        )


class OfferOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow owner of an offer to delete it.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.user == request.user
