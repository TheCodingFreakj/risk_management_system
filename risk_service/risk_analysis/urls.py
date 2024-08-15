# urls.py

from django.urls import path
from .views import PortfolioPerformanceView

urlpatterns = [
    # path('api/risk_exposure_api/<str:portfolio_id>/', RiskExposureAPIView.as_view(), name='risk_exposure_api'),
    path('api/portfolio_performance/<str:portfolio_id>/', PortfolioPerformanceView.as_view(), name='portfolio_performance'),

]