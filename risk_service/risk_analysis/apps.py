from django.apps import AppConfig


class RiskAnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'risk_analysis'
    # def ready(self):
    #     from .insert_risk_factors_task import process_portfolio
    #     process_portfolio.delay()
