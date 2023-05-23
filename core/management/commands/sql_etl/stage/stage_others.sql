SELECT DISTINCT
    branch_name, message_without_variables,
    COUNT(id) AS quantity,
    CASE
        WHEN COUNT(id) = 1 THEN 'Single'
        ELSE 'Duplicated' END AS is_duplicated
    INTO stage.duplicated_messages
    FROM stage.statements
    GROUP BY branch_name, message_without_variables
    ORDER BY COUNT(id) DESC;

---------------

CREATE OR REPLACE VIEW stage.vw_overview_changements AS
SELECT 'Changed severity levels' AS action,
(SELECT COUNT(id) FROM stage.changes WHERE changed_severity_level ILIKE 'YES%' AND category='Updated') AS quantity
UNION
SELECT 'Changed variables' AS action,
(SELECT COUNT(id) FROM stage.changes WHERE changed_variables ILIKE 'YES%' AND category='Updated') AS quantity
UNION
SELECT 'Changed messages' AS action,
(SELECT COUNT(id) FROM stage.changes WHERE changed_semantic_content ILIKE 'YES%' AND category='Updated') AS quantity;

CREATE OR REPLACE VIEW stage.relationship_overview AS
SELECT DISTINCT
substring(changed_semantic_content, 1, 1) AS changed_messages,
substring(changed_variables, 1, 1) AS changed_variables,
substring(changed_severity_level, 1, 1) AS changed_severity_level,
COUNT(id) AS quantity,
(SELECT COUNT(id) FROM stage.changes WHERE category='Updated') AS total
FROM stage.changes
WHERE category='Updated'
GROUP BY substring(changed_severity_level, 1, 1), substring(changed_semantic_content, 1, 1), substring(changed_variables, 1, 1)
ORDER BY substring(changed_semantic_content, 1, 1), substring(changed_variables, 1, 1), substring(changed_severity_level, 1, 1);