# urls.py

from django.urls import path
from .views import RiskExposureAPIView

urlpatterns = [
    path('api/risk_exposure_api/<str:portfolio_id>/', RiskExposureAPIView.as_view(), name='risk_exposure_api'),
]