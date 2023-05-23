import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import connection

from core.models import TimeTracker

SQL_UPDATE_STATEMENTS = """
DELETE FROM public.core_methodstatement;
COMMIT;
INSERT INTO public.core_methodstatement (statement_id, method_id)
SELECT DISTINCT s.id AS statement_id, m.id AS method_id
	FROM public.core_statement s
	INNER JOIN public.core_method m
	ON m.branch_id=s.branch_id AND m.file_id=s.file_id
	AND m.start_line <= s.line_number AND m.end_line >= s.line_number_final
	AND m.id IS NOT NULL AND s.id IS NOT NULL;
"""

SQL_UPDATE_METHODS = """
WITH methods AS (
SELECT ms.method_id,
	COUNT(DISTINCT s.severity_level_id) AS severity_level_number,
	COUNT(s.id) AS log_statement_number
	FROM public.core_statement s
	INNER JOIN public.core_methodstatement ms ON ms.statement_id = s.id
    JOIN public.core_branch b ON b.id = s.branch_id
	GROUP BY ms.method_id
)
UPDATE public.core_method s
   SET log_statement_number = m.log_statement_number,
       severity_level_number = m.severity_level_number
  FROM methods m
 WHERE s.id = m.method_id;
"""

class Command(BaseCommand):

    def handle(self, *args, **options):

        logger = logging.getLogger('django')
        time_initial = datetime.now()

        with connection.cursor() as cursor:
            cursor.execute(SQL_UPDATE_STATEMENTS)
            logger.info('Updated core_statement table')
            cursor.execute(SQL_UPDATE_METHODS)
            logger.info('Updated core_method table')

        TimeTracker.save_time('Integration', time_initial)
