import os
import re
import sys
from datetime import datetime

sys.path.append("..")
import glob
import codecs
import logging
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from pathlib import Path
from git import Repo

logger = logging.getLogger('django')


class TimeTracker(models.Model):
    pipeline = models.CharField('Pipeline', max_length=50)
    system = models.CharField('System', max_length=50, null=True)
    branch = models.CharField('Branch', max_length=50, null=True)
    delta_time = models.DecimalField('Time (seconds)', decimal_places=4, max_digits=15)

    @staticmethod
    def save_time(pipeline, time_initial):
        delta = datetime.now() - time_initial
        data = {
            "pipeline": pipeline,
            "system": "",
            "branch": "",
            "delta_time": delta.total_seconds()}
        TimeTracker(**data).save()

    def __str__(self):
        return f"{self.id} - {self.pipeline}"


class SeverityLevel(models.Model):
    name = models.CharField('Name', max_length=500, unique=True)
    severity = models.IntegerField('Severity', default=0)

    def __str__(self):
        return self.name


class System(models.Model):
    name = models.CharField('Name', max_length=500, unique=True)
    github_url = models.CharField('GitHub URL', max_length=500, )
    cloned_date = models.DateTimeField(null=True, blank=True, )
    head = models.CharField('Head', max_length=50, null=True, blank=True, )
    version_regex = models.CharField(
        'Version detection regex',
        max_length=100, default='^(rel\/release-|release-)(?P<v1>\d+)\.(?P<v2>\d+)\.(?P<v3>\d+)$')

    def __str__(self):
        return self.name

    def get_branch_number(self):
        return Branch.objects.filter(system=self).count()

    def save(self, *args, **kwargs):
        self.name = re.sub(r"[^a-zA-Z0-9]", "", self.name)
        super(System, self).save(*args, **kwargs)

    def path(self):
        return str(os.path.join(settings.GIT_CLONE_PATH, self.name, 'main'))

    def get_tags(self):
        repo = Repo(self.path())
        tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
        return tags

    def clone_repositories(self):
        logger.info('Cloning repositories ...')
        try:
            create_dir_path = Path(self.path())
            create_dir_path.mkdir(parents=True, exist_ok=True)
            repo = Repo.clone_from(self.github_url, self.path())
            self.cloned_date = timezone.now()
            self.head = repo.head
            self.save()
        except Exception as e:
            logging.error(e)


class Branch(models.Model):
    system = models.ForeignKey(
        'System',
        on_delete=models.CASCADE,
        verbose_name='System',
        related_name='%(class)s_system', )
    name = models.CharField('Name', max_length=500, )
    std_version = models.CharField('Version (Standardized)', max_length=50, null=True, blank=True)
    version = models.IntegerField('Version Level 1', default=0)
    version2 = models.IntegerField('Version Level 2', default=0)
    version3 = models.IntegerField('Version Level 3', default=0)
    version4 = models.IntegerField('Version Level 4', default=0)
    tagged_date = models.DateTimeField('Tagged Date', null=True, blank=True)
    log_statement_number = models.IntegerField('Log Statement Number', default=0)
    file_number = models.IntegerField('File Number', null=True, blank=True)
    method_number = models.IntegerField('Method Number', null=True, blank=True)
    nloc = models.IntegerField('NLOC', null=True, blank=True)
    cyclomatic_complexity = models.IntegerField('Cyclomatic Complexity', null=True, blank=True)
    cloned_date = models.DateTimeField(null=True, blank=True, )
    head = models.CharField('Head', max_length=50, null=True, blank=True, )

    def save(self, *args, **kwargs):
        self.std_version = f"{self.version:02d}.{self.version2:02d}.{self.version3:02d}.{self.version4:02d}"
        super(Branch, self).save(*args, **kwargs)

    def save_time(self, pipeline, time_initial):
        delta = datetime.now() - time_initial
        TimeTracker(**{
            "pipeline": pipeline,
            "system": self.system.name,
            "branch": self.name,
            "delta_time": delta.total_seconds()}).save()

    class Meta:
        ordering = ['system', '-std_version']
        unique_together = ('system', 'version', 'version2', 'version3', 'version4',)

    def __str__(self):
        return f'{self.system.name}/{self.name}'

    def path(self):
        return str(os.path.join(settings.GIT_CLONE_PATH, self.system.name, self.name)) + '/'

    def clone_repositories(self):
        logger.info(f'Clonning repository {self.system.github_url}/{self.name}')
        try:
            create_dir_path = Path(self.path())
            create_dir_path.mkdir(parents=True, exist_ok=True)
            repo = Repo.clone_from(self.system.github_url, self.path(), branch=self.name, depth=1)
            self.cloned_date = timezone.now()
            self.head = repo.head
            self.save()
        except Exception as e:
            logging.error(e)
        logger.info(f'Repository {self.system.github_url}/{self.name} cloned')

    def delete_all_data(self):
        branch = self
        statements = Statement.objects.filter(branch=branch).all()
        file_id = [statement.file_id for statement in statements]
        Statement.objects.filter(branch=branch).delete()
        File.objects.filter(id__in=file_id).delete()
        branch.delete()

    def update_method_number_in_statement(self):
        methods = Method.objects.filter(branch_id=self.id).all()
        number = 0
        total = len(methods)
        logger.info("Update method number in statements.")
        for method in methods:
            number += 1
            Statement.objects.filter(
                line_number__gte=method.start_line,
                line_number_final__lte=method.end_line,
                branch_id=method.branch_id,
                file_id=method.file_id).update(method=method)
            if number % 100 == 0:
                logger.info(f'{number}/{total} processed... ')
        logger.info(f'{number}/{total} processed... ')

    def get_files(self):
        pathname = self.path() + "/**/*.java"
        files = glob.glob(pathname, recursive=True)
        filenames = [file.replace(self.path(), '') for file in files if not os.path.isdir(file)]
        filenames_list = []
        for filename in filenames:
            filenames_list.append(File(name=filename))
        File.objects.bulk_create(filenames_list, batch_size=500, ignore_conflicts=True)
        files = File.objects.filter(name__in=filenames)
        return files


class File(models.Model):
    name = models.CharField('Name', max_length=500, unique=True)
    system_number = models.IntegerField('System Number', default=-1)
    branch_number = models.IntegerField('Branch Number', default=-1)
    log_statement_number = models.IntegerField('Log Statement Number', default=-1)

    def __str__(self):
        return f'{self.name}'


class BranchComparison(models.Model):
    branch_1 = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        verbose_name='Branch1',
        related_name='%(class)s_branch1', )
    branch_2 = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        verbose_name='Branch2',
        related_name='%(class)s_branch2', )

    def __str__(self):
        return f'{self.branch_1.name} -> {self.branch_2.name}'

    class Meta:
        unique_together = (
            ('branch_1', 'branch_2',),
        )


class BranchFileComparison(models.Model):
    branch_1 = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        verbose_name='Branch 1',
        related_name='%(class)s_branch_1', )
    branch_2 = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        verbose_name='Branch 2',
        related_name='%(class)s_branch_2', )
    file = models.ForeignKey(
        'File',
        on_delete=models.CASCADE,
        verbose_name='File',
        related_name='%(class)s_file', )
    statement_1 = models.OneToOneField(
        'Statement',
        on_delete=models.CASCADE,
        verbose_name='Statement 1',
        related_name='%(class)s_statement_1',
        null=True)
    statement_2 = models.OneToOneField(
        'Statement',
        on_delete=models.CASCADE,
        verbose_name='Statement 2',
        related_name='%(class)s_statement_2',
        null=True)
    severity_level_1 = models.ForeignKey(
        'SeverityLevel',
        on_delete=models.CASCADE,
        verbose_name='Severity Level 1',
        related_name='%(class)s_severity_level_1', null=True)
    severity_level_2 = models.ForeignKey(
        'SeverityLevel',
        on_delete=models.CASCADE,
        verbose_name='Severity Level 2',
        related_name='%(class)s_severity_level_2', null=True)
    message_1 = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        verbose_name='Message 1',
        related_name='%(class)s_severity_message_1', null=True)
    message_2 = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        verbose_name='Message 2',
        related_name='%(class)s_severity_message_2', null=True)
    sentence_1 = models.TextField( null=True)
    sentence_2 = models.TextField( null=True)
    variables_1 = models.TextField( null=True)
    variables_2 = models.TextField( null=True)
    variable_count_1 = models.IntegerField(
        'Variable count 1', null=True)
    variable_count_2 = models.IntegerField(
        'Variable count 2', null=True)
    cosine_similarity = models.DecimalField(
        'Cosine of similarity',
        decimal_places=2, max_digits=5)
    cosine_similarity_messages = models.DecimalField(
        'Cosine of similarity between messages',
        decimal_places=2, max_digits=5)
    cosine_similarity_statements = models.DecimalField(
        'Cosine of similarity between statements',
        decimal_places=2, max_digits=5)
    cosine_similarity_variables = models.DecimalField(
        'Cosine of similarity between variables names',
        decimal_places=2, max_digits=5)
    changed_severity_level = models.IntegerField(
        'Changed severity level',
        choices=(
            (0, 'No'),
            (1, 'Yes')), null=True)
    changed_file = models.IntegerField(
        'Changed file',
        choices=(
            (0, 'No'),
            (1, 'Yes')), null=True)
    changed_variables = models.IntegerField(
        'Changed variables',
        choices=(
            (0, 'No'),
            (1, 'Yes')), null=True)
    changed_messages = models.IntegerField(
        'Changed message',
        choices=(
            (0, 'No'),
            (1, 'Yes')), null=True)
    file_exists_in_both_branches = models.IntegerField(
        'File exists in both branches',
        choices=(
            (1, 'Yes'),
            (0, 'No')))
    category = models.IntegerField(
        'Category',
        choices=(
            (1, 'Added'),
            (2, 'Updated'),
            (3, 'Deleted'),
            (4, 'No updated')))

    def __str__(self):
        return f'{self.branch_1.name} -> {self.branch_2.name}'

    # def save(self, *args, **kwargs):
    #
    #     self.changed_severity_level = 0
    #     if self.severity_level_1 != self.severity_level_2:
    #         self.changed_severity_level = 1
    #
    #     self.changed_variables = 0
    #     if self.variable_count_1 != self.variable_count_2:
    #         self.changed_variables = 1
    #
    #     self.changed_messages = 0
    #     if self.message_1 != self.message_2:
    #         self.changed_messages = 1
    #
    #     super(BranchFileComparison, self).save(*args, **kwargs)



# SELECT distinct file_id,
# sum(quant_lines_2)-sum(quant_lines_1) as nlog_changed
# 	FROM stage.changes
# 	WHERE category='Updated'
# 	GROUP BY file_id;

class BranchFile(models.Model):
    branch = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        verbose_name='Branch',
        related_name='%(class)s_branch', )
    file = models.ForeignKey(
        'File',
        on_delete=models.CASCADE,
        verbose_name='File',
        related_name='%(class)s_file', )
    nloc = models.IntegerField(
        'NLOC (Number lines of code without comments)')
    nlog_without_log_statements = models.IntegerField(
        'NLOG (Number lines of log code without_log_statements)')
    nlog = models.IntegerField(
        'NLOG (Number lines of log code)')

    def __str__(self):
        return f'{self.branch.name} {self.file.name}'

    class Meta:
        unique_together = ('branch', 'file',)


class Method(models.Model):
    branch = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        verbose_name='Branch',
        related_name='%(class)s_branch', )
    file = models.ForeignKey(
        'File',
        on_delete=models.CASCADE,
        verbose_name='File',
        related_name='%(class)s_file', )
    name = models.TextField('Name')
    cyclomatic_complexity = models.IntegerField('Cyclomatic Complexity')
    nloc = models.IntegerField('NLOC (Lines of code without comments)')
    token_count = models.IntegerField('Token Count')
    long_name = models.TextField('Long Name')
    start_line = models.IntegerField('Start Line')
    end_line = models.IntegerField('End line')
    full_parameters_json = models.TextField('Full Parameters (JSON)')
    filename = models.TextField('File Name')
    relative_filename = models.TextField('File Name (Reference)')
    top_nesting_level = models.IntegerField('Top Nesting Level')
    fan_in = models.IntegerField('Fan In')
    fan_out = models.IntegerField('Fan Out')
    general_fan_out = models.IntegerField('General Fan Out')
    parameters_count = models.IntegerField('Parameters Count')
    code = models.TextField('Code', null=True, blank=True)
    code_raw = models.TextField('Code (raw)', null=True, blank=True)
    severity_level_number = models.IntegerField('Severity Level Number', default=-1)

    conditional_statements_number = models.IntegerField('Conditional Statement sNumber', default=-1)
    catch_blocks_statements_number = models.IntegerField('Catch/blocks Statements Number', default=-1)
    looping_statements_number = models.IntegerField('Looping Statements Number', default=-1)
    continue_statements_number = models.IntegerField('continue Statements Number', default=-1)
    break_statements_number = models.IntegerField('Beeak Statements Number', default=-1)
    log_statement_number = models.IntegerField('Log Statements Number', default=-1)

    def __str__(self):
        return f'{self.name}'


class Statement(models.Model):
    cols = {
        'original_statement': 12,
        'message_with_variables': 12,
        'line_text': 12,
    }
    branch = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        verbose_name='Branch',
        related_name='%(class)s_branch', )
    file = models.ForeignKey(
        'File',
        on_delete=models.CASCADE,
        verbose_name='File',
        related_name='%(class)s_file', )
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        verbose_name='Message',
        related_name='%(class)s_message', )
    severity_level = models.ForeignKey(
        'SeverityLevel',
        on_delete=models.CASCADE,
        verbose_name='SeverityLevel',
        related_name='%(class)s_severity_level', )
    line_number = models.IntegerField('Line Number (initial)')
    line_number_final = models.IntegerField('Line Number (final)')
    count_variables = models.IntegerField('Count variables')
    code_snippet = models.TextField('Code Snippet', null=True, blank=True)
    span_initial = models.IntegerField('Span initial')
    span_final = models.IntegerField('Span final')
    is_in_comment = models.BooleanField('Is in comment?', default=True)
    is_in_test = models.BooleanField('Is in tests?', default=True)
    conditional_statements_number = models.IntegerField(
        'Conditional statements number', default=-1)
    looping_statements_number = models.IntegerField(
        'Looping statements number', default=-1)
    is_in_continue_statement = models.BooleanField('Is in continue statement?', default=False)
    is_in_break_statement = models.BooleanField('Is in break statement?', default=False)
    catch_blocks_statements_number = models.IntegerField(
        'Catch blocks statements number', default=-1)
    original_statement = models.TextField('Statement', )
    variables = models.TextField('Variables', )
    message_with_variables = models.TextField('Message with variables', )
    message_without_variables = models.TextField('Message without variables', )
    line_text = models.TextField('Line text', )
    message_words_count = models.IntegerField(
        'Message words count', default=-1)
    uses_string_concatenation = models.BooleanField(
        'Uses string concatenation?', default=False)
    message_length = models.IntegerField('Message Length without variables', )

    def __str__(self):
        return f'{self.original_statement}'

    def get_lines(self):
        return list(range(self.line_number, self.line_number_final + 1))

    def get_code(self):
        filename = os.path.join(settings.GIT_CLONE_PATH, self.branch.path(), self.file.name)
        if os.path.isfile(filename):
            file = codecs.open(filename, "r", "utf-8")
            content = file.read()
            file.close()
            content = content.split('\n')
            if self.line_number > 10:
                return '\n'.join(content[self.line_number - 10:self.line_number + 10])
            elif self.line_number > len(content) - 10:
                return '\n'.join(content[self.line_number - 20:])
            else:
                return '\n'.join(content[:self.line_number + 20])

    class Meta:
        unique_together = ('branch', 'file', 'line_number',)


class MethodStatement(models.Model):
    statement = models.ForeignKey(
        'Statement',
        on_delete=models.CASCADE,
        verbose_name='Statement',
        related_name='%(class)s_statement')
    method = models.ForeignKey(
        'Method',
        on_delete=models.CASCADE,
        verbose_name='Method',
        related_name='%(class)s_method')


class Message(models.Model):
    message = models.TextField('Message')
    message_length = models.IntegerField('Message Length without variables', )
    count_variables = models.IntegerField('Count variables')
    file_number = models.IntegerField('File Number', default=-1)
    log_statement_number = models.IntegerField('Log Statement Number', default=-1)
    severity_level_number = models.IntegerField('Severity Level Number', default=-1)
    branch_number = models.IntegerField('Branch Number', default=-1)
    system_number = models.IntegerField('System Number', default=-1)

    def __str__(self):
        return f'{self.message}'

    def counter_variables(self):
        statements = Statement.objects.filter(message_id=self.id)
        self.file_number = statements.values('file').distinct().count()
        self.severity_level_number = statements.values('severity_level').distinct().count()
        self.branch_number = statements.values('branch').distinct().count()
        self.log_statement_number = statements.distinct().count()
        self.save()
