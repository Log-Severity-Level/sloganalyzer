from django.core.management.base import BaseCommand

from core.models import System

data = [
    {
        'name': 'hadoop',
        'github_url': 'https://github.com/apache/hadoop.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/release-|release-)(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d+)$'
    },
    {
        'name': 'kafka',
        'github_url': 'https://github.com/apache/kafka.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d+)(\.(?P<v4>\d+))?$'
    },
    {
        'name': 'hbase',
        'github_url': 'https://github.com/apache/hbase.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'hive',
        'github_url': 'https://github.com/apache/hive.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'openmeetings',
        'github_url': 'https://github.com/apache/openmeetings.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'tomcat',
        'github_url': 'https://github.com/apache/tomcat.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'ant',
        'github_url': 'https://github.com/apache/ant.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'fop',
        'github_url': 'https://github.com/apache/xmlgraphics-fop.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'jmeter',
        'github_url': 'https://github.com/apache/jmeter.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'maven',
        'github_url': 'https://github.com/apache/maven.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'creadur-rat',
        'github_url': 'https://github.com/apache/creadur-rat.git', # RAT
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'activemq',
        'github_url': 'https://github.com/apache/activemq.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'empire-db',
        'github_url': 'https://github.com/apache/empire-db.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'karaf',
        'github_url': 'https://github.com/apache/karaf.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'log4j',
        'github_url': 'https://github.com/apache/logging-log4j1.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'lucene',
        'github_url': 'https://github.com/apache/lucene.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'mahout',
        'github_url': 'https://github.com/apache/mahout.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'mina',
        'github_url': 'https://github.com/apache/mina.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'pig',
        'github_url': 'https://github.com/apache/pig.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'pivot',
        'github_url': 'https://github.com/apache/pivot.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'struts',
        'github_url': 'https://github.com/apache/struts.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
    {
        'name': 'zookeeper',
        'github_url': 'https://github.com/apache/zookeeper.git',
        'cloned_date': None,
        'head': None,
        'version_regex': '^(rel\/|release-)?(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d{1,3})$'
    },
]

class Command(BaseCommand):

    def handle(self, *args, **options):
        for system in data:
            System(**system).save()
