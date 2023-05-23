import codecs
import difflib
import logging
import math
import os
import re
from collections import Counter
from datetime import datetime
from django.db import connection

from django.core.management.base import BaseCommand

from core.models import (System, Branch, File, Statement, BranchComparison, BranchFileComparison, MethodStatement, Method, TimeTracker)

logger = logging.getLogger('django')

WORD = re.compile(r"\w+")

YES = 1
NO = 0

ADDED = 1
UPDATED = 2
DELETED = 3
NO_UPDATED = 4

UPDATE_BRANCH_FILE_COMPARISON = """
UPDATE public.core_branchfilecomparison SET changed_severity_level=1
WHERE severity_level_1_id != severity_level_2_id;
UPDATE public.core_branchfilecomparison SET changed_severity_level=0
WHERE severity_level_1_id = severity_level_2_id;

UPDATE public.core_branchfilecomparison SET changed_messages=1
WHERE message_1_id != message_2_id;
UPDATE public.core_branchfilecomparison SET changed_messages=0
WHERE message_1_id = message_2_id;

UPDATE public.core_branchfilecomparison SET changed_variables=1
WHERE variables_1 != variables_2;
UPDATE public.core_branchfilecomparison SET changed_variables=0
WHERE variables_1 = variables_2;

"""

def get_changes(target_string):
    regex = r'\-(\d+),?(\d*)? \+(\d+),?(\d*)?'
    result = re.search(regex, target_string)
    g = [int(gr or 1) for gr in result.groups()]
    return list(range(g[0], g[0] + g[1])), list(range(g[2], g[2] + g[3]))


def clear_message(target_string):
    regex = r'\".*?\"'
    result = re.sub(regex, '', target_string)
    return result


def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)


def read_file(filename):
    if os.path.isfile(filename):
        file = codecs.open(filename, "r", "utf-8")
        content = file.read()
        file.close()
        return content
    else:
        raise NameError('Não foi possivel ler o arquivo %s.' % filename)


def make_pairs_of_elements(statements1, statements2):
    list_cos_sims = []
    for l1 in statements1:
        for l2 in statements2:
            vector1 = text_to_vector(l1[1])
            vector2 = text_to_vector(l2[1])
            cos_sim = get_cosine(vector1, vector2)
            # print(vector1)
            # print(vector2)
            # print(cos_sim)
            # print(l1[2])
            # print(l2[2])
            # print("*******")
            if cos_sim > 0.5:  # and l1[2] == l2[2]:
                list_cos_sims.append([l1[0], l2[0], cos_sim])
    list_cos_sims = sorted(list_cos_sims, reverse=True, key=lambda x: x[2])
    pairs = []
    while list_cos_sims:
        pairs.append(list_cos_sims[0])
        ele1, ele2, _ = list_cos_sims.pop(0)
        for ele in list_cos_sims:
            if ele[0] == ele1 or ele[1] == ele2:
                list_cos_sims.remove(ele)
    return pairs


class Command(BaseCommand):

    def handle(self, *args, **options):
        time_initial = datetime.now()
        BranchComparison.objects.all().delete()

        systems = System.objects.all()
        for system in systems:
            branches = Branch.objects. \
                filter(system=system).order_by('version', 'version2', 'version3', 'version4').all()
            branches = [branch.id for branch in branches]
            for n in list(range(len(branches) - 1)):
                data = {'branch_1_id': branches[n], 'branch_2_id': branches[n + 1]}
                BranchComparison(**data).save()

        BranchFileComparison.objects.all().delete()
        branchcomparison = BranchComparison.objects.order_by('id').all()
        total_comparison = len(branchcomparison)
        n_comparison = 0

        for bc in branchcomparison:
            n_comparison += 1
            logger.info(f'{bc} {n_comparison}/{total_comparison}')
            statements1 = Statement.objects.filter(branch=bc.branch_1_id)
            files1 = [statement.file_id for statement in statements1]
            files1 = set(files1)
            statements2 = Statement.objects.filter(branch=bc.branch_2_id)
            files2 = [statement.file_id for statement in statements2]
            files2 = set(files2)
            files_intersection = files1.intersection(files2)
            files_intersection = File.objects.filter(id__in=files_intersection)
            total = len(files_intersection)
            n = 0
            bulk_create_list = []

            for file in files_intersection:
                n += 1
                file1 = os.path.join(bc.branch_1.path(), file.name)
                content1 = read_file(file1)
                content1 = [cont.strip() for cont in content1.split('\n')]
                file2 = os.path.join(bc.branch_2.path(), file.name)
                content2 = read_file(file2)
                content2 = [cont.strip() for cont in content2.split('\n')]
                changed_file = False
                if content1 != content2:
                    changed_file = True
                processed_statements_1 = []
                processed_statements_2 = []
                linesfile1_list = []
                linesfile2_list = []

                for line in difflib.unified_diff(
                        content1,
                        content2,
                        fromfile='file1',
                        tofile='file2', lineterm='', n=0):
                    if line.startswith('@@'):
                        linesfile1, linesfile2 = get_changes(line)
                        linesfile1_list.extend(linesfile1)
                        linesfile2_list.extend(linesfile2)

                stat1_id = []
                statementsfile1 = []
                for linefile1 in linesfile1_list:
                    for statement in Statement.objects.filter(branch=bc.branch_1_id, file=file.id, ).all():
                        if linefile1 in statement.get_lines() and statement.id not in stat1_id:
                            statementsfile1.append(statement)
                            stat1_id.append(statement.id)

                stat2_id = []
                statementsfile2 = []
                for linefile2 in linesfile2_list:
                    for statement in Statement.objects.filter(branch=bc.branch_2_id, file=file.id, ).all():
                        if linefile2 in statement.get_lines() and statement.id not in stat2_id:
                            statementsfile2.append(statement)
                            stat2_id.append(statement.id)

                # statement1_tuple = []
                # for stat in statementsfile1:
                #     statement1_tuple.append(tuple([stat, stat.original_statement]))
                #
                # statement2_tuple = []
                # for stat in statementsfile2:
                #     statement2_tuple.append(tuple([stat, stat.original_statement]))

                statement1_tuple = []
                for stat in statementsfile1:
                    method_statement = MethodStatement.objects.filter(statement_id=stat.id).all()
                    methods_id = [m.method_id for m in method_statement]
                    method = Method.objects.filter(id__in=methods_id).order_by('start_line').last()
                    method_name = method.name if method else 'main'
                    message = f"{method_name} {stat.severity_level.name.replace('.', '')} {stat.message_with_variables}"
                    statement1_tuple.append(tuple([stat, message, method_name]))
                    # statement1_tuple.append(tuple([stat, stat.original_statement, method_name]))

                statement2_tuple = []
                for stat in statementsfile2:
                    method_statement = MethodStatement.objects.filter(statement_id=stat.id).all()
                    methods_id = [m.method_id for m in method_statement]
                    method = Method.objects.filter(id__in=methods_id).order_by('start_line').last()
                    method_name = method.name if method else 'main'
                    message = f"{method_name} {stat.severity_level.name.replace('.', '')} {stat.message_with_variables}"
                    statement2_tuple.append(tuple([stat, message, method_name]))
                    # statement2_tuple.append(tuple([stat, stat.original_statement, method_name]))


                pairs = make_pairs_of_elements(statement1_tuple, statement2_tuple)
                # print(pairs)

                for statement1, statement2, cos_sim in pairs:
                    if statement1.id not in processed_statements_1 and \
                            statement2.id not in processed_statements_2:
                        vector1_message = text_to_vector(statement1.message.message)
                        vector2_message = text_to_vector(statement2.message.message)
                        vector1_statement = text_to_vector(statement1.original_statement)
                        vector2_statement = text_to_vector(statement2.original_statement)
                        variables_1 = clear_message(statement1.message_with_variables)
                        variables_2 = clear_message(statement2.message_with_variables)
                        vector1_variable = text_to_vector(variables_1)
                        vector2_variable = text_to_vector(variables_2)

                        data = {'branch_1_id': bc.branch_1_id,
                                'branch_2_id': bc.branch_2_id,
                                'file_id': file.id,
                                'statement_1_id': statement1.id,
                                'statement_2_id': statement2.id,
                                'severity_level_1_id': statement1.severity_level_id,
                                'severity_level_2_id': statement2.severity_level_id,
                                'message_1_id': statement1.message_id,
                                'message_2_id': statement2.message_id,
                                'variable_count_1': statement1.count_variables,
                                'variable_count_2': statement2.count_variables,
                                'sentence_1': statement1.original_statement,
                                'sentence_2': statement2.original_statement,
                                'variables_1': statement1.variables,
                                'variables_2': statement2.variables,
                                'cosine_similarity': cos_sim,
                                'cosine_similarity_messages': get_cosine(vector1_message, vector2_message),
                                'cosine_similarity_statements': get_cosine(vector1_statement, vector2_statement),
                                'cosine_similarity_variables': get_cosine(vector1_variable, vector2_variable),
                                'category': UPDATED,
                                'changed_file': changed_file,
                                'file_exists_in_both_branches': YES}

                        processed_statements_1.append(statement1.id)
                        processed_statements_2.append(statement2.id)
                        bulk_create_list.append(
                            BranchFileComparison(**data))

                #####

                statementsfile1_not_in_diff = Statement.objects.filter(
                    branch=bc.branch_1_id,
                    file=file.id, ).exclude(id__in=stat1_id)

                statementsfile2_not_in_diff = Statement.objects.filter(
                    branch=bc.branch_2_id,
                    file=file.id, ).exclude(id__in=stat2_id)

                for statement1, statement2 in zip(statementsfile1_not_in_diff, statementsfile2_not_in_diff):
                    data = {
                        'branch_1_id': bc.branch_1_id,
                        'branch_2_id': bc.branch_2_id,
                        'file_id': file.id,
                        'statement_1_id': statement1.id,
                        'statement_2_id': statement2.id,
                        'severity_level_1_id': statement1.severity_level_id,
                        'severity_level_2_id': statement2.severity_level_id,
                        'message_1_id': statement1.message_id,
                        'message_2_id': statement2.message_id,
                        'variable_count_1': statement1.count_variables,
                        'variable_count_2': statement2.count_variables,
                        'sentence_1': statement1.original_statement,
                        'sentence_2': statement2.original_statement,
                        'variables_1': statement1.variables,
                        'variables_2': statement2.variables,
                        'cosine_similarity': 1,
                        'cosine_similarity_messages': 1,
                        'cosine_similarity_statements': 1,
                        'cosine_similarity_variables': 1,
                        'category': NO_UPDATED,
                        'changed_file': changed_file,
                        'file_exists_in_both_branches': YES}

                    processed_statements_1.append(statement1.id)
                    processed_statements_2.append(statement2.id)

                    bulk_create_list.append(
                        BranchFileComparison(**data))

                statementsfile1_not_in_diff = Statement.objects.filter(
                    branch=bc.branch_1_id,
                    file=file.id, ).exclude(id__in=processed_statements_1)

                statementsfile2_not_in_diff = Statement.objects.filter(
                    branch=bc.branch_2_id,
                    file=file.id, ).exclude(id__in=processed_statements_2)

                for statement1 in statementsfile1_not_in_diff:

                    if statement1.id not in processed_statements_1:
                        data = {'branch_1_id': bc.branch_1_id,
                                'branch_2_id': bc.branch_2_id,
                                'file_id': file.id,
                                'statement_1_id': statement1.id,
                                'statement_2_id': None,
                                'severity_level_1_id': statement1.severity_level_id,
                                'severity_level_2_id': None,
                                'message_1_id': statement1.message_id,
                                'message_2_id': None,
                                'variable_count_1': statement1.count_variables,
                                'variable_count_2': None,
                                'sentence_1': statement1.original_statement,
                                'sentence_2': None,
                                'variables_1': statement1.variables,
                                'variables_2': None,
                                'cosine_similarity': 0,
                                'cosine_similarity_messages': 0,
                                'cosine_similarity_statements': 0,
                                'cosine_similarity_variables': 0,
                                'category': DELETED,
                                'changed_file': changed_file,
                                'file_exists_in_both_branches': YES}

                        processed_statements_1.append(statement1.id)

                        bulk_create_list.append(
                            BranchFileComparison(**data))

                for statement2 in statementsfile2_not_in_diff:
                    if statement2.id not in processed_statements_2:
                        data = {'branch_1_id': bc.branch_1_id,
                                'branch_2_id': bc.branch_2_id,
                                'file_id': file.id,
                                'statement_1_id': None,
                                'statement_2_id': statement2.id,
                                'severity_level_1_id': None,
                                'severity_level_2_id': statement2.severity_level_id,
                                'message_1_id': None,
                                'message_2_id': statement2.message_id,
                                'variable_count_1': None,
                                'variable_count_2': statement2.count_variables,
                                'sentence_1': None,
                                'sentence_2': statement2.original_statement,
                                'variables_1': None,
                                'variables_2': statement2.variables,
                                'cosine_similarity': 0,
                                'cosine_similarity_messages': 0,
                                'cosine_similarity_statements': 0,
                                'cosine_similarity_variables': 0,
                                'category': ADDED,
                                'changed_file': changed_file,
                                'file_exists_in_both_branches': YES}

                        processed_statements_1.append(statement2.id)

                        bulk_create_list.append(
                            BranchFileComparison(**data))

                print(f'{n}/{total}', end='\r')

            logger.info(f'Existing files in the two releases - {n}/{total}')

            n = 0
            files = File.objects.filter(id__in=files1).exclude(id__in=files_intersection)
            total = len(files)
            for file in files:
                statements = Statement.objects.filter(file=file, branch=bc.branch_1).all()
                n += 1
                for statement1 in statements:
                    data = {'branch_1_id': bc.branch_1_id,
                            'branch_2_id': bc.branch_2_id,
                            'file_id': file.id,
                            'statement_1_id': statement1.id,
                            'statement_2_id': None,
                            'severity_level_1_id': statement1.severity_level_id,
                            'severity_level_2_id': None,
                            'message_1_id': statement1.message_id,
                            'message_2_id': None,
                            'variable_count_1': statement1.count_variables,
                            'variable_count_2': None,
                            'sentence_1': statement1.original_statement,
                            'sentence_2': None,
                            'variables_1': statement1.variables,
                            'variables_2': None,
                            'cosine_similarity': 0,
                            'cosine_similarity_messages': 0,
                            'cosine_similarity_statements': 0,
                            'cosine_similarity_variables': 0,
                            'category': DELETED,
                            'changed_file': changed_file,
                            'file_exists_in_both_branches': NO}

                    bulk_create_list.append(
                        BranchFileComparison(**data))

                print(f'{n}/{total}', end='\r')
            logger.info(f'Files existing only in the {bc.branch_1} release - {n}/{total}')

            n = 0
            files = File.objects.filter(id__in=files2).exclude(id__in=files_intersection)
            total = len(files)
            for file in files:
                statements = Statement.objects.filter(file=file, branch=bc.branch_2).all()
                n += 1
                for statement2 in statements:
                    data = {'branch_1_id': bc.branch_1_id,
                            'branch_2_id': bc.branch_2_id,
                            'file_id': file.id,
                            'statement_1_id': None,
                            'statement_2_id': statement2.id,
                            'severity_level_1_id': None,
                            'severity_level_2_id': statement2.severity_level_id,
                            'message_1_id': None,
                            'message_2_id': statement2.message_id,
                            'variable_count_1': None,
                            'variable_count_2': statement2.count_variables,
                            'sentence_1': None,
                            'sentence_2': statement2.original_statement,
                            'variables_1': None,
                            'variables_2': statement2.variables,
                            'cosine_similarity': 0,
                            'cosine_similarity_messages': 0,
                            'cosine_similarity_statements': 0,
                            'cosine_similarity_variables': 0,
                            'category': ADDED,
                            'changed_file': changed_file,
                            'file_exists_in_both_branches': NO,}

                    bulk_create_list.append(
                        BranchFileComparison(**data))
                print(f'{n}/{total}', end='\r')
            logger.info(f'Files existing only in the {bc.branch_2} release - {n}/{total}')

            BranchFileComparison.objects.bulk_create(
                bulk_create_list, batch_size=1000)

        with connection.cursor() as cursor:
            cursor.execute(UPDATE_BRANCH_FILE_COMPARISON)

        TimeTracker.save_time('Branch Comparison', time_initial)


