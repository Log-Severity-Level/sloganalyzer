import codecs
import logging
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import connection
from core.models import TimeTracker

from config.settings import BASE_DIR


def read_file(filename):
    if os.path.isfile(filename):
        file = codecs.open(filename, "r", "utf-8")
        content = file.read()
        file.close()
        content = content.split('\n')
        content = '\n'.join(content)
        return content
    else:
        raise NameError('Unable to read file %s.' % filename)


class Command(BaseCommand):

    def handle(self, *args, **options):
        time_initial = datetime.now()

        logger = logging.getLogger('django')

        with connection.cursor() as cursor:

            logger.info('Exporting stage data')
            SQL_UPDATE_STATEMENTS = read_file(
                os.path.join(BASE_DIR, 'core', 'management', 'commands', 'sql_etl', 'stage', 'drop_create_schema_stage.sql'))
            cursor.execute(SQL_UPDATE_STATEMENTS)

            logger.info('Exporting stage_statements')
            SQL_UPDATE_STATEMENTS = read_file(
                os.path.join(BASE_DIR, 'core', 'management', 'commands', 'sql_etl', 'stage', 'stage_statements.sql'))
            cursor.execute(SQL_UPDATE_STATEMENTS)

            logger.info('Exporting stage_changes')
            SQL_UPDATE_STATEMENTS = read_file(
                os.path.join(BASE_DIR, 'core', 'management', 'commands', 'sql_etl', 'stage', 'stage_changes.sql'))
            cursor.execute(SQL_UPDATE_STATEMENTS)

            logger.info('Exporting stage_others')
            SQL_UPDATE_STATEMENTS = read_file(
                os.path.join(BASE_DIR, 'core', 'management', 'commands', 'sql_etl', 'stage', 'stage_others.sql'))
            cursor.execute(SQL_UPDATE_STATEMENTS)

            logger.info('Stage data exported')

            logger.info('Transforming...')
            path = os.path.join(BASE_DIR, 'core', 'management', 'commands', 'sql_etl', 'transform')
            files = os.listdir(path)
            for file in files:
                logger.info(os.path.join(BASE_DIR, 'core', 'management', 'commands', 'sql_etl', 'transform', file))
                sql = read_file(
                    os.path.join(BASE_DIR, 'core', 'management', 'commands', 'sql_etl', 'transform', file))
                cursor.execute(sql)

        TimeTracker.save_time('Data', time_initial)
