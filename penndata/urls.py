from django.urls import path

from penndata.views import Calendar, Events, GSRView, HomePage, News


urlpatterns = [
    path("news/", News.as_view(), name="news"),
    path("calendar/", Calendar.as_view(), name="calendar"),
    path("homepage", HomePage.as_view(), name="homepage"),
    path("events/<type>/", Events.as_view(), name="events"),
    path("gsrs/", GSRView.as_view(), name="gsrs"),
]
