from django.urls import path, re_path

from apps.meeting.consumers import HostMeetingConsumer, ParticipantMeetingConsumer

websocket_urlpatterns = [
    path("ws/meeting/<uuid:meeting_id>/host/", HostMeetingConsumer.as_asgi()),  # type: ignore
    re_path(r'^ws/meeting/(?P<access_code>[^/]+)/participant/$', ParticipantMeetingConsumer.as_asgi()), #type: ignore

]