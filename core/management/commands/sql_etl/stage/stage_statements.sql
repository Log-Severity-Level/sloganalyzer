WITH branch_message_counter AS (
    SELECT DISTINCT sd.branch_id,
           sd.message_id, COUNT(id) AS quantity
      FROM public.core_statement sd
     GROUP BY sd.branch_id, sd.message_id )

SELECT bv.id,
       bv.id AS statement_id,
       s.id AS system_id,
       s.name AS system_name,
       b.id as branch_id,
       CONCAT(s.name, '/', b.name) AS branch_name,
       REPLACE(
           CONCAT(
               to_char(b.version, '0'), '.',
               to_char(b.version2, '00'), '.',
               to_char(b.version3, '00')), ' ', '') AS release,
       b.version,
       b.version2,
       b.version3,
       sl.id AS severity_level_id,
       sl.name AS severity_level,
       sl.severity AS severity_level_severity,
       f.id AS filename_id,
       f.name AS filename,
	   me.id AS method_id,
	   me.name AS method_name,
       m.id AS message_id,
       m.message AS message,
	   bv.count_variables,
       CASE
           WHEN bv.count_variables = 0 THEN 'No'
           ELSE 'Yes' END AS have_variables,
       CASE
           WHEN bv.message_length = 0 THEN 'No'
           ELSE 'Yes' END AS have_message,
       CASE
           WHEN bv.message_without_variables = '' THEN 'No'
           ELSE 'Yes' END AS have_words_in_message,
       CASE
           WHEN bv.is_in_test = TRUE THEN 'Yes'
           ELSE 'No' END AS is_in_test,
	   bv.message_length,
	   bv.catch_blocks_statements_number,
       CASE
           WHEN bv.catch_blocks_statements_number = 0 THEN 'No'
           ELSE 'Yes' END AS is_in_catch_blocks_statements,
	   bv.conditional_statements_number,
       CASE
           WHEN bv.conditional_statements_number = 0 THEN 'No'
           ELSE 'Yes' END AS is_in_conditional_statements,
       CASE
           WHEN bv.is_in_break_statement = TRUE THEN 'Yes'
           ELSE 'No' END AS is_in_break_statement,
       CASE
           WHEN bv.is_in_continue_statement = TRUE THEN 'Yes'
           ELSE 'No' END AS is_in_continue_statement,
	   bv.message_without_variables,
	   bv.looping_statements_number,
       CASE
           WHEN bv.looping_statements_number = 0 THEN 'No'
           ELSE 'Yes'
           END AS is_in_looping_statements,
       CASE
           WHEN bv.uses_string_concatenation = TRUE THEN 'Yes'
           ELSE 'No'
           END AS uses_string_concatenation,
	   bv.message_words_count,
	   me.cyclomatic_complexity AS method_cyclomatic_complexity,
	   me.nloc AS method_nloc,
	   me.token_count AS method_token_count,
	   me.long_name AS method_long_name,
	   me.top_nesting_level AS method_top_nesting_level,
	   me.parameters_count AS method_parameters_count,
	   me.fan_in AS method_fan_in,
	   me.fan_out AS method_fan_out,
	   me.general_fan_out AS method_general_fan_out,
	   (bv.line_number_final - bv.line_number + 1) AS line_count,
	   bv.line_number AS line_initial,
	   bv.line_number_final AS line_final,
	   CASE
	       WHEN bmc.quantity > 1 THEN 'Yes'
           ELSE 'No' END AS duplicated,
	   CASE
	       WHEN bv.line_number_final = bv.line_number THEN 'Single line'
           ELSE 'Multiply lines' END AS log_lines
    INTO stage.statements
	FROM public.core_statement bv
    JOIN public.core_severitylevel sl ON sl.id = bv.severity_level_id
    JOIN public.core_file f ON f.id = bv.file_id
    JOIN public.core_message m ON m.id = bv.message_id
	LEFT JOIN public.core_methodstatement ms ON ms.statement_id = bv.id
    LEFT JOIN public.core_method me ON me.id = ms.method_id
    JOIN public.core_branch b ON b.id = bv.branch_id
    JOIN public.core_system s ON s.id = b.system_id
    JOIN branch_message_counter bmc ON bmc.message_id = bv.message_id AND bmc.branch_id = bv.branch_id
    ORDER BY s.name, filename, severity_level, b.name;
