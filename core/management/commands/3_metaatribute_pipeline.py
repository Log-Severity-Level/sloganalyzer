import logging
import codecs
import logging
import os
import re
import lizard
import json
from datetime import datetime
from django.db import connection

from django.core.management.base import BaseCommand

from core.models import System, Branch, BranchFile, Method, File, TimeTracker, Statement

logger = logging.getLogger('django')

# TODO: Clean REGEX variable
REGEX = [
    r'.*LoggerFactory\.*',
    r'import.*\.(logging|slf4j)\..*;',
    r'.*getLogger.*',
    # r'(.*LOG.is.*|.*getLogger.*|.*LoggerFactory\.*|import.*\.(logging|slf4j)\..*;)',
]


class Counter:

    def __init__(self, filename):
        self.filename = filename
        self.content = self.read_file(filename)

    def read_file(self, filename):
        if os.path.isfile(filename):
            file = codecs.open(filename, "r", "utf-8")
            self.content = file.read()
            file.close()
            return self.content
        else:
            raise NameError('Unable to read file %s.' % self.filename)

    def remove_comments(self):
        content = self.content
        matchs = re.finditer(r'\/\/.*', content)
        for match in matchs:
            initial, end = match.span()
            replacement = '*' * (end - initial)
            content = content[:initial] + replacement + content[end:]
        matchs = re.finditer(r'^[ \t]*\/\*[\S\s]*?\*\/[ \t]*$', self.content, re.MULTILINE)
        for match in matchs:
            initial, end = match.span()
            replacement = '\n'.join(['*' * len(part) for part in self.content[initial:end].split('\n')])
            content = content[:initial] + replacement + content[end:]
        return content

    def count_log_lines(self, content):
        counter = 0
        for regex in REGEX:
            matchs = re.finditer(regex, content)
            for match in matchs:
                initial, end = match.span()
                counter += len(content[initial:end].split('\n'))
                replacement = '*' * (end - initial)
                content = content[:initial] + replacement + content[end:]
        return counter


def analyse_files(branch):
    Method.objects.filter(branch_id=branch.id).delete()
    BranchFile.objects.filter(branch_id=branch.id).delete()
    files = branch.get_files()
    filenames = [file.name for file in files]
    number = 0
    file_number = 0
    method_number = 0
    nloc = 0
    cyclomatic_complexity = 0
    logger.info(f"total files: {len(filenames)}")
    logger.info(f"Analyzing {branch.name}...")

    path = branch.path()

    filenames_lizard = []
    bulk_create_list = []
    branch_file_bulk_create_list = []
    for file in files:
        data = lizard.analyze_file(os.path.join(path, file.name))
        file_number += 1
        filename = data.filename.replace(path, "").strip()
        filenames_lizard.append(filename)
        file = File.objects.get(name=filename)

        counter = Counter(os.path.join(path, file.name))
        content = counter.remove_comments()
        nlog = counter.count_log_lines(content)

        nloc += data.nloc
        for method in data.function_list:
            cyclomatic_complexity += method.cyclomatic_complexity
            method_number += 1

            bulk_create_list.append(
                Method(
                    branch_id=branch.id,
                    file_id=file.id,
                    name=method.name,
                    cyclomatic_complexity=method.cyclomatic_complexity,
                    nloc=method.nloc,
                    token_count=method.token_count,
                    long_name=method.long_name,
                    start_line=method.start_line,
                    end_line=method.end_line,
                    full_parameters_json=json.dumps(list(method.full_parameters)),
                    parameters_count=len(list(method.full_parameters)),
                    filename=method.filename,
                    relative_filename=filename,
                    top_nesting_level=method.top_nesting_level,
                    fan_in=method.fan_in,
                    fan_out=method.fan_out,
                    general_fan_out=method.general_fan_out,
                    ))

        log_statements = Statement.objects.filter(branch_id=branch.id, file_id=file.id).all()
        log_statements_lines = [(l.line_number_final - l.line_number + 1) for l in log_statements]
        branch_file_bulk_create_list.append(
            BranchFile(
                branch_id=branch.id,
                file_id=file.id,
                nloc=data.nloc,
                nlog=nlog + sum(log_statements_lines),
                nlog_without_log_statements=nlog,
            ))
        number += 1
        if number % 100 == 0:
            Method.objects.bulk_create(bulk_create_list, ignore_conflicts=True)
            BranchFile.objects.bulk_create(branch_file_bulk_create_list, ignore_conflicts=True)
            bulk_create_list = []
            branch_file_bulk_create_list = []
            logger.info(f'{number}/{len(files)} files processed... ')

    Method.objects.bulk_create(bulk_create_list, ignore_conflicts=True)
    BranchFile.objects.bulk_create(branch_file_bulk_create_list, ignore_conflicts=True)
    logger.info(f'{number}/{len(files)} processed... ')

    branch.cyclomatic_complexity = cyclomatic_complexity
    branch.nloc = nloc
    branch.file_number = file_number
    branch.method_number = method_number
    branch.save()


class Command(BaseCommand):

    def handle(self, *args, **options):
        time_initial = datetime.now()
        branchs_exists = [b.branch_id for b in Method.objects.all()]
        systems = System.objects.all()

        for system in systems:
            branchs = Branch.objects.filter(system=system). \
                exclude(id__in=branchs_exists). \
                order_by('version', 'version2', 'version3').all()
            for branch in branchs:
                logger.info(f'Processing methods: System: {system.name} Branch: {branch.name}')
                time_initial_branch = datetime.now()
                analyse_files(branch)
                branch.save_time('Extract Meta Attributes', time_initial_branch)

        TimeTracker.save_time('Extract Meta Attributes', time_initial)
