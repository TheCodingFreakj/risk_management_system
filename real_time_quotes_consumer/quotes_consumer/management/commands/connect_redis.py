from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Tests the Redis connection'

    def handle(self, *args, **kwargs):
        self.test_redis_connection()

    def test_redis_connection(self):
        try:
            cache.set('test_key', 'test_value', timeout=1)
            value = cache.get('test_key')
            if value == 'test_value':
                self.stdout.write(self.style.SUCCESS('Redis connection successful'))
            else:
                self.stdout.write(self.style.ERROR('Redis connection failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Redis connection error: {e}'))