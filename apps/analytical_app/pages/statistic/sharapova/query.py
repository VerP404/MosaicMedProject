sql_query_sharapova = """
WITH sharapova AS (
    SELECT 
        ob.name AS "Подразделение",
        SUM(CASE WHEN dlo.main_diagnosis LIKE 'I%' THEN 1 ELSE 0 END) AS "БСК",
        SUM(CASE WHEN dlo.main_diagnosis LIKE ANY (ARRAY ['I%', 'C%', 'J44%']) THEN 0 ELSE 1 END) AS "Другая",
        SUM(CASE WHEN dlo.main_diagnosis LIKE 'C%' THEN 1 ELSE 0 END) AS "Онко",
        SUM(CASE WHEN dlo.main_diagnosis LIKE 'J44%' THEN 1 ELSE 0 END) AS "Хобл",
        SUM(CASE WHEN dlo.main_diagnosis LIKE ANY (ARRAY ['E10%', 'E11%']) THEN 1 ELSE 0 END) AS "СД",
        COUNT(*) AS "Итого",
        CASE WHEN GROUPING(ob.name) = 1 THEN 1 ELSE 0 END AS is_total
    FROM data_loader_omsdata dlo
    JOIN personnel_doctorrecord pd ON SUBSTRING(dlo.doctor, 1, POSITION(' ' IN dlo.doctor) - 1) = pd.doctor_code
    JOIN organization_department od ON pd.department_id = od.id
    JOIN organization_building ob ON od.building_id = ob.id
    WHERE dlo.goal = '3' 
      AND to_date(dlo.initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') 
      AND to_date(:end_date, 'DD-MM-YYYY')
    GROUP BY ROLLUP(ob.name)
    ORDER BY is_total, ob.name
) 
SELECT "Подразделение", "БСК", "Другая", "Онко", "Хобл", "СД", "Итого" 
FROM sharapova;
"""


sql_query_sharapova_doctors = """
WITH sharapova_doctors AS (
    SELECT 
        ob.name AS "Подразделение",
        od.name AS "Отделение",
        COALESCE(specialty.description, dlo.specialty, '') AS "Специальность",
        dlo.doctor AS "Врач",
        SUM(CASE WHEN dlo.main_diagnosis LIKE 'I%' THEN 1 ELSE 0 END) AS "БСК",
        SUM(CASE WHEN dlo.main_diagnosis LIKE ANY (ARRAY ['I%', 'C%', 'J44%']) THEN 0 ELSE 1 END) AS "Другая",
        SUM(CASE WHEN dlo.main_diagnosis LIKE 'C%' THEN 1 ELSE 0 END) AS "Онко",
        SUM(CASE WHEN dlo.main_diagnosis LIKE 'J44%' THEN 1 ELSE 0 END) AS "Хобл",
        SUM(CASE WHEN dlo.main_diagnosis LIKE ANY (ARRAY ['E10%', 'E11%']) THEN 1 ELSE 0 END) AS "СД",
        COUNT(*) AS "Итого"
    FROM data_loader_omsdata dlo
    JOIN personnel_doctorrecord pd ON SUBSTRING(dlo.doctor, 1, POSITION(' ' IN dlo.doctor) - 1) = pd.doctor_code
    JOIN organization_department od ON pd.department_id = od.id
    JOIN organization_building ob ON od.building_id = ob.id
    LEFT JOIN personnel_specialty specialty ON specialty.id = pd.specialty_id
    WHERE dlo.goal = '3' 
      AND to_date(dlo.initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') 
      AND to_date(:end_date, 'DD-MM-YYYY')
    GROUP BY ob.name, od.name, COALESCE(specialty.description, dlo.specialty, ''), dlo.doctor
)
SELECT 
    "Подразделение",
    "Отделение",
    "Специальность",
    "Врач",
    "БСК",
    "Другая",
    "Онко",
    "Хобл",
    "СД",
    "Итого"
FROM sharapova_doctors
ORDER BY "Подразделение", "Отделение", "Специальность", "Врач";
"""
