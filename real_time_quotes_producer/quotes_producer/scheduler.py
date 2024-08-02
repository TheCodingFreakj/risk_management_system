from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from .loggin_config import logger
import atexit


scheduler = BackgroundScheduler()
@retry(stop=stop_after_attempt(5), wait=wait_fixed(10))  # Retry 5 times with a 10-second delay between attempts
def call_produce_to_kafka_viewset():
    try:
        response = requests.post('http://127.0.0.1:8003/quotes_producer/stockdata/producetokafka/')
        if response.status_code == 200:
            logger.info("Successfully called produce_to_kafka viewset.")
        else:
            logger.error(f'Failed to call produce_to_kafka viewset: {response.status_code}')
    except requests.RequestException as e:
        logger.exception("Exception occurred while calling produce_to_kafka viewset")
        raise e


def start_scheduler():

    if not scheduler.running:
        scheduler.start()
        trigger = DateTrigger(run_date=None)  # `None` means "now"
        scheduler.add_job(call_produce_to_kafka_viewset, trigger=trigger)

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

atexit.register(stop_scheduler)
