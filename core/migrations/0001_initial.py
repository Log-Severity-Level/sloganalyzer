# Generated by Django 3.2.4 on 2023-05-19 00:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='Name')),
                ('std_version', models.CharField(blank=True, max_length=50, null=True, verbose_name='Version (Standardized)')),
                ('version', models.IntegerField(default=0, verbose_name='Version Level 1')),
                ('version2', models.IntegerField(default=0, verbose_name='Version Level 2')),
                ('version3', models.IntegerField(default=0, verbose_name='Version Level 3')),
                ('version4', models.IntegerField(default=0, verbose_name='Version Level 4')),
                ('tagged_date', models.DateTimeField(blank=True, null=True, verbose_name='Tagged Date')),
                ('log_statement_number', models.IntegerField(blank=True, null=True, verbose_name='Log Statement Number')),
                ('file_number', models.IntegerField(blank=True, null=True, verbose_name='File Number')),
                ('method_number', models.IntegerField(blank=True, null=True, verbose_name='Method Number')),
                ('nloc', models.IntegerField(blank=True, null=True, verbose_name='NLOC')),
                ('cyclomatic_complexity', models.IntegerField(blank=True, null=True, verbose_name='Cyclomatic Complexity')),
                ('cloned_date', models.DateTimeField(blank=True, null=True)),
                ('head', models.CharField(blank=True, max_length=50, null=True, verbose_name='Head')),
            ],
            options={
                'ordering': ['system', '-std_version'],
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, unique=True, verbose_name='Name')),
                ('system_number', models.IntegerField(default=-1, verbose_name='System Number')),
                ('branch_number', models.IntegerField(default=-1, verbose_name='Branch Number')),
                ('log_statement_number', models.IntegerField(default=-1, verbose_name='Log Statement Number')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(verbose_name='Message')),
                ('message_length', models.IntegerField(verbose_name='Message Length without variables')),
                ('count_variables', models.IntegerField(verbose_name='Count variables')),
                ('file_number', models.IntegerField(default=-1, verbose_name='File Number')),
                ('log_statement_number', models.IntegerField(default=-1, verbose_name='Log Statement Number')),
                ('severity_level_number', models.IntegerField(default=-1, verbose_name='Severity Level Number')),
                ('branch_number', models.IntegerField(default=-1, verbose_name='Branch Number')),
                ('system_number', models.IntegerField(default=-1, verbose_name='System Number')),
            ],
        ),
        migrations.CreateModel(
            name='Method',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(verbose_name='Name')),
                ('cyclomatic_complexity', models.IntegerField(verbose_name='Cyclomatic Complexity')),
                ('nloc', models.IntegerField(verbose_name='NLOC (Lines of code without comments)')),
                ('token_count', models.IntegerField(verbose_name='Token Count')),
                ('long_name', models.TextField(verbose_name='Long Name')),
                ('start_line', models.IntegerField(verbose_name='Start Line')),
                ('end_line', models.IntegerField(verbose_name='End line')),
                ('full_parameters_json', models.TextField(verbose_name='Full Parameters (JSON)')),
                ('filename', models.TextField(verbose_name='File Name')),
                ('relative_filename', models.TextField(verbose_name='File Name (Reference)')),
                ('top_nesting_level', models.IntegerField(verbose_name='Top Nesting Level')),
                ('fan_in', models.IntegerField(verbose_name='Fan In')),
                ('fan_out', models.IntegerField(verbose_name='Fan Out')),
                ('general_fan_out', models.IntegerField(verbose_name='General Fan Out')),
                ('parameters_count', models.IntegerField(verbose_name='Parameters Count')),
                ('code', models.TextField(blank=True, null=True, verbose_name='Code')),
                ('code_raw', models.TextField(blank=True, null=True, verbose_name='Code (raw)')),
                ('severity_level_number', models.IntegerField(default=-1, verbose_name='Severity Level Number')),
                ('conditional_statements_number', models.IntegerField(default=-1, verbose_name='Conditional Statement sNumber')),
                ('catch_blocks_statements_number', models.IntegerField(default=-1, verbose_name='Catch/blocks Statements Number')),
                ('looping_statements_number', models.IntegerField(default=-1, verbose_name='Looping Statements Number')),
                ('continue_statements_number', models.IntegerField(default=-1, verbose_name='continue Statements Number')),
                ('break_statements_number', models.IntegerField(default=-1, verbose_name='Beeak Statements Number')),
                ('log_statement_number', models.IntegerField(default=-1, verbose_name='Log Statements Number')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='method_branch', to='core.branch', verbose_name='Branch')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='method_file', to='core.file', verbose_name='File')),
            ],
        ),
        migrations.CreateModel(
            name='SeverityLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, unique=True, verbose_name='Name')),
                ('severity', models.IntegerField(default=0, verbose_name='Severity')),
            ],
        ),
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, unique=True, verbose_name='Name')),
                ('github_url', models.CharField(max_length=500, verbose_name='GitHub URL')),
                ('cloned_date', models.DateTimeField(blank=True, null=True)),
                ('head', models.CharField(blank=True, max_length=50, null=True, verbose_name='Head')),
                ('version_regex', models.CharField(default='^(rel\\/release-|release-)(?P<v1>\\d+)\\.(?P<v2>\\d+)\\.(?P<v3>\\d+)$', max_length=100, verbose_name='Version detection regex')),
            ],
        ),
        migrations.CreateModel(
            name='TimeTracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pipeline', models.CharField(max_length=50, verbose_name='Pipeline')),
                ('system', models.CharField(max_length=50, null=True, verbose_name='System')),
                ('branch', models.CharField(max_length=50, null=True, verbose_name='Branch')),
                ('delta_time', models.DecimalField(decimal_places=4, max_digits=15, verbose_name='Time (seconds)')),
            ],
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_number', models.IntegerField(verbose_name='Line Number (initial)')),
                ('line_number_final', models.IntegerField(verbose_name='Line Number (final)')),
                ('count_variables', models.IntegerField(verbose_name='Count variables')),
                ('code_snippet', models.TextField(blank=True, null=True, verbose_name='Code Snippet')),
                ('span_initial', models.IntegerField(verbose_name='Span initial')),
                ('span_final', models.IntegerField(verbose_name='Span final')),
                ('is_in_comment', models.BooleanField(default=True, verbose_name='Is in comment?')),
                ('is_in_test', models.BooleanField(default=True, verbose_name='Is in tests?')),
                ('conditional_statements_number', models.IntegerField(default=-1, verbose_name='Conditional statements number')),
                ('looping_statements_number', models.IntegerField(default=-1, verbose_name='Looping statements number')),
                ('is_in_continue_statement', models.BooleanField(default=False, verbose_name='Is in continue statement?')),
                ('is_in_break_statement', models.BooleanField(default=False, verbose_name='Is in break statement?')),
                ('catch_blocks_statements_number', models.IntegerField(default=-1, verbose_name='Catch blocks statements number')),
                ('original_statement', models.TextField(verbose_name='Statement')),
                ('variables', models.TextField(verbose_name='Variables')),
                ('message_with_variables', models.TextField(verbose_name='Message with variables')),
                ('message_without_variables', models.TextField(verbose_name='Message without variables')),
                ('line_text', models.TextField(verbose_name='Line text')),
                ('message_words_count', models.IntegerField(default=-1, verbose_name='Message words count')),
                ('uses_string_concatenation', models.BooleanField(default=False, verbose_name='Uses string concatenation?')),
                ('message_length', models.IntegerField(verbose_name='Message Length without variables')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statement_branch', to='core.branch', verbose_name='Branch')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statement_file', to='core.file', verbose_name='File')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statement_message', to='core.message', verbose_name='Message')),
                ('severity_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statement_severity_level', to='core.severitylevel', verbose_name='SeverityLevel')),
            ],
            options={
                'unique_together': {('branch', 'file', 'line_number')},
            },
        ),
        migrations.CreateModel(
            name='MethodStatement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='methodstatement_method', to='core.method', verbose_name='Method')),
                ('statement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='methodstatement_statement', to='core.statement', verbose_name='Statement')),
            ],
        ),
        migrations.CreateModel(
            name='BranchFileComparison',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sentence_1', models.TextField(null=True)),
                ('sentence_2', models.TextField(null=True)),
                ('variables_1', models.TextField(null=True)),
                ('variables_2', models.TextField(null=True)),
                ('variable_count_1', models.IntegerField(null=True, verbose_name='Variable count 1')),
                ('variable_count_2', models.IntegerField(null=True, verbose_name='Variable count 2')),
                ('cosine_similarity', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Cosine of similarity')),
                ('cosine_similarity_messages', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Cosine of similarity between messages')),
                ('cosine_similarity_statements', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Cosine of similarity between statements')),
                ('cosine_similarity_variables', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Cosine of similarity between variables names')),
                ('changed_severity_level', models.IntegerField(choices=[(0, 'No'), (1, 'Yes')], null=True, verbose_name='Changed severity level')),
                ('changed_file', models.IntegerField(choices=[(0, 'No'), (1, 'Yes')], null=True, verbose_name='Changed file')),
                ('changed_variables', models.IntegerField(choices=[(0, 'No'), (1, 'Yes')], null=True, verbose_name='Changed variables')),
                ('changed_messages', models.IntegerField(choices=[(0, 'No'), (1, 'Yes')], null=True, verbose_name='Changed message')),
                ('file_exists_in_both_branches', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')], verbose_name='File exists in both branches')),
                ('category', models.IntegerField(choices=[(1, 'Added'), (2, 'Updated'), (3, 'Deleted'), (4, 'No updated')], verbose_name='Category')),
                ('branch_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_branch_1', to='core.branch', verbose_name='Branch 1')),
                ('branch_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_branch_2', to='core.branch', verbose_name='Branch 2')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_file', to='core.file', verbose_name='File')),
                ('message_1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_severity_message_1', to='core.message', verbose_name='Message 1')),
                ('message_2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_severity_message_2', to='core.message', verbose_name='Message 2')),
                ('severity_level_1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_severity_level_1', to='core.severitylevel', verbose_name='Severity Level 1')),
                ('severity_level_2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_severity_level_2', to='core.severitylevel', verbose_name='Severity Level 2')),
                ('statement_1', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_statement_1', to='core.statement', verbose_name='Statement 1')),
                ('statement_2', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branchfilecomparison_statement_2', to='core.statement', verbose_name='Statement 2')),
            ],
        ),
        migrations.AddField(
            model_name='branch',
            name='system',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branch_system', to='core.system', verbose_name='System'),
        ),
        migrations.CreateModel(
            name='BranchFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nloc', models.IntegerField(verbose_name='NLOC (Number lines of code without comments)')),
                ('nlog_without_log_statements', models.IntegerField(verbose_name='NLOG (Number lines of log code without_log_statements)')),
                ('nlog', models.IntegerField(verbose_name='NLOG (Number lines of log code)')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branchfile_branch', to='core.branch', verbose_name='Branch')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branchfile_file', to='core.file', verbose_name='File')),
            ],
            options={
                'unique_together': {('branch', 'file')},
            },
        ),
        migrations.CreateModel(
            name='BranchComparison',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branchcomparison_branch1', to='core.branch', verbose_name='Branch1')),
                ('branch_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branchcomparison_branch2', to='core.branch', verbose_name='Branch2')),
            ],
            options={
                'unique_together': {('branch_1', 'branch_2')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='branch',
            unique_together={('system', 'version', 'version2', 'version3', 'version4')},
        ),
    ]
