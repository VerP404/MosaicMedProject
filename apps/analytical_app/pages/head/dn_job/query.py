def sql_head_dn_job():
    return f"""
    WITH combined_diagnoses AS (
    SELECT DISTINCT
        enp,
        status,
        LOWER(LEFT(main_diagnosis, POSITION(' ' IN main_diagnosis)-1)) AS ds
    FROM data_loader_omsdata
    WHERE main_diagnosis IS NOT NULL
    and goal = '3'
    UNION ALL

    SELECT DISTINCT
        enp,
        status,
        LOWER(LEFT(additional_diagnosis, POSITION(' ' IN additional_diagnosis)-1)) AS ds
    FROM data_loader_omsdata
    WHERE additional_diagnosis IS NOT NULL
    and goal = '3'
),

job_data AS (
    SELECT
        job.id_iszl,
        job.organization,
        job.fio,
        job.birth_date,
        job.enp,
        job.ds,
        CASE
            WHEN people.enp IS NOT NULL THEN 'да'
            ELSE 'нет'
        END AS attachment,
        CASE
            WHEN COUNT(CASE WHEN diag.enp IS NOT NULL THEN 1 END) > 0 THEN 'да'
            ELSE 'нет'
        END AS oms,
        CASE
            WHEN COUNT(CASE WHEN diag.enp IS NOT NULL AND diag.status = '3' THEN 1 END) > 0 THEN 'да'
            ELSE 'нет'
        END AS oms_paid
    FROM data_loader_iszldisnabjob AS job
    LEFT JOIN data_loader_iszlpeople AS people
        ON job.enp = people.enp
    LEFT JOIN combined_diagnoses AS diag
        ON job.enp = diag.enp
        AND LOWER(job.ds) = diag.ds
    GROUP BY
        job.id_iszl,
        job.organization,
        job.fio,
        job.birth_date,
        job.enp,
        job.ds,
        people.enp
)

SELECT
    COUNT(*) AS "Всего записей в ИСЗЛ",                                             
    COUNT(CASE WHEN attachment = 'да' THEN 1 END) AS "Прикреплено (заменить)",          
    COUNT(CASE WHEN attachment = 'нет' THEN 1 END) AS "Не прикреплено",     
    COUNT(CASE WHEN attachment = 'нет' AND oms = 'да' THEN 1 END) AS "Подано",  
    COUNT(CASE WHEN attachment = 'нет' AND oms_paid = 'да' THEN 1 END) AS "Оплачено"  
FROM job_data;
    """


def sql_head_dn_job2():
    return f"""
WITH combined_diagnoses AS (
    SELECT DISTINCT
        enp,
        status,
        LOWER(LEFT(main_diagnosis, POSITION(' ' IN main_diagnosis)-1)) AS ds
    FROM data_loader_omsdata
    WHERE main_diagnosis IS NOT NULL
    and goal = '3'

    UNION ALL

    SELECT DISTINCT
        enp,
        status,
        LOWER(LEFT(additional_diagnosis, POSITION(' ' IN additional_diagnosis)-1)) AS ds
    FROM data_loader_omsdata
    WHERE additional_diagnosis IS NOT NULL
    and goal = '3'
)

SELECT
    job.id_iszl,
    job.organization,
    job.fio,
    job.birth_date,
    job.enp,
    job.ds,
    CASE
        WHEN people.enp IS NOT NULL THEN 'да'
        ELSE 'нет'
    END AS "Прикреплен",
    CASE
        WHEN COUNT(CASE WHEN diag.enp IS NOT NULL THEN 1 END) > 0 THEN 'да'
        ELSE 'нет'
    END AS "Выставлено",
    CASE
        WHEN COUNT(CASE WHEN diag.enp IS NOT NULL AND diag.status = '3' THEN 1 END) > 0 THEN 'да'
        ELSE 'нет'
    END AS "Оплачено"
FROM data_loader_iszldisnabjob AS job
LEFT JOIN data_loader_iszlpeople AS people
    ON job.enp = people.enp
LEFT JOIN combined_diagnoses AS diag
    ON job.enp = diag.enp
    AND LOWER(job.ds) = diag.ds
GROUP BY
    job.id_iszl,
    job.organization,
    job.fio,
    job.birth_date,
    job.enp,
    job.ds,
    people.enp
ORDER BY job.fio;
    """
