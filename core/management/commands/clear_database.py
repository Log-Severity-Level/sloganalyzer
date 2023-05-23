from django.core.management.base import BaseCommand
from datetime import datetime

from core.models import System, Branch, Statement, BranchComparison, BranchFileComparison, TimeTracker

from django.db import connection
import logging
import codecs
import os

logger = logging.getLogger('django')
from config.settings import BASE_DIR

import psycopg2
from django.core.management.base import BaseCommand

logger = logging.getLogger('django')

CLEAR_DATABASE = """
TRUNCATE public.core_branchfilecomparison CASCADE;
TRUNCATE public.core_branchcomparison CASCADE;
TRUNCATE public.core_statement CASCADE;
TRUNCATE public.core_message CASCADE;
TRUNCATE public.core_method CASCADE;
TRUNCATE public.core_file CASCADE;
TRUNCATE public.core_severitylevel CASCADE;
TRUNCATE public.core_branchfile CASCADE;

INSERT INTO public.core_severitylevel(id, severity, name) VALUES (0, 0, 'Not defined');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (1, 10, 'FINEST');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (2, 20, 'VERBOSE');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (3, 30, 'FINER');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (4, 40, 'TRACE');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (5, 50, 'DEBUG');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (6, 60, 'BASIC');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (7, 70, 'FINE');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (8, 80, 'CONFIG');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (9, 90, 'INFO');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (10, 100, 'SUCCESS');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (11, 110, 'NOTICE');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (12, 120, 'WARN');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (13, 120, 'WARNING');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (14, 130, 'ERROR');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (15, 140, 'FAULT');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (16, 150, 'SEVERE');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (17, 160, 'CRITICAL');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (18, 170, 'ALERT');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (19, 180, 'FATAL');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (20, 190, 'EMERG');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (21, 200, 'SYSTEM.OUT.PRINTLN');
INSERT INTO public.core_severitylevel(id, severity, name) VALUES (22, 210, 'SYSTEM.ERR.PRINTLN');

SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_branchfilecomparison', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_branchfilecomparison)+1);
SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_branchcomparison', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_branchcomparison)+1);
SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_statement', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_statement)+1);
SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_message', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_message)+1);
SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_method', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_method)+1);
SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_file', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_file)+1);
SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_severitylevel', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_severitylevel)+1);
SELECT pg_catalog.setval(
	pg_get_serial_sequence('core_branchfile', 'id'),
	(SELECT coalesce(MAX(id),0) FROM core_branchfile)+1);
"""


class Command(BaseCommand):
    help = 'delete all data'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            logger.info('Delete all data')
            cursor.execute(CLEAR_DATABASE)
            cursor.execute("VACUUM FULL")
        for branch in Branch.objects.all():
            branch.log_statement_number = 0
            branch.file_number = 0
            branch.method_number = 0
            branch.nloc = 0
            branch.cyclomatic_complexity = 0
            branch.save()