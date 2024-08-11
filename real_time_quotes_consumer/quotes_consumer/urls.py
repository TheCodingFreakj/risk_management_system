from django.urls import path, include
from . import routing
from . import views
urlpatterns = [
    path('', views.index, name='index'),
     path('get-final-context/', views.get_final_context, name='get_final_context'),
    path('load-additional-data/', views.load_additional_data, name='load_additional_data'),
    path('chart-data/', views.chart_data, name='chart_data'),  # Add this line
    path('get-scenario-data/<int:scenario_id>/', views.get_scenario_data, name='get_scenario_data'),
]

# Include the WebSocket URLs
urlpatterns += routing.websocket_urlpatterns