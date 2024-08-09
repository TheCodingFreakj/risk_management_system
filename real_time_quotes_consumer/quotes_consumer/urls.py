from django.urls import path, include
from . import routing
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('chart-data/', views.chart_data, name='chart_data'),  # Add this line

]

# Include the WebSocket URLs
urlpatterns += routing.websocket_urlpatterns