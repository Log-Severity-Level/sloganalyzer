WITH branch_message_counter AS (
    SELECT DISTINCT sd.branch_id,
           sd.message_id, COUNT(id) AS quantity
      FROM public.core_statement sd
     GROUP BY sd.branch_id, sd.message_id )

SELECT  c.id,
        s.name AS system_name,
		b1.id AS branch_1_id,
		b2.id AS branch_2_id,
		CONCAT(s.name, '/', b1.name) AS  branch_name_1,
		CONCAT(s.name, '/', b2.name) AS  branch_name_2,
		f.id AS file_id,
		f.name AS filename,
		l1.name AS severity_level_1,
		l2.name AS severity_level_2,
		l1.severity AS severity_level_severity_1,
		l2.severity AS severity_level_severity_2,
		s1.id AS statement_1_id,
		s2.id AS statement_2_id,
           REPLACE(
               CONCAT(
                   to_char(b1.version, '0'), '.',
                   to_char(b1.version2, '00'), '.',
                   to_char(b1.version3, '00')), ' ', '') AS release_1,
           REPLACE(
               CONCAT(
                   to_char(b2.version, '0'), '.',
                   to_char(b2.version2, '00'), '.',
                   to_char(b2.version3, '00')), ' ', '') AS release_2,
           REPLACE(
               CONCAT(
                   to_char(b1.version, '0'), '.',
                   to_char(b1.version2, '00'), '.',
                   to_char(b1.version3, '00'), '->',
                   to_char(b2.version, '0'), '.',
                   to_char(b2.version2, '00'), '.',
                   to_char(b2.version3, '00')), ' ', '') AS releases,
		b1.version AS version_1,
		b2.version AS version_2,
		b1.version2 AS version2_1,
		b2.version2 AS version2_2,
		b1.version3 AS version3_1,
		b2.version3 AS version3_2,
		s1.message_words_count AS message_words_count_1,
		s2.message_words_count AS message_words_count_2,
		s1.count_variables AS count_variables_1,
		s2.count_variables AS count_variables_2,
		CASE
			WHEN s1.message_without_variables != s2.message_without_variables THEN 'Yes'
		ELSE 'No' END AS changed_semantic_content,
		CASE
			WHEN s1.message_without_variables != s2.message_without_variables THEN 'Changed content'
			WHEN (s1.message_without_variables = '' AND s2.message_without_variables != '') THEN 'Included content'
			WHEN (s1.message_without_variables != '' AND s2.message_without_variables = '') THEN 'Removed content'
		ELSE 'Unchanged' END AS changed_semantic_content_type,
		CASE
			WHEN c.severity_level_1_id != c.severity_level_2_id THEN 'Yes'
		ELSE 'No' END AS changed_severity_level,
		CASE
			WHEN l1.severity > l2.severity THEN 'Severity Decreased'
			WHEN l1.severity < l2.severity THEN 'Severity Increased'
		ELSE 'Unchanged' END AS changed_severity_level_type,
		CASE
			WHEN m1.message != m2.message THEN 'Yes'
		ELSE 'No' END AS changed_messages_length,
		CASE
			WHEN m1.message_length > m2.message_length THEN 'Decreased message length'
			WHEN m1.message_length < m2.message_length THEN 'Increased message length'
		ELSE 'Unchanged' END AS changed_messages_length_type,
		CASE
			WHEN TRIM(REGEXP_REPLACE(REGEXP_REPLACE(s1.message_with_variables, '\".*?\"', '', 'g'), '[+,\s]+', ' ', 'g')) !=
			     TRIM(REGEXP_REPLACE(REGEXP_REPLACE(s2.message_with_variables, '\".*?\"', '', 'g'), '[+,\s]+', ' ', 'g')) THEN 'Yes'
		ELSE 'No' END AS changed_variables,
		CASE
			WHEN s1.count_variables > s2.count_variables THEN 'Decreased number of variables'
			WHEN s1.count_variables < s2.count_variables THEN 'Increased number of variables'
		ELSE 'Unchanged' END AS changed_variables_type,

        s1.line_number_final - s1.line_number + 1 AS quant_lines_1,
        s2.line_number_final - s2.line_number + 1 AS quant_lines_2,

        CASE WHEN s1.line_number_final - s1.line_number + 1 > s2.line_number_final - s2.line_number + 1 THEN 'Decreased'
            WHEN s1.line_number_final - s1.line_number + 1 < s2.line_number_final - s2.line_number + 1 THEN 'Increased'
            ELSE 'Unchanged' END AS changed_quant_lines,

        CASE WHEN s1.catch_blocks_statements_number > 0 THEN 'Yes' ELSE 'No' END AS is_in_catch_blocks_statements_1,
        CASE WHEN s2.catch_blocks_statements_number > 0 THEN 'Yes' ELSE 'No' END AS is_in_catch_blocks_statements_2,
        CASE WHEN s1.conditional_statements_number > 0 THEN 'Yes' ELSE 'No' END AS is_in_conditional_statements_1,
        CASE WHEN s2.conditional_statements_number > 0 THEN 'Yes' ELSE 'No' END AS is_in_conditional_statements_2,
        CASE WHEN s1.is_in_break_statement = TRUE THEN 'Yes' ELSE 'No' END AS is_in_break_statement_1,
        CASE WHEN s2.is_in_break_statement = TRUE THEN 'Yes' ELSE 'No' END AS is_in_break_statement_2,
        CASE WHEN s1.is_in_continue_statement = TRUE THEN 'Yes' ELSE 'No' END AS is_in_continue_statement_1,
        CASE WHEN s2.is_in_continue_statement = TRUE THEN 'Yes' ELSE 'No' END AS is_in_continue_statement_2,
        CASE WHEN s1.looping_statements_number > 0 THEN 'Yes' ELSE 'No' END AS is_in_looping_statements_1,
        CASE WHEN s2.looping_statements_number > 0 THEN 'Yes' ELSE 'No' END AS is_in_looping_statements_2,
        CASE WHEN s1.uses_string_concatenation = TRUE THEN 'Yes' ELSE 'No' END AS uses_string_concatenation_1,
        CASE WHEN s2.uses_string_concatenation = TRUE THEN 'Yes' ELSE 'No' END AS uses_string_concatenation_2,

        s1.catch_blocks_statements_number AS catch_blocks_statements_number_1,
        s2.catch_blocks_statements_number AS catch_blocks_statements_number_2,

        CASE WHEN s1.catch_blocks_statements_number > s2.catch_blocks_statements_number THEN 'Decreased'
            WHEN s1.catch_blocks_statements_number < s2.catch_blocks_statements_number THEN 'Increased'
            ELSE 'Unchanged' END AS uses_string_concatenation_changed,

        s1.conditional_statements_number AS conditional_statements_number_1,
        s2.conditional_statements_number AS conditional_statements_number_2,

        CASE WHEN s1.conditional_statements_number > s2.conditional_statements_number THEN 'Decreased'
            WHEN s1.conditional_statements_number < s2.conditional_statements_number THEN 'Increased'
            ELSE 'Unchanged' END AS conditional_statements_number_changed,

        s1.looping_statements_number AS looping_statements_number_1,
        s2.looping_statements_number AS looping_statements_number_2,

        CASE WHEN s1.looping_statements_number > s2.looping_statements_number THEN 'Decreased'
            WHEN s1.looping_statements_number < s2.looping_statements_number THEN 'Increased'
            ELSE 'Unchanged' END AS looping_statements_number_changed,

        me1.parameters_count AS method_parameters_count_1,
        me2.parameters_count AS method_parameters_count_2,

        CASE WHEN me1.parameters_count > me2.parameters_count THEN 'Decreased'
            WHEN me1.parameters_count < me2.parameters_count THEN 'Increased'
            ELSE 'Unchanged' END AS method_parameters_count_changed,

        me1.cyclomatic_complexity AS method_cyclomatic_complexity_1,
        me2.cyclomatic_complexity AS method_cyclomatic_complexity_2,

        CASE WHEN me1.cyclomatic_complexity > me2.cyclomatic_complexity THEN 'Decreased'
            WHEN me1.cyclomatic_complexity < me2.cyclomatic_complexity THEN 'Increased'
            ELSE 'Unchanged' END AS method_cyclomatic_complexity_changed,

        me1.nloc AS method_nloc_1,
        me2.nloc AS method_nloc_2,

        CASE WHEN me1.nloc > me2.nloc THEN 'Decreased'
            WHEN me1.nloc < me2.nloc THEN 'Increased'
            ELSE 'Unchanged' END AS method_nloc_changed,

        CASE
            WHEN bmc1.quantity > 1 THEN 'Yes'
            ELSE 'No' END AS message_1_duplicated,
        CASE
            WHEN bmc2.quantity > 1 THEN 'Yes'
            ELSE 'No' END AS message_2_duplicated,
        CASE
            WHEN bmc1.quantity > 1 OR bmc2.quantity > 1 THEN 'Yes'
            ELSE 'No' END AS message_duplicated,
        CASE
			WHEN s1.message_without_variables = '' THEN 'Yes'
			ELSE 'No' END AS message_1_blank,
        CASE
			WHEN s2.message_without_variables = '' THEN 'Yes'
			ELSE 'No' END AS message_2_blank,
        CASE
			WHEN s1.message_without_variables = '' OR s2.message_without_variables = '' THEN 'Yes'
			ELSE 'No' END AS message_blank,
       CASE
            WHEN c.file_exists_in_both_branches = 1 THEN 'Yes'
            ELSE 'No' END AS file_exists_in_both_branches,
       CASE
            WHEN c.category = 1 THEN 'Added'
            WHEN c.category = 2 THEN 'Updated'
            WHEN c.category = 3 THEN 'Deleted'
            ELSE 'Unchanged' END AS category,
        l1.id AS severity_level_1_id,
        l2.id AS severity_level_2_id,
        m1.id AS message_1_id,
        m2.id AS message_2_id,
        m1.message AS message_1,
        m2.message AS message_2,
        s1.original_statement AS statement_1,
        s2.original_statement AS statement_2,
        s1.message_without_variables AS message_without_variables_1,
        s2.message_without_variables AS message_without_variables_2,
        s1.line_number AS line_number_initial_1,
        s2.line_number AS line_number_initial_2,
 		c.cosine_similarity_statements,
 		c.cosine_similarity_messages,
 		c.cosine_similarity_variables
    INTO stage.changes
	FROM public.core_branchfilecomparison c
	JOIN public.core_branch b1 ON b1.id = c.branch_1_id
	JOIN public.core_system s ON s.id = b1.system_id
	JOIN public.core_branch b2 ON b2.id = c.branch_2_id
	JOIN public.core_file f ON f.id = c.file_id
	LEFT JOIN public.core_severitylevel l1 ON l1.id = c.severity_level_1_id
	LEFT JOIN public.core_severitylevel l2 ON l2.id = c.severity_level_2_id
	LEFT JOIN public.core_message m1 ON m1.id = c.message_1_id
	LEFT JOIN public.core_message m2 ON m2.id = c.message_2_id
	LEFT JOIN public.core_statement s1 ON s1.id = c.statement_1_id
	LEFT JOIN public.core_statement s2 ON s2.id = c.statement_2_id
	LEFT JOIN public.core_methodstatement ms1 ON ms1.statement_id = c.statement_1_id
	LEFT JOIN public.core_method me1 ON me1.id = ms1.method_id
	LEFT JOIN public.core_methodstatement ms2 ON ms2.statement_id = c.statement_2_id
	LEFT JOIN public.core_method me2 ON me2.id = ms2.method_id
    LEFT JOIN branch_message_counter bmc1 ON bmc1.message_id = c.message_1_id
                                            AND bmc1.branch_id = c.branch_1_id
    LEFT JOIN branch_message_counter bmc2 ON bmc2.message_id = c.message_2_id
                                            AND bmc2.branch_id = c.branch_2_id;
