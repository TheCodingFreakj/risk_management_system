from django.urls import path, include
from . import routing

urlpatterns = [
    # Other URL patterns for your app
]

# Include the WebSocket URLs
urlpatterns += routing.websocket_urlpatterns