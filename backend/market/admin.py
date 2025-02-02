from django.contrib import admin
from django.utils.html import mark_safe

from market.models import Category, Item, ItemImage, Offer, Sublet, Tag


class ItemAdmin(admin.ModelAdmin):
    def image_tag(self, instance):
        images = ['<img src="%s" height="150" />' for image in instance.images.all()]
        return mark_safe("<br>".join(images))

    image_tag.short_description = "Item Images"
    readonly_fields = ("image_tag",)


admin.site.register(Offer)
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(Item, ItemAdmin)
admin.site.register(Sublet)
admin.site.register(ItemImage)
