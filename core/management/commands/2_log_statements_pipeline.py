import codecs
import glob
import logging
import os
import re
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import connection

from core.models import System, Branch, Statement, File, Message, SeverityLevel, TimeTracker

logger = logging.getLogger('django')

codecs.register_error("strict", codecs.ignore_errors)


class Structure:

    def __init__(self, filename):
        self.filename = filename
        self.content = None
        self.content_raw = None
        self.comments = {}
        self.parentheses = {}
        self.brackets = {}
        self.strings = {}
        self.statements = {}
        self.statements_types = ['for', 'if', 'else', 'while', 'try', 'catch', ]
        for statement in self.statements_types:
            self.statements[statement] = {}

    def save_file(self, filename, content):
        file = codecs.open(filename, "w", "utf-8")
        file.write(content)
        file.close()

    def read_file(self):
        if os.path.isfile(self.filename):
            file = codecs.open(self.filename, "r", "utf-8")
            content = file.read()
            file.close()
            content = content.split('\n')
            content = '\n'.join(content)
            self.content_raw = content
            self.content = content
        else:
            raise NameError('Unable to read file %s.' % self.filename)

    def get_comments(self):
        content = self.get_strings()
        matchs = re.finditer(r'\/\/.*', content)
        for match in matchs:
            initial, end = match.span()
            replacement = '*' * (end - initial)
            content = content[:initial] + replacement + content[end:]
            self.comments[initial] = end
        matchs = re.finditer(r'^[ \t]*\/\*[\S\s]*?\*\/[ \t]*$', self.content, re.MULTILINE)
        for match in matchs:
            initial, end = match.span()
            replacement = '\n'.join(['*' * len(part) for part in self.content[initial:end].split('\n')])
            content = content[:initial] + replacement + content[end:]
            self.comments[initial] = end
        return content

    def get_strings(self):
        content = self.content
        content = content.replace(r'\"', '""')
        matchs = re.finditer(r'"[^"]*"', content)
        for match in matchs:
            initial, end = match.span()
            replacement = '*' * (end - initial)
            content = content[:initial] + replacement + content[end:]
            self.strings[initial] = end
        return content

    def get_brackets(self):
        content = self.get_comments()
        matchs = list(re.finditer(r'{[^{}]*}', content))
        while len(matchs) > 0:
            for match in matchs:
                initial, end = match.span()
                replacement = '\n'.join(['*' * len(part) for part in self.content[initial:end].split('\n')])
                content = content[:initial] + replacement + content[end:]
                self.brackets[initial] = end
            matchs = list(re.finditer(r'{[^{}]*}', content))
        return content

    def get_parentheses(self):
        content = self.get_comments()
        matchs = list(re.finditer(r'\([^()]*\)', content, re.ASCII))
        while len(matchs) > 0:
            for match in matchs:
                initial, end = match.span()
                # print(end, content[initial:end])
                # print(end, self.content[initial:end])
                replacement = '\n'.join(['*' * len(part) for part in self.content[initial:end].split('\n')])
                content = content[:initial] + replacement + content[end:]
                self.parentheses[initial] = end
            matchs = list(re.finditer(r'\([^()]*\)', content, re.ASCII))
        return content

    def get_statements(self):
        content = self.get_comments()
        for statement in self.statements:
            matchs = list(re.finditer(statement + '[^{]*{', content))
            for match in matchs:
                initial, end = match.span()
                print(self.filename)
                print(content[initial:end])
                self.statements[statement][end] = self.brackets[end - 1]

    def remove_log_statements(self):
        content = self.get_comments()
        matchs = re.finditer(
            r"(?i)[a-zA-Z0-9]*log[a-zA-Z0-9]*[\s]*\.[\s]*(|log\([a-zA-Z0-9\.]*)(?P<severity_level>fatal|error|warning|info|debug|trace|severe|warn|config|fine|finer|finest)[\s]*(\(|\,)",
            content)
        for match in matchs:
            initial, end = match.span()
            replacement = '*' * (end - initial)
            content = content[:initial] + replacement + content[end:]
        return content

    def load(self):
        self.read_file()
        self.get_strings()
        self.get_comments()
        self.get_brackets()
        self.get_parentheses()
        # self.get_statements()


class LogStatement:

    def __init__(self, file):
        self.file = file
        self.__log_commands_dict = []
        self.search_conditional_statements = []
        self.search_catch_blocks = []
        self.search_looping_statements = []
        structure = Structure(file)
        structure.load()
        self.structure = structure
        self.get_block_statement()

    def get_log_commands(self):
        return self.__log_commands_dict

    def __save_file(self, filename, content):
        file = codecs.open(filename, "w", "utf-8")
        file.write(content)
        file.close()

    def __read_file(self, filename):
        if os.path.isfile(filename):
            file = codecs.open(filename, "r", "utf-8")
            content = file.read()
            file.close()
            content = content.split('\n')
            content = '\n'.join(content)
            return content
        else:
            raise NameError('Unable to read file %s.' % filename)

    def get_block_statement(self):
        content = self.__read_file(self.file)

        regex_search_conditional_statements = re.finditer(r'(if|else|switch)\s*\([\s\S]*?\)\s*\{', content)
        search_conditional_statements = []
        for item in regex_search_conditional_statements:
            initial, final = item.span()
            search_conditional_statements.append(final)
        self.search_conditional_statements = search_conditional_statements

        regex_search_catch_blocks = re.finditer(r'(try|catch)\s*(\([\s\S]*?\)\s*)?\{', content)
        search_catch_blocks = []
        for item in regex_search_catch_blocks:
            initial, final = item.span()
            search_catch_blocks.append(final)
        self.search_catch_blocks = search_catch_blocks

        regex_search_looping_statements = re.finditer(r'(for|while)\s*(\([\s\S]*?\)\s*)\{', content)
        search_looping_statements = []
        for item in regex_search_looping_statements:
            initial, final = item.span()
            search_looping_statements.append(final)
        self.search_looping_statements = search_looping_statements

    def __get_statements_number(self, span_initial, span_final):
        content = self.__read_file(self.file)
        counter = {}
        counter['conditional_statements_number'] = 0
        counter['looping_statements_number'] = 0
        # counter['control_jump_statements_number'] = -1  # TODO
        counter['is_in_continue_statement'] = False
        counter['is_in_break_statement'] = False
        counter['catch_blocks_statements_number'] = 0
        regex_recursiva = r'\{[^{}]*\}'
        level = 0
        while len(re.findall(regex_recursiva, content)):
            items = re.finditer(regex_recursiva, content)
            for item in items:
                initial, final = item.span()
                total_chars = final - initial
                if span_initial >= initial and span_final <= final:
                    if len(re.findall(r'continue[\w\s]*;', content[initial:final])) and level == 0:
                        counter['is_in_continue_statement'] = True
                    if len(re.findall(r'break[\w\s]*;', content[initial:final])) and level == 0:
                        counter['is_in_break_statement'] = True
                    level += 1
                    if initial + 1 in self.search_conditional_statements:
                        counter['conditional_statements_number'] += 1
                    if initial + 1 in self.search_looping_statements:
                        counter['looping_statements_number'] += 1
                    if initial + 1 in self.search_catch_blocks:
                        counter['catch_blocks_statements_number'] += 1
                content = content[0:initial] + '*' * total_chars + content[final:]
        return counter

    def __get_message(self, text):
        text = text.strip()
        count_parentheses = 1
        quotes = False
        for n in range(len(text)):
            if text[n] == '"' and not quotes and text[n - 1] != '\\':
                quotes = True
            elif text[n] == '"' and quotes and text[n - 1] != '\\':
                quotes = False
            elif text[n] == '(' and not quotes:
                count_parentheses += 1
            elif text[n] == ')' and not quotes:
                count_parentheses -= 1
            if count_parentheses == 0:
                return text[:n]

    def __clear_message(self, message):
        message = message.strip()
        message = message.replace('\\n', ' ')
        message = message.replace('\\t', ' ')
        message = message.replace('\\r', ' ')
        message = re.sub('\"[\s]*\+[\s]*\"', '', message)
        message = re.sub('[\s]{1,}', ' ', message)
        return message

    def __remove_variables(self, message, variable_number):
        message = self.__clear_variables(message, variable_number)
        message = message.replace('{}', '')
        message = re.sub('[^A-Za-z0-9 ]', ' ', message)
        message = re.sub('[\s]{1,}', ' ', message)
        return message.strip().lower()

    def __clear_variables(self, message, variable_number):
        message = message.strip()
        message = message.replace('\\n', ' ')
        message = message.replace('\\t', ' ')
        message = message.replace('\\r', ' ')
        message = re.sub('\"[\s]*\+[\s]*\"', '', message)
        message = re.sub('[\s]{1,}', ' ', message)
        message = message.replace(r'\"', "''")
        matchs = re.finditer(r'"[^"]*"', message)
        new_message = ""
        end = len(message)
        matchs_number = 0
        variables = len(message.split('{}')) - 1
        for match in matchs:
            matchs_number += 1
            initial, end = match.span()
            if initial == 0:
                new_message += message[initial + 1:end - 1]
            else:
                variables += 1
                new_message += '{}' + message[initial + 1:end - 1]
        while variables < variable_number:
            variables += 1
            new_message += '{}'
        return new_message

    def get_code(self, line_number):
        if os.path.isfile(self.file):
            file = codecs.open(self.file, "r", "utf-8")
            content = file.read()
            file.close()
            content = content.split('\n')
            if line_number > 10:
                return '\n'.join(content[line_number - 10:line_number + 10])
            elif line_number > len(content) - 10:
                return '\n'.join(content[line_number - 20:])
            else:
                return '\n'.join(content[:line_number + 20])

    def __count_variables(self, original_statement):
        original_statement = original_statement.replace('\n', ' ')
        match_string = re.sub(r'".*?"', "", original_statement)
        match_string = re.sub(r'\+\ *\+', "+", match_string)
        match_string = match_string.replace(',', '+').strip()
        match_string = re.sub(r'(^[ ]*\+|\+[ ]*$)', "", match_string)
        variable_names = [name.strip() for name in match_string.strip().split('+') if name.strip()]
        count = len(variable_names)
        return count, variable_names

    def __is_in_test(self):
        if '/examples/' in self.file.lower() or '/tests/' in self.file.lower():
            return 1
        return 0

    def __is_in_comments(self, initial, end):
        for block_initial in self.structure.comments:
            if initial >= block_initial and end <= self.structure.comments[block_initial]:
                return 1
        return 0

    def __is_in_statements(self, statement, initial, end):
        count = 0
        for block_initial in self.structure.statements[statement]:
            if initial >= block_initial and end <= self.structure.statements[statement][block_initial]:
                return 1
        return count

    def process(self):
        REGEX_VERIFIER = [
            r"(?i)[a-zA-Z0-9]*log[a-zA-Z0-9]*[\s]*\.[\s]*(|log\([a-zA-Z0-9\.]*)(?P<severity_level>fatal|error|warning|info|debug|trace|severe|warn|config|fine|finer|finest)[\s]*(\(|\,)",
            r"(?P<severity_level>System\.out\.println|System\.err\.println)\(",
        ]
        content = self.__read_file(self.file)
        content_list = []

        for regex in REGEX_VERIFIER:
            matchs = re.finditer(regex, self.structure.get_comments(), re.DOTALL)

            for match in matchs:
                dict_content = match.groupdict()
                initial, end = match.span()
                if not 'severity_level' in dict_content:
                    dict_content['severity_level'] = "PRINT_STATEMENT"
                match_content = content[initial:end]
                last_parentheses = initial + len(match_content.split('(')[0])
                if last_parentheses not in self.structure.parentheses:
                    message = content[end:].split(")")[0]
                    logger.error(f"Error when processing file: {self.file}. Captured message: `{message}`")
                else:
                    message = content[end:self.structure.parentheses[last_parentheses] - 1]
                line_number = len(content[:initial].split('\n'))
                line = content.split('\n')[line_number - 1]
                if message:
                    dict_content['severity_level'] = dict_content['severity_level'].upper()
                    dict_content['line_number'] = len(content[:initial].split('\n'))
                    dict_content['line_number_final'] = len(content[:end + len(message)].split('\n'))
                    dict_content['filename'] = self.file
                    dict_content['span_initial'] = initial
                    dict_content['span_final'] = end
                    dict_content['message_with_variables'] = self.__clear_message(message)
                    dict_content['count_variables'], dict_content['variables'] = self.__count_variables(
                        dict_content['message_with_variables'])
                    dict_content['message_without_variables'] = self.__remove_variables(
                        message, dict_content['count_variables'])
                    dict_content['message_words_count'] = len(dict_content['message_without_variables'].split(' '))
                    dict_content['original_statement'] = content[initial:end + len(message) + 1]
                    dict_content['message'] = self.__clear_variables(message, dict_content['count_variables'])
                    dict_content['message_length'] = len(dict_content['message'].replace('{}', ''))
                    dict_content['line_text'] = line
                    dict_content['is_in_test'] = self.__is_in_test()
                    dict_content['is_in_comment'] = self.__is_in_comments(initial, end)
                    dict_content['code_snippet'] = self.get_code(dict_content['line_number'])
                    uses_string_concatenation_regex = re.findall(
                        r'(\+\s*\".+\"|\".+\"\s*\+)',
                        dict_content['original_statement'], re.DOTALL)
                    dict_content['uses_string_concatenation'] = True if len(
                        uses_string_concatenation_regex) > 0 else False
                    counter = self.__get_statements_number(initial, end)
                    dict_content.update(counter)
                    content_list.append(dict_content)
        return content_list


class Repository:

    def __init__(self, path):
        self.path = path

    def process_files(self):
        pathname = self.path + "/**/*.java"
        files = glob.glob(pathname, recursive=True)
        files_batch_list = []
        files_list = []
        files_batch = 500
        num_files = 0
        for file in files:
            num_files += 1
            files_list.append(file)
            if len(files_list) == files_batch:
                files_batch_list.append(files_list)
                files_list = []
        files_batch_list.append(files_list)
        return files_batch_list


def execute_statements_pipeline(branch):
    branch.log_statement_number = 0
    branch.save()
    Statement.objects.filter(branch_id=branch.id).delete()
    repo = Repository(str(branch.path()))
    files_batch_list = repo.process_files()
    log_statement_number = 0
    for files_batch in files_batch_list:
        commands = []
        len_files = len(files_batch)
        number = 0
        for file in files_batch:
            number += 1
            if not os.path.isdir(file):
                log = LogStatement(file)
                data = log.process()
                commands = commands + data
            if number % 100 == 0:
                logger.info(f'{number}/{len_files} files processed... ')
        logger.info(f'{number}/{len_files} files processed... ')

        log_statement_number += len(commands)

        filenames = set()
        messages = set()
        levels = set()

        logger.info(f"Started {branch.system.name}/{branch.name} ...")
        number = 0
        for command in commands:
            filenames.add(command['filename'].replace(branch.path(), ''))
            messages.add(command['message'])
            levels.add(command['severity_level'])
            number += 1
            if number % 100 == 0:
                logger.info(f'{number}/{len(commands)} processed... ')
        logger.info(f'{number}/{len(commands)} processed... ')

        filenames_dict = {}
        messages_dict = {}
        levels_dict = {}

        logger.info(f"{branch.system.name}/{branch.name} - processing filenames...")
        number = 0
        filenames_list = []
        for filename in filenames:
            filenames_list.append(File(name=filename))
            number += 1
            if number % 500 == 0:
                logger.info(f'{number}/{len(filenames)} processed... ')
                File.objects.bulk_create(filenames_list, ignore_conflicts=True)
                filenames_list = []
        logger.info(f'{number}/{len(filenames)} processed... ')

        logger.info(f"{branch.system.name}/{branch.name} - saving filenames...")
        number = 0
        File.objects.bulk_create(filenames_list, ignore_conflicts=True)
        all_filenames = File.objects.all()
        for filename in all_filenames:
            filenames_dict[filename.name] = filename.id
            number += 1
            if number % 100 == 0:
                logger.info(f'{number}/{len(all_filenames)} processed... ')
        logger.info(f'{number}/{len(all_filenames)} processed... ')

        logger.info(f"{branch.system.name}/{branch.name} - processing messages...")
        number = 0
        messages_list = []
        for message in messages:
            count_variables = len(message.split('{}')) - 1
            message_length = len(message.replace('{}', ''))
            if not Message.objects.filter(message=message).all():
                messages_list.append(
                    Message(message=message, message_length=message_length, count_variables=count_variables))
            number += 1
            if number % 500 == 0:
                logger.info(f'{number}/{len(messages)} processed... ')
                Message.objects.bulk_create(messages_list, ignore_conflicts=True)
                messages_list = []
        logger.info(f'{number}/{len(messages)} processed... ')

        logger.info(f"{branch.system.name}/{branch.name} - saving messages...")
        number = 0
        Message.objects.bulk_create(messages_list, ignore_conflicts=True)
        all_messages = Message.objects.all()
        for message in all_messages:
            messages_dict[message.message] = message.id
            number += 1
            if number % 100 == 0:
                logger.info(f'{number}/{len(all_messages)} processed... ')
        logger.info(f'{number}/{len(all_messages)} processed... ')

        logger.info(f"{branch.system.name}/{branch.name} - processing levels...")
        number = 0
        for level in levels:
            level_obj, _ = SeverityLevel.objects.get_or_create(name=level)
            levels_dict[level] = level_obj.id
            number += 1
            if number % 100 == 0:
                logger.info(f'{number}/{len(levels)} processed... ', end='')
        logger.info(f'{number}/{len(levels)} processed... ')

        logger.info(f"{branch.system.name}/{branch.name} - creating bulk for save...")
        number = 0
        bulk_create_list = []
        for command in commands:
            filename = command['filename'].replace(branch.path(), '')
            message = command['message']
            level = command['severity_level']
            command['branch_id'] = branch.id
            command['file_id'] = filenames_dict[filename]
            command['message_id'] = messages_dict[message]
            command['severity_level_id'] = levels_dict[level]
            del command['message']
            del command['severity_level']
            del command['filename']
            bulk_create_list.append(
                Statement(**command))
            number += 1
            if number % 500 == 0:
                logger.info(f'{number}/{len(commands)} processed... ')
                Statement.objects.bulk_create(bulk_create_list, ignore_conflicts=True)
                bulk_create_list = []
        logger.info(f'{number}/{len(commands)} processed... ')

        logger.info(f"{branch.system.name}/{branch.name} - Saving bulk...")
        Statement.objects.bulk_create(bulk_create_list, ignore_conflicts=True)
    branch.log_statement_number = log_statement_number
    branch.save()
    logger.info(f"{branch.system.name}/{branch.name} - Finishing! This may still take a few minutes...")


SQL_UPDATE_MESSAGES = """
WITH messages AS (
SELECT s.message_id,
	COUNT(DISTINCT b.system_id) AS system_number,
	COUNT(DISTINCT s.branch_id) AS branch_number,
	COUNT(DISTINCT s.severity_level_id) AS severity_level_number,
	COUNT(DISTINCT s.file_id) AS file_number,
	COUNT(s.id) AS log_statement_number
	FROM public.core_statement s
    JOIN public.core_branch b ON b.id = s.branch_id
	GROUP BY s.message_id)
UPDATE public.core_message s
   SET system_number = m.system_number,
       branch_number = m.branch_number,
       log_statement_number = m.log_statement_number,
       severity_level_number = m.severity_level_number,
       file_number = m.file_number
  FROM messages m
 WHERE s.id = m.message_id;
"""


SQL_UPDATE_FILES = """
WITH files AS (
SELECT s.file_id,
	COUNT(DISTINCT b.system_id) AS system_number,
	COUNT(DISTINCT s.branch_id) AS branch_number,
	COUNT(s.id) AS log_statement_number
	FROM public.core_statement s
    JOIN public.core_branch b ON b.id = s.branch_id
	GROUP BY s.file_id)
UPDATE public.core_file s
   SET system_number = m.system_number,
       branch_number = m.branch_number,
       log_statement_number = m.log_statement_number
  FROM files m
 WHERE s.id = m.file_id;
"""

class Command(BaseCommand):

    def handle(self, *args, **options):
        time_initial = datetime.now()
        logger = logging.getLogger('django')
        systems = System.objects.all()

        for system in systems:

            branchs = Branch.objects.filter(system=system, log_statement_number=0). \
                order_by('version', 'version2', 'version3', 'version4').all()
            for branch in branchs:
                logger.info(f'Processing log statements: System: {system.name}/{branch.name}')
                time_initial_branch = datetime.now()
                execute_statements_pipeline(branch)
                branch.save_time('Extract Log Statements', time_initial_branch)

        with connection.cursor() as cursor:
            cursor.execute(SQL_UPDATE_MESSAGES)
            cursor.execute(SQL_UPDATE_FILES)

        TimeTracker.save_time('Extract Log Statements', time_initial)