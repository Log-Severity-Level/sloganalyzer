from django.core.management.base import BaseCommand

from core.models import System

data = [
    {
        'name': 'Hadoop',
        'github_url': 'https://github.com/apache/hadoop.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/release-|release-)(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d+)$'
    },
    {
        'name': 'Kafka',
        'github_url': 'https://github.com/apache/kafka.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d+)(\.(?P<v4>\d+))?$'
    },
    {
        'name': 'HBase',
        'github_url': 'https://github.com/apache/hbase.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-|hbase-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
]

class Command(BaseCommand):

    def handle(self, *args, **options):
        for system in data:
            System(**system).save()
