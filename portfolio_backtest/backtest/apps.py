from django.apps import AppConfig


class BacktestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backtest'

    def ready(self):
        from backtest import tasks
        tasks.start_scheduler()
