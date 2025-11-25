sql_query_form131 = """
SELECT DISTINCT ON (t.talon)
    t.talon AS Талон,
    t.goal AS Цель,
    t.patient AS Пациент,
    t.birth_date AS "Дата рождения",
    (CAST(t.report_year AS INTEGER) - CAST(SUBSTRING(t.birth_date FROM '[0-9]{4}$') AS INTEGER)) AS Возраст,
    t.gender AS Пол,
    t.enp AS ЕНП,
    t.treatment_start AS "Дата начала лечения",
    t.treatment_end AS "Дата окончания лечения",
    t.main_diagnosis AS Диагноз,
    t.department AS Корпус,
    t.doctor AS Врач,
    t.doctor_profile AS "Специальность",
    d.health_group AS "Группа здоровья"
FROM load_data_talons t
LEFT JOIN load_data_detailed_medical_examination d ON t.talon = d.talon_number
WHERE t.report_year = :selected_year
AND t.goal in ('ДВ4', 'ДВ2', 'ОПВ', 'УД1', 'УД2', 'ДР1', 'ДР2', 'ПН1', 'ДС1', 'ДС2')
ORDER BY t.talon, d.health_group;
"""

