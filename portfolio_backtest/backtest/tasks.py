# backtest/tasks.py

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from backtest.management.commands.update_asset_data import Command as UpdateAssetDataCommand

def update_asset_data_task():
    """Task to update asset data."""
    UpdateAssetDataCommand().handle()

def start_scheduler():
    """Starts the scheduler with the update_asset_data task."""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Schedule the update_asset_data_task to run daily
    scheduler.add_job(update_asset_data_task, 'interval', days=1, id="update_asset_data", replace_existing=True)
    scheduler.start()
