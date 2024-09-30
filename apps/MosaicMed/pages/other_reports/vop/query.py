sql_query_vop = """
SELECT distinct "Подразделение" || ' ' || split_part("Врач", ' ', 2) || ' ' || left(split_part("Врач", ' ', 3), 1) ||
             '.' || left(split_part("Врач", ' ', 4), 1) || '.' AS "врач",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['I%', 'E%', 'K%', 'N%', 'J%', 'D5%', 'D6%', 'D7%', 'D8%']) THEN  CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Внутренние болезни",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['I%', 'E%', 'K%', 'N%', 'J%', 'D5%', 'D6%', 'D7%', 'D8%']) and CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Внутренние болезни в МО",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['I%', 'E%', 'K%', 'N%', 'J%', 'D5%', 'D6%', 'D7%', 'D8%']) and CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Внутренние болезни на Дому",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['G%', 'F%', 'H8%']) THEN CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Неврология",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['G%', 'F%', 'H8%']) and CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Неврология в МО",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['G%', 'F%', 'H8%']) and CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Неврология на Дому",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['H6%', 'H7%','H9%']) THEN CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Отоларингология",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['H6%', 'H7%','H9%']) and CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Отоларингология в МО",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['H6%', 'H7%','H9%']) and CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Отоларингология на Дому",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['S05%', 'H0%', 'H1%','H2%','H3%','H4%','H5%']) THEN CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Офтальмология",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['S05%', 'H0%', 'H1%','H2%','H3%','H4%','H5%']) and CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Офтальмология в МО",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['S05%', 'H0%', 'H1%','H2%','H3%','H4%','H5%']) and CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Офтальмология на Дому",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['C%', 'D0%', 'D1%', 'D2%', 'D3%', 'D4%', 'S01%', 'S02%', 'S03%', 'S04%', 'S06%', 'S07%', 'S08%', 'S09%', 'S1%', 'S2%', 'S3%', 'S4%', 'S5%', 'S6%', 'S7%', 'S8%', 'S9%', 'M%']) THEN CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Хирургия",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['C%', 'D0%', 'D1%', 'D2%', 'D3%', 'D4%', 'S01%', 'S02%', 'S03%', 'S04%', 'S06%', 'S07%', 'S08%', 'S09%', 'S1%', 'S2%', 'S3%', 'S4%', 'S5%', 'S6%', 'S7%', 'S8%', 'S9%', 'M%']) and CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Хирургия в МО",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['C%', 'D0%', 'D1%', 'D2%', 'D3%', 'D4%', 'S01%', 'S02%', 'S03%', 'S04%', 'S06%', 'S07%', 'S08%', 'S09%', 'S1%', 'S2%', 'S3%', 'S4%', 'S5%', 'S6%', 'S7%', 'S8%', 'S9%', 'M%']) and CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Хирургия на Дому",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['O%']) THEN CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Ак. и ген.",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['O%']) and CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Ак. и ген. в МО",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['O%']) and CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Ак. и ген. на Дому",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['P%', 'Q%']) THEN CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Педиатрия",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['P%', 'Q%']) and CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Педиатрия в МО",
                sum(CASE WHEN "Диагноз основной (DS1)" like ANY(array['P%', 'Q%']) and CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Педиатрия на Дому",
                sum(CASE WHEN CAST("Посещения в МО" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) ELSE 0 END ) as "Итого в МО",
                sum(CASE WHEN CAST("Посещения на Дому" AS numeric(8)) > 0 THEN CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Итого на Дому",
                sum(CASE WHEN CAST("Посещения" AS numeric(8)) > 0 THEN CAST("Посещения в МО" AS numeric(8)) +  CAST("Посещения на Дому" AS numeric(8)) ELSE 0 END ) as "Всего"
from oms.oms_data
where "Врач (Профиль МП)" = '57 общей врачебной практике (семейной медицине)'
and to_date("Первоначальная дата ввода", 'DD-MM-YYYY') BETWEEN to_date(:start_date, 'DD-MM-YYYY') and to_date(:end_date, 'DD-MM-YYYY')
group by  "врач"
"""