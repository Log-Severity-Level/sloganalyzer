#!/bin/bash

python manage.py 1_clone_repositories_pipeline
python manage.py 2_log_statements_pipeline
python manage.py 3_metaatribute_pipeline
python manage.py 4_integration_pipeline
python manage.py 5_branchcomparison_pipeline