from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/television_updates/', consumers.TelevisionConsumer.as_asgi()),
]
