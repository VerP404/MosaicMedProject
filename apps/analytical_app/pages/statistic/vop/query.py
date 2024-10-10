sql_query_vop = """
SELECT DISTINCT
       department || ' ' || split_part(doctor, ' ', 2) || ' ' || left(split_part(doctor, ' ', 3), 1) || '.' || left(split_part(doctor, ' ', 4), 1) || '.' AS "Врач",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['I%', 'E%', 'K%', 'N%', 'J%', 'D5%', 'D6%', 'D7%', 'D8%'])
               AND mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) +  CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Внутренние болезни",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['I%', 'E%', 'K%', 'N%', 'J%', 'D5%', 'D6%', 'D7%', 'D8%'])
               AND mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Внутренние болезни в МО",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['I%', 'E%', 'K%', 'N%', 'J%', 'D5%', 'D6%', 'D7%', 'D8%'])
               AND home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Внутренние болезни на Дому",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['G%', 'F%', 'H8%'])
               AND mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) + CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Неврология",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['G%', 'F%', 'H8%'])
               AND mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Неврология в МО",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['G%', 'F%', 'H8%'])
               AND home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Неврология на Дому",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['H6%', 'H7%', 'H9%'])
               AND mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) + CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Отоларингология",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['H6%', 'H7%', 'H9%'])
               AND mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Отоларингология в МО",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['H6%', 'H7%', 'H9%'])
               AND home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Отоларингология на Дому",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['S05%', 'H0%', 'H1%', 'H2%', 'H3%', 'H4%', 'H5%'])
               AND mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) + CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Офтальмология",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['S05%', 'H0%', 'H1%', 'H2%', 'H3%', 'H4%', 'H5%'])
               AND mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Офтальмология в МО",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['S05%', 'H0%', 'H1%', 'H2%', 'H3%', 'H4%', 'H5%'])
               AND home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Офтальмология на Дому",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['C%', 'D0%', 'D1%', 'D2%', 'D3%', 'D4%', 'S01%', 'S02%', 'S03%', 'S04%', 'S06%', 'S07%', 'S08%', 'S09%', 'S1%', 'S2%', 'S3%', 'S4%', 'S5%', 'S6%', 'S7%', 'S8%', 'S9%', 'M%'])
               AND mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) + CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Хирургия",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['C%', 'D0%', 'D1%', 'D2%', 'D3%', 'D4%', 'S01%', 'S02%', 'S03%', 'S04%', 'S06%', 'S07%', 'S08%', 'S09%', 'S1%', 'S2%', 'S3%', 'S4%', 'S5%', 'S6%', 'S7%', 'S8%', 'S9%', 'M%'])
               AND mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Хирургия в МО",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['C%', 'D0%', 'D1%', 'D2%', 'D3%', 'D4%', 'S01%', 'S02%', 'S03%', 'S04%', 'S06%', 'S07%', 'S08%', 'S09%', 'S1%', 'S2%', 'S3%', 'S4%', 'S5%', 'S6%', 'S7%', 'S8%', 'S9%', 'M%'])
               AND home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Хирургия на Дому",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['O%'])
               AND mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) + CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Ак. и ген.",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['O%'])
               AND mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Ак. и ген. в МО",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['O%'])
               AND home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Ак. и ген. на Дому",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['P%', 'Q%'])
               AND mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) + CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Педиатрия",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['P%', 'Q%'])
               AND mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Педиатрия в МО",
       SUM(CASE
               WHEN main_diagnosis LIKE ANY(array['P%', 'Q%'])
               AND home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Педиатрия на Дому",
       SUM(CASE
               WHEN mo_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8))
               ELSE 0
           END) AS "Итого в МО",
       SUM(CASE
               WHEN home_visits ~ '^[0-9]+$'
               THEN CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Итого на Дому",
       SUM(CASE
               WHEN mo_visits ~ '^[0-9]+$' AND home_visits ~ '^[0-9]+$'
               THEN CAST(mo_visits AS numeric(8)) + CAST(home_visits AS numeric(8))
               ELSE 0
           END) AS "Всего"
FROM data_loader_omsdata
WHERE doctor_profile = '57 общей врачебной практике (семейной медицине)'
and to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
GROUP BY "Врач"
"""