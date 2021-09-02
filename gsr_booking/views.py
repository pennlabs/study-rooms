import datetime

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from gsr_booking.api_wrapper import LibCalWrapper, WhartonLibWrapper
from gsr_booking.booking_logic import book_rooms_for_group
from gsr_booking.csrfExemptSessionAuthentication import CsrfExemptSessionAuthentication
from gsr_booking.models import (  # GSR,
    Group,
    GroupMembership,
    GSRBooking,
    GSRBookingCredentials,
    UserSearchIndex,
)
from gsr_booking.serializers import (
    GroupBookingRequestSerializer,
    GroupMembershipSerializer,
    GroupSerializer,
    GSRBookingCredentialsSerializer,
    GSRBookingSerializer,
    UserSerializer,
)


User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Can specify `me` instead of the `username` to retrieve details on the current user.
    """

    queryset = User.objects.all().prefetch_related(
        Prefetch("booking_groups", Group.objects.filter(memberships__accepted=True))
    )
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    lookup_field = "username"
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["username", "first_name", "last_name"]

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        param = self.kwargs[lookup_url_kwarg]
        if param == "me":
            return self.request.user
        else:
            return super().get_object()

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.none()

        queryset = User.objects.all()
        queryset = queryset.prefetch_related(
            Prefetch(
                "memberships",
                GroupMembership.objects.filter(
                    group__in=self.request.user.booking_groups.all(), accepted=True
                ),
            )
        )
        return queryset

    @action(detail=True, methods=["get"])
    def invites(self, request, username=None):
        """
        Retrieve all invites for a given user.
        """
        if username == "me":
            username = request.user.username

        user = get_object_or_404(User, username=username)
        return Response(
            GroupMembershipSerializer(
                GroupMembership.objects.filter(
                    user=user, accepted=False, group__in=self.request.user.booking_groups.all(),
                ),
                many=True,
            ).data
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, username=None):
        """
        Activate a user's account. Must be run when a user signs in for the first time, at least.
        The action is idempotent, so no harm in calling it multiple times.
        """
        if username == "me":
            username = request.user.username

        user = get_object_or_404(User, username=username)
        if user != request.user:
            return HttpResponseForbidden()

        # Ensure that all invites for this user, even ones created before their account was in the
        # DB, are associated with the User object.
        GroupMembership.objects.filter(username=user.username).update(user=user)

        UserSearchIndex.objects.get_or_create(user=user)

        return Response({"success": True})

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search the database of registered users by name or pennkey. Deprecated in favor
        of the platform route.
        """
        query = request.query_params.get("q", "")
        results = UserSearchIndex.objects.filter(
            Q(full_name__istartswith=query) | Q(pennkey__istartswith=query)
        ).select_related("user")

        return Response(UserSerializer([entry.user for entry in results], many=True).data)


class GSRBookingCredentialsViewSet(generics.RetrieveUpdateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = GSRBookingCredentialsSerializer

    def get_object(self):
        if not self.request.user.is_authenticated:
            return GSRBookingCredentials.objects.none()
        try:
            return GSRBookingCredentials.objects.get(user=self.request.user)
        except GSRBookingCredentials.DoesNotExist:
            if self.request.method == "PUT":
                return GSRBookingCredentials(user=self.request.user)
            else:
                raise Http404("detail not found")

    def update(self, *args, **kwargs):
        supplied_username = args[0].data.get("user")
        if supplied_username is None:
            return Response(data={"user": "not supplied"}, status=404)
        if self.request.user.username != supplied_username:
            return HttpResponseForbidden()
        return super().update(*args, **kwargs)


class GroupMembershipViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "group"]
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated or not hasattr(self.request.user, "memberships"):
            return GroupMembership.objects.none()
        return GroupMembership.objects.filter(
            Q(id__in=self.request.user.memberships.all())
            | Q(
                group__in=Group.objects.filter(
                    memberships__in=GroupMembership.objects.filter(user=self.request.user, type="A")
                )
            )
        )

    def create(self, request, *args, **kwargs):
        group_id = request.data.get("group")
        group = get_object_or_404(Group, pk=group_id)
        if not group.has_member(request.user):
            return HttpResponseForbidden()

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def invite(self, request):
        """
        Invite a user to a group.
        """
        group_id = request.data.get("group")
        group = get_object_or_404(Group, pk=group_id)

        if not group.has_member(request.user):
            return HttpResponseForbidden()

        usernames = request.data.get("user").split(",")
        if isinstance(usernames, str):
            usernames = [usernames]

        for username in usernames:
            if GroupMembership.objects.filter(
                username=username, group=group, accepted=False
            ).exists():
                return Response({"message": "invite exists"}, status=400)
            elif GroupMembership.objects.filter(
                username=username, group=group, accepted=True
            ).exists():
                return Response({"message": f"user {username} already member"}, status=400)
            GroupMembership.objects.create(
                username=username, group=group, type=request.data.get("type", "M")
            )

        return Response({"message": "invite(s) sent."})

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        if membership.user is None or membership.user != request.user:
            return HttpResponseForbidden()

        if not membership.is_invite:
            return Response({"message": "invite has already been accepted"}, 400)

        membership.accepted = True
        membership.save()
        return Response(
            {
                "message": "group joined",
                "user": membership.user.username,
                "group": membership.group_id,
            }
        )

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        if membership.user is None or membership.user != request.user:
            return HttpResponseForbidden()
        if not membership.is_invite:
            return Response({"message": "cannot decline an invite that has been accepted."}, 400)

        resp = {
            "message": "invite declined",
            "user": membership.user.username,
            "group": membership.group_id,
        }
        membership.delete()
        return Response(resp)

    @action(detail=False, methods=["post"])
    def pennkey(self, request):
        group_id = request.data.get("group")
        username = request.data.get("user")
        allow = request.data.get("allow")
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(username=username)
        membership = GroupMembership.objects.get(user=user, group=group)
        membership.pennkey_allow = allow
        membership.save()
        return Response(
            {
                "message": "pennkey allowance updated",
                "user": membership.user.username,
                "group": membership.group_id,
            }
        )

    @action(detail=False, methods=["post"])
    def notification(self, request):
        group_id = request.data.get("group")
        username = request.data.get("user")
        active = request.data.get("active")
        print(active)
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(username=username)
        membership = GroupMembership.objects.get(user=user, group=group)
        membership.notifications = active
        membership.save()
        return Response(
            {
                "message": "notification updated",
                "user": membership.user.username,
                "group": membership.group_id,
            }
        )


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Group.objects.none()
        return (
            super()
            .get_queryset()
            .filter(members=self.request.user)
            .prefetch_related(
                Prefetch("memberships", GroupMembership.objects.filter(accepted=True))
            )
        )

    @action(detail=True, methods=["get"])
    def invites(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        if not group.has_member(request.user):
            return HttpResponseForbidden()

        return Response(
            GroupMembershipSerializer(
                GroupMembership.objects.filter(group=group, accepted=False), many=True
            ).data
        )

    @action(detail=True, methods=["post"], url_path="book-rooms")
    def book_rooms(self, request, pk):
        """
        Book GSR room(s) for a group. Requester must be an admin to book.
        """
        booking_serialized = GroupBookingRequestSerializer(data=request.data)
        if not booking_serialized.is_valid():
            return Response(status=400)

        booking_data = booking_serialized.data

        group = get_object_or_404(Group, pk=pk)

        # must be admin (and also a member) of the group to book
        if not group.has_admin(request.user):
            return HttpResponseForbidden()

        result_json = book_rooms_for_group(
            group, booking_data["room_bookings"], request.user.username
        )

        return Response(result_json)


LCW = LibCalWrapper()
WLW = WhartonLibWrapper()
WHARTON_URL = "https://apps.wharton.upenn.edu/gsr/api/v1/"


class Locations(APIView):
    """Returns location IDs and names."""

    def get(self, request):

        wharton_buildings = WLW.request("GET", WHARTON_URL + "locations").json()
        for building in wharton_buildings["locations"]:
            building["lid"] = building["id"]
            del building["building_code"]
            del building["id"]

        return Response({"locations": LCW.get_buildings() + wharton_buildings["locations"]})


class Availability(APIView):
    """
    Returns JSON containing all rooms for a given building.
    Usage:
        /studyspaces/availability/<building> gives all rooms for the next 24 hours
        /studyspaces/availability/<building>?start=2018-25-01 gives all rooms in the start date
        /studyspaces/availability/<building>?start=...&end=... gives all rooms between the two days
    """

    def get(self, request, lid):
        start = request.GET.get("start")
        # end = request.GET.get("end")

        time = timezone.localtime().date()

        date = start if start is not None else str(time)
        url = WHARTON_URL + "jongmin" + "/availability/" + lid + "/" + date

        response = WLW.request("GET", url).json()

        for room in response:
            keep_list = []
            for slot in room["availability"]:
                date = datetime.datetime.strptime(slot["start_time"], "%Y-%m-%dT%H:%M:%S%z")
                if timezone.localtime() < date:
                    keep_list.append(slot)
            room["availability"] = keep_list

        return Response(response)

        # TODO: fix wharton
        # room = get_object_or_404(GSR, lid=lid)
        # if room.kind == GSR.KIND_WHARTON:
        #     date = start if start is not None else str(timezone.localtime().date())
        #     url = WHARTON_URL + request.user.pennid + "/availability/" + lid + "/" + date
        #     return Response(WLW.request("GET", url).json())

        # try:
        #     rooms = self.parse_times(lid, start, end)
        # except APIError as e:
        #     return Response({"error": str(e)}, status=400)
        # return Response(rooms)

    def parse_times(self, lid, start=None, end=None):
        rooms = LCW.get_rooms(lid, start, end)
        rooms["location_id"] = rooms["id"]
        rooms["rooms"] = []
        for room_list in rooms["categories"]:
            for room in room_list["rooms"]:
                room["thumbnail"] = room["image"]
                del room["image"]
                room["room_id"] = room["id"]
                del room["id"]
                room["gid"] = room_list["cid"]
                room["lid"] = lid
                room["times"] = room["availability"]
                del room["availability"]
                for time in room["times"]:
                    time["available"] = True
                    time["start"] = time["from"]
                    time["end"] = time["to"]
                    del time["from"]
                    del time["to"]
                rooms["rooms"].append(room)
        return rooms


class BookWhartonRoom(APIView):
    def post(self, request):
        payload = {
            "start": request.data["start_time"],
            "end": request.data["end_time"],
            "pennkey": request.user.username,
            "room": request.data["id"],
        }
        url = WHARTON_URL + request.user.username + "/student_reserve"
        return Response(WLW.request("POST", url, json=payload).json())


class CancelWhartonRoom(APIView):
    def post(self, request):
        url = (
            WHARTON_URL
            + request.user.username
            + "/reservations/"
            + str(request.data["booking_id"])
            + "/cancel"
        )
        return Response(WLW.request("DELETE", url).json())


class WhartonReservations(APIView):
    def get(self, request):
        url = WHARTON_URL + request.user.username + "/reservations"
        return Response(WLW.request("GET", url).json())


class BookRoom(generics.CreateAPIView):
    """
    Books a room for a given user.
    """

    serializer_class = GSRBookingSerializer


class CancelRoom(APIView):
    """
    Cancels  a room for a given user
    """

    def post(self, request):
        booking_id = request.data["booking_id"]

        gsr_booking = get_object_or_404(GSRBooking, booking_id=booking_id)
        if request.user.profile != gsr_booking.profile:
            return Response(
                {"detail": "Unauthorized: This reservation was booked by someone else."}, status=400
            )

        # TODO: fix wharton
        # room = get_object_or_404(GSR, lid=gsr_booking.room.lid)
        # if room.kind == GSR.KIND_WHARTON:
        #     url = WHARTON_URL + request.user.pennid + "/reservations/" + room.lid + "/cancel"
        #     return Response(WLW.request("DELETE", url).json())

        response = LCW.cancel_room(booking_id)
        if "error" not in response[0]:
            # cancels booking
            gsr_booking.is_cancelled = True
            gsr_booking.save()
            return Response({"detail": "success"})

        return Response({"detail": response[0]["error"]}, status=400)


class ReservationsView(APIView):
    """
    Gets reservations for a User
    """

    def get(self, request):

        # this variable tells how many days in advance to look for, defaults at 3
        libcal_search_span = request.GET.get("libcal_search_span")
        if not libcal_search_span:
            libcal_search_span = 3

        cutoff = timezone.localtime() + datetime.timedelta(days=libcal_search_span)

        # filters for booking_ids for valid reservations within time span
        booking_ids = GSRBooking.objects.filter(
            profile=request.user.profile, is_cancelled=False, end__lte=cutoff
        ).values_list("booking_id", flat=True)
        booking_str = ",".join(booking_ids)

        # TODO: do wharton here (don't use LCW)
        # url = WHARTON_URL + request.user.pennid + "/reservations"
        # wharton_reservations = WLW.request("GET", url).json()
        # return Response({"reservations": LCW.get_reservations(booking_str)
        #                   + wharton_reservations['bookings']})

        return Response({"reservations": LCW.get_reservations(booking_str)})
