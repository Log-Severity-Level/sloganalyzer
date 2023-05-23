from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.urls import reverse
from django.utils.safestring import mark_safe
from core.models import *


class StatementWithoutBranchVerifierFilter(SimpleListFilter):
    title = 'Statement without branch verifier'
    parameter_name = 'statement_without_branch_verifier'

    def lookups(self, request, model_admin):
        return [
            (1, 'Only statement with branch verifier'),
            (2, 'Only statement without branch verifier'), ]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(branchverifier_id__isnull=True)
        if self.value() == '2':
            return queryset.filter(branchverifier_id__isnull=True)


class BranchVerifierWithoutStatementFilter(SimpleListFilter):
    title = 'Branch verifier without statement'
    parameter_name = 'branch_verifier_without_statement'

    def lookups(self, request, model_admin):
        return [
            (1, 'Only branch verifier with statements'),
            (2, 'Only branch verifier without statements'), ]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(statement_id__isnull=True)
        if self.value() == '2':
            return queryset.filter(statement_id__isnull=True)


@admin.action(description='Analyse files')
def analyse_files(modeladmin, request, queryset):
    for branch in queryset:
        branch.analyse_files()


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_per_page = 10

    list_filter = (
        'system', )
    list_display = (
        'system',
        'name',
        'std_version',
        'log_statement_number',
        'file_number',
        'method_number',
        'nloc',
        'cyclomatic_complexity',
        'cloned_date', )
    readonly_fields = (
        'std_version',
        'version',
        'version2',
        'version3',
        'version4',
        'tagged_date',
        'log_statement_number',
        'file_number',
        'method_number',
        'nloc',
        'cyclomatic_complexity',
        'cloned_date',
        'head',
    )
    # actions = [analyse_files, ]
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False


class BranchInline(admin.TabularInline):
    list_per_page = 10
    model = Branch
    readonly_fields = (
        'tagged_date',
        'log_statement_number',
        'file_number',
        'method_number',
        'nloc',
        'cyclomatic_complexity',
        'cloned_date', 
        'head')
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False


@admin.action(description='Clone repositories')
def clone_repositories(modeladmin, request, queryset):
    for obj in queryset:
        try:
            create_dir_path = Path(obj.path())
            create_dir_path.mkdir(parents=True, exist_ok=True)
            repo = Repo.clone_from(obj.github_url, obj.path())
            obj.head = repo.head
            obj.cloned_date = timezone.now()
            obj.save()
            messages.add_message(request, messages.INFO, mark_safe(f"Repository {obj.github_url} was cloned"))
        except Exception as e:
            logging.error(e)
            messages.add_message(request, messages.ERROR, e)

        for branch in obj.branch_system.all():
            try:
                branch.clone_repositories()
                messages.add_message(request, messages.INFO, mark_safe(f"Repository {obj.github_url}/{branch.name} was cloned"))
            except Exception as e:
                logging.error(e)
                messages.add_message(request, messages.ERROR, e)


@admin.action(description='Process repositories')
def process_repositories(modeladmin, request, queryset):
    for obj in queryset:
        for branch in obj.branch_system.all():
            logging.info(f'Processing branch {branch.name}')
            try:
                branch.process_repositories()
                messages.add_message(request, messages.INFO, f'{branch.name} processed!')
            except Exception as e:
                logging.error(e)
                messages.add_message(request, messages.ERROR, e)


@admin.action(description='Delete repositories')
def delete_repositories(modeladmin, request, queryset):
    for obj in queryset:
        for branch in obj.branch_system.all():
            logging.info(f'Deleting branch {branch.name}')
            try:
                branch.delete_all_data()
                messages.add_message(request, messages.INFO, f'{branch.name} deleted')
            except Exception as e:
                logging.error(e)
                messages.add_message(request, messages.ERROR, e)


def standartize(number):
    while len(number) < 3:
        number = '0' + number
    return number

def get_version_std(target_string):
    regex = r'(\d+)\.(\d+)\.(\d+)'
    result = re.search(regex, target_string)
    if result:
        g = [standartize(gr) for gr in result.groups()]
        return '.'.join(g)
    else:
        return target_string


@admin.action(description='Import tags from git')
def import_tags(modeladmin, request, queryset):
    import datetime
    for system in queryset:
        system.clone_repositories()
        tags = system.get_tags()
        bulk_create_list = []
        n = 0
        length = len(tags)
        for tag in tags:
            committed_date = datetime.datetime.fromtimestamp(tag.commit.committed_date)
            m = re.match(system.version_regex, tag.name)
            if m:
                version_dict = m.groupdict()
                if not 'v2' in version_dict:
                    version_dict['v2'] = 0
                if not 'v3' in version_dict or not (version_dict.get('v3')):
                    version_dict['v3'] = 0
                if not 'v4' in version_dict or not (version_dict.get('v4')):
                    version_dict['v4'] = 0
                branch = {
                    'system': system,
                    'name': tag.name,
                    'tagged_date': committed_date,
                    'version': int(version_dict['v1']),
                    'version2': int(version_dict['v2']),
                    'version3': int(version_dict['v3']),
                    'version4': int(version_dict['v4']),
                }
                n += 1
                print(f'{n}/{length}', end='\r')
                bulk_create_list.append(Branch(**branch))
        print(f'{n}/{length}', end='\r')
        Branch.objects.bulk_create(
            bulk_create_list, batch_size=500, ignore_conflicts=True)


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_per_page = 10

    def get_branch_number(self, obj):
        return obj.get_branch_number()

    get_branch_number.short_description = 'Branch Number'
    list_display = (
        'name',
        'github_url',
        'get_branch_number', )
    readonly_fields = ('cloned_date', 'head')
    inlines = [BranchInline, ]
    actions = [
        import_tags,
        # clone_repositories,
        # process_repositories,
        delete_repositories, ]


class StatementWithoutMethodFilter(SimpleListFilter):
    title = 'statement_without_method'
    parameter_name = 'statement_without_method'

    def lookups(self, request, model_admin):
        return [
            (1, 'Only statements with method'),
            (2, 'Only statements without method'), ]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(method_id__isnull=True)
        if self.value() == '2':
            return queryset.filter(method_id__isnull=True)


class StatementWithoutBranchVerifierFilter(SimpleListFilter):
    title = 'statement_without_branch_verifier'
    parameter_name = 'statement_without_branch_verifier'

    def lookups(self, request, model_admin):
        return [
            (1, 'Only statements with branch verifier'),
            (2, 'Only statements without branch verifier'), ]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(branchverifier_id__isnull=True)
        if self.value() == '2':
            return queryset.filter(branchverifier__isnull=True)


@admin.register(Statement)
class StatementAdmin(admin.ModelAdmin):
    list_per_page = 10

    def display_message(self, obj):
        return mark_safe(obj.message.message)
    display_message.allow_tags = True
    display_message.short_description = 'Message'

    search_fields = (
        'original_statement',
        'message__message', )
    list_filter = (
        # StatementWithoutMethodFilter,
        'branch', 
        'severity_level',
        # 'is_in_comment',
        'is_in_test',
        'message_length',
        'message_words_count',
        'count_variables',
        'conditional_statements_number',
        'looping_statements_number',
        'is_in_continue_statement',
        'is_in_break_statement',
        'catch_blocks_statements_number',
        'uses_string_concatenation',
    )
    list_display = (
        'severity_level',
        'original_statement',
        'branch',
        'display_message',
        'message_length',
        'count_variables',
        'line_number', 
        'is_in_comment',
        'is_in_test',
        'message_words_count',
        'conditional_statements_number',
        'looping_statements_number',
        'is_in_continue_statement',
        'is_in_break_statement',
        'catch_blocks_statements_number',
        'uses_string_concatenation',
    )
    exclude = ('code_snippet', )
    change_form_template = 'statement_change_form.htm'
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False


class StatementInline(admin.TabularInline):
    list_per_page = 10
    model = Statement
    def display_statement(self, obj):
        url = reverse(
                'admin:core_statement_change', 
                kwargs={'object_id': obj.pk, })
        return mark_safe(f'<a href="{url}" target="_blank">{obj.original_statement}</a>')
    display_statement.allow_tags = True
    display_statement.short_description = 'Statement'
    fields = (
        'display_statement',
        'severity_level',
        'branch',
        'message', 
        'file', 
        'line_number',)
    readonly_fields = (
        'display_statement',
        'severity_level',
        'branch',
        'message', 
        'file', )


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_per_page = 10
    search_fields = ('name', )
    list_filter = (
        'system_number',
        'branch_number',
        'log_statement_number', )
    list_display = (
        'name',
        'system_number',
        'branch_number',
        'log_statement_number', )
    inlines = (StatementInline, )
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False



@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_per_page = 10
    search_fields = (
        'name', )
    list_filter = (
        'branch',
        # 'cyclomatic_complexity',
        # 'parameters_count',
        # 'nloc',
        'severity_level_number',
        'log_statement_number', )
    list_display = (
        'branch',
        'name',
        'cyclomatic_complexity',
        'parameters_count',
        'nloc',
        'severity_level_number',
        'log_statement_number',  )
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False        


@admin.register(SeverityLevel)
class SeverityLevelAdmin(admin.ModelAdmin):
    list_per_page = 10
    inlines = (StatementInline, )
    list_display = (
        'name',
        'severity', )
    # def has_change_permission(self, request, obj=None):
    #     return False
    # def has_add_permission(self, request, obj=None):
    #     return False


@admin.action(description='Create manual message classification')
def create_manual_message_classification(modeladmin, request, messages_queryset):
    number = 0
    for message_obj in messages_queryset:
        message_obj.create_manual_message_classification()
        number += 1
        if number % 50 == 0: print(f'{number}/{len(messages_queryset)} variables processed... ', end='\r')


@admin.action(description='Counter variables')
def counter_variables(modeladmin, request, messages_queryset):
    number = 0
    total = len(messages_queryset)
    print(f'Processing {total} variables')
    update_list = []
    for message_obj in messages_queryset:
        message_obj.counter_variables()
        number += 1
        if number % 50 == 0: print(f'{number}/{total} variables processed... ', end='\r')


class SystemFilterInMessage(SimpleListFilter):
    title = 'Systems'
    parameter_name = 'system_filter'

    def lookups(self, request, model_admin):
        options = []
        systems = System.objects.order_by('name')
        for system in systems:
            options.append(tuple([system.id, system.name]))
        return options

    def queryset(self, request, queryset):
        if self.value():
            statements = Statement.objects.filter(branch__system=int(self.value())).all()
            messages = [statement.message_id for statement in statements]
            return queryset.filter(id__in=messages)
        else:
            return queryset


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_per_page = 10
    search_fields = (
        'message',)
    list_filter = (
        SystemFilterInMessage,
        'file_number',
        'message_length',
        'count_variables',
        'log_statement_number',
        'severity_level_number',
        'branch_number', )
    list_display = (
        'message',
        'message_length',
        'count_variables',
        'system_number',
        'branch_number',
        'file_number',
        'log_statement_number',
        'severity_level_number', )
    inlines = (StatementInline, )
    actions = (create_manual_message_classification, counter_variables)
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(BranchComparison)
class BranchComparisonAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_per_page = 10
    list_filter = (
        'branch_1',
        'branch_2', )
    list_display = (
        'branch_1',
        'branch_2', )
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(BranchFileComparison)
class BranchFileComparisonAdmin(admin.ModelAdmin):
    change_form_template = 'branchfilecomparison_change_form.htm'
    list_per_page = 10
    list_filter = (
        'file',
        'branch_1',
        'branch_2',
        'severity_level_1',
        'severity_level_2',
        'changed_severity_level',
        'changed_variables',
        'changed_messages',
        'file_exists_in_both_branches',
        'category', )
    list_display = (
        'branch_1',
        'branch_2',
        'statement_1',
        'statement_2',
        'category',
    )
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False
