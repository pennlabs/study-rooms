from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view


urlpatterns = [
    path("gsr/", include("gsr_booking.urls")),
    path("portal/", include("portal.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("user/", include("user.urls")),
    path("laundry/", include("laundry.urls")),
    path(
        "openapi/",
        get_schema_view(title="Penn Mobile Backend Documentation", public=True),
        name="openapi-schema",
    ),
    path(
        "documentation/",
        TemplateView.as_view(
            template_name="redoc.html", extra_context={"schema_url": "openapi-schema"}
        ),
        name="documentation",
    ),
    path("dining/", include("dining.urls")),
    path("penndata/", include("penndata.urls")),
    path("sublet/", include("sublet.urls")),
    path("market/", include("market.urls")),
]

urlpatterns = [
    path("api/", include(urlpatterns)),
    path("", include((urlpatterns, "apex"))),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
