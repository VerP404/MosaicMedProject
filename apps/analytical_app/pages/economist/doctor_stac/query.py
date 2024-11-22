# отчет по диспансеризации
from apps.analytical_app.pages.SQL_query.query import base_query


def sql_query_doc_stac_na_dom(selected_year, months_placeholder, inogorod, sanction, amount_null,
                              building=None,
                              department=None,
                              profile=None,
                              doctor=None,
                              input_start=None,
                              input_end=None,
                              treatment_start=None,
                              treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
        SELECT
            doctor AS "Врач",
            building AS "Корпус",
            department AS "Отделение",
            profile AS "Профиль",
            COUNT(*) AS "Случаи",
            SUM(
                CASE
                    WHEN visits = '-' THEN 0
                    WHEN visits ~ '^\\d+(\\.\\d+)?$' THEN CAST(visits AS NUMERIC)
                    ELSE 0
                END
            ) AS "Посещения",
            SUM(amount_numeric) as "Сумма"
        FROM oms
        WHERE goal = 'В дневном стационаре'
        GROUP BY doctor, building, department, profile
    """
    return query


def sql_query_doc_stac_v_ds(selected_year, months_placeholder, inogorod, sanction, amount_null,
                            building=None,
                            department=None,
                            profile=None,
                            doctor=None,
                            input_start=None,
                            input_end=None,
                            treatment_start=None,
                            treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
        SELECT
            doctor AS "Врач",
            building AS "Корпус",
            department AS "Отделение",
            profile AS "Профиль",
            COUNT(*) AS "Случаи",
            SUM(
                CASE
                    WHEN visits = '-' THEN 0
                    WHEN visits ~ '^\\d+(\\.\\d+)?$' THEN CAST(visits AS NUMERIC)
                    ELSE 0
                END
            ) AS "Посещения",
            SUM(amount_numeric) as "Сумма"
        FROM oms
        WHERE goal = 'В дневном стационаре'
        GROUP BY doctor, building, department, profile
    """
    return query


def sql_query_doc_stac_na_d(selected_year, months_placeholder, inogorod, sanction, amount_null,
                            building=None,
                            department=None,
                            profile=None,
                            doctor=None,
                            input_start=None,
                            input_end=None,
                            treatment_start=None,
                            treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
        SELECT
            doctor AS "Врач",
            building AS "Корпус",
            department AS "Отделение",
            profile AS "Профиль",
            COUNT(*) AS "Случаи",
            SUM(
                CASE
                    WHEN visits = '-' THEN 0
                    WHEN visits ~ '^\\d+(\\.\\d+)?$' THEN CAST(visits AS NUMERIC)
                    ELSE 0
                END
            ) AS "Посещения",
            SUM(amount_numeric) as "Сумма"
        FROM oms
        WHERE goal = 'На дому'
        GROUP BY doctor, building, department, profile
    """
    return query


def sql_query_doc_stac(selected_year, months_placeholder, inogorod, sanction, amount_null,
                       building=None,
                       department=None,
                       profile=None,
                       doctor=None,
                       input_start=None,
                       input_end=None,
                       treatment_start=None,
                       treatment_end=None):
    base = base_query(selected_year, months_placeholder, inogorod, sanction, amount_null, building, department, profile,
                      doctor,
                      input_start, input_end,
                      treatment_start, treatment_end)
    query = f"""
    {base}
        SELECT
            doctor AS "Врач",
            building AS "Корпус",
            department AS "Отделение",
            profile AS "Профиль",
            COUNT(*) AS "Случаи",
            SUM(
                CASE
                    WHEN visits = '-' THEN 0
                    WHEN visits ~ '^\\d+(\\.\\d+)?$' THEN CAST(visits AS NUMERIC)
                    ELSE 0
                END
            ) AS "Посещения",
            SUM(amount_numeric) as "Сумма"
        FROM oms
        WHERE goal = 'Стационарно'
        GROUP BY doctor, building, department, profile
    """
    return query
