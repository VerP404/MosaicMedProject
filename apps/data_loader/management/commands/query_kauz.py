from datetime import datetime, timedelta

date_start = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
date_end = datetime.now().strftime('%d.%m.%Y')

query_kauz_talon = f"""
SELECT ca.ID                            AS "Талон",
       'МИС КАУЗ'                       AS "Источник",
       '-'                              AS "ID источника",
       case
           when ACCOUNTS.NUMACCOUNT is null then '-'
           else ACCOUNTS.NUMACCOUNT end AS "Номер счёта",
       COALESCE(
               LPAD(CAST(EXTRACT(DAY FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(2)), 2, '0') || '-' ||
               LPAD(CAST(EXTRACT(MONTH FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(2)), 2, '0') || '-' ||
               CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4)),
               '-')                     AS "Дата выгрузки",
       '-'                              AS "Причина аннулирования",
    CASE
           WHEN ca.IDSTATUSACCOUNT = 1 THEN 0
           WHEN ca.IDSTATUSACCOUNT = 2 THEN 1
           WHEN ca.IDSTATUSACCOUNT = 3 THEN 6
           WHEN ca.IDSTATUSACCOUNT = 4 THEN 2
           WHEN ca.IDSTATUSACCOUNT = 5 THEN 3
           WHEN ca.IDSTATUSACCOUNT = 0 THEN 0
           WHEN ca.IDSTATUSACCOUNT = 6 THEN 0
           WHEN ca.IDSTATUSACCOUNT = 7 THEN 5
           WHEN ca.IDSTATUSACCOUNT = 8 THEN 0
           WHEN ca.IDSTATUSACCOUNT = 9 THEN 0
           WHEN ca.IDSTATUSACCOUNT = 10 THEN 7
           ELSE ca.IDSTATUSACCOUNT
END
AS "Статус",
       '-'                                                                                             AS "Тип талона",
       CASE
           WHEN ca.IDTARGET = 1 AND ca.IDTYPEDOCUMENTCASE = 3 AND
                TYPESACCOUNTS.NAME = 'ДНЕВНОЙ СТАЦИОНАР, СТАЦИОНАР НА ДОМУ, ЦАПХ (БЕЗ ОНКО)' THEN 'В дневном стационаре'
           WHEN ca.IDTARGET = 1 AND ca.IDTYPEDOCUMENTCASE = 4 AND
                TYPESACCOUNTS.NAME = 'ДНЕВНОЙ СТАЦИОНАР, СТАЦИОНАР НА ДОМУ, ЦАПХ (БЕЗ ОНКО)' THEN 'На дому'
           WHEN ca.IDTARGET = 502 THEN 55
           WHEN ca.IDTARGET = 38 THEN 'ДВ4'
           WHEN ca.IDTARGET = 39 THEN 'ДВ2'
           WHEN ca.IDTARGET = 35 THEN 'ОПВ'
           WHEN ca.IDTARGET = 382 THEN 'УД1'
           WHEN ca.IDTARGET = 392 THEN 'УД2'
           WHEN ca.IDTARGET = 383 THEN 'ДР1'
           WHEN ca.IDTARGET = 393 THEN 'ДР2'
           WHEN ca.IDTARGET = 43 THEN 'ПН1'
           WHEN ca.IDTARGET = 44 THEN 'ПН1'
           WHEN ca.IDTARGET = 40 THEN 'ДС1'
           WHEN ca.IDTARGET = 49 THEN 'ДС2'
           ELSE ca.IDTARGET
END
AS "Цель",
       '-'                                                                                             AS "Фед. цель",
       ca.SURNAME || ' ' || ca.FIRSTNAME || ' ' || ca.PATRONYMIC                                       AS "Пациент",
       LPAD(CAST(EXTRACT(DAY FROM ca.DATEBIRTH) AS VARCHAR(2)), 2, '0') || '-' ||
       LPAD(CAST(EXTRACT(MONTH FROM ca.DATEBIRTH) AS VARCHAR(2)), 2, '0') || '-' ||
       CAST(EXTRACT(YEAR FROM ca.DATEBIRTH) AS VARCHAR(4))                                             AS "Дата рождения",
       '-'                                                                                             AS "Возраст",
       ca.IDSEX                                                                                        AS "Пол",
       ca.SERNUMPOLICYOMS                                                                              AS "Полис",
       CASE
           WHEN IDINSURER = 71 OR IDINSURER = 79 THEN 36071
           WHEN IDINSURER = 65 THEN 36065
           ELSE IDINSURER
END
AS "Код СМО",
       INSURERS.NAMELEGAL                                                                              AS "Страховая",

       ca.SERNUMPOLICYOMS                                                                              AS "ЕНП",
       LPAD(CAST(EXTRACT(DAY FROM ca.DATBEGVST) AS VARCHAR(2)), 2, '0') || '-' ||
       LPAD(CAST(EXTRACT(MONTH FROM ca.DATBEGVST) AS VARCHAR(2)), 2, '0') || '-' ||
       CAST(EXTRACT(YEAR FROM ca.DATBEGVST) AS VARCHAR(4))                                             AS "Начало лечения",
       LPAD(CAST(EXTRACT(DAY FROM ca.DATENDVST) AS VARCHAR(2)), 2, '0') || '-' ||
       LPAD(CAST(EXTRACT(MONTH FROM ca.DATENDVST) AS VARCHAR(2)), 2, '0') || '-' ||
       CAST(EXTRACT(YEAR FROM ca.DATENDVST) AS VARCHAR(4))                                             AS "Окончание лечения",
       DOCTORS.TABN || ' ' || DOCTORS.SURNAME || ' ' || DOCTORS.FIRSTNAME || ' ' || DOCTORS.PATRONYMIC AS "Врач",
       '-'                                                                                             AS "Врач (Профиль МП)",
       '-'                                                                                             AS "Должность мед.персонала (V021)",
       LPU.NAME                                                                                        AS "Подразделение",
       '-'                                                                                             AS "Условия оказания помощи",
       '-'                                                                                             AS "Вид мед. помощи",
       '-'                                                                                             AS "Тип заболевания",
       '-'                                                                                             AS "Характер основного заболевания",
       ca.CNTVSTLPU + ca.CNTVSTHOME                                                                    AS "Посещения",
       ca.CNTVSTLPU                                                                                    AS "Посещения в МО",
       ca.CNTVSTHOME                                                                                   AS "Посещения на Дому",
       '-'                                                                                             AS "Случай",
       MKB10.COD                                                                                       AS "Диагноз основной (DS1)",
       COALESCE(NULLIF(TRIM(BOTH ', ' FROM
                            COALESCE(MKB10_CONT1.COD || ', ', '') ||
                            COALESCE(MKB10_CONT2.COD, '')
                       ), ''),
                '-')                                                                                   AS "Сопутствующий диагноз (DS2)",
       SPECIALITIES.PROFIL_FED                                                                         AS "Профиль МП",
       '-'                                                                                             AS "Профиль койки",
       '-'                                                                                             AS "Диспансерное наблюдение",
       PRVS.V021CODE                                                                                   AS "Специальность",
       '-'                                                                                             AS "Исход",
       '-'                                                                                             AS "Результат",
       'МИС КАУЗ'                                                                                      AS "Оператор",
       LPAD(CAST(EXTRACT(DAY FROM ca.DATEINSERT) AS VARCHAR(2)), 2, '0') || '-' ||
       LPAD(CAST(EXTRACT(MONTH FROM ca.DATEINSERT) AS VARCHAR(2)), 2, '0') || '-' ||
       CAST(EXTRACT(YEAR FROM ca.DATEINSERT) AS VARCHAR(4))                                            AS "Первоначальная дата ввода",
       COALESCE(
               LPAD(CAST(EXTRACT(DAY FROM ca.DATEUPDATE) AS VARCHAR(2)), 2, '0') || '-' ||
               LPAD(CAST(EXTRACT(MONTH FROM ca.DATEUPDATE) AS VARCHAR(2)), 2, '0') || '-' ||
               CAST(EXTRACT(YEAR FROM ca.DATEUPDATE) AS VARCHAR(4)),
               '-')                                                                                    AS "Дата последнего изменения",
       '-'                                                                                             AS "Тариф",
       case
           when ACCOUNTS.SUMACCOUNT is null then 0
           else ACCOUNTS.SUMACCOUNT
end
AS "Сумма",
       '-'                                                                                             AS "Оплачено",
       '-'                                                                                             AS "Тип оплаты",
       '-'                                                                                             AS "Санкции",
       KSG_DS.CODE                                                                                     AS "КСГ",
       '-'                                                                                             AS "КЗ",
       '-'                                                                                             AS "Код схемы лекарственной терапии",
       '-'                                                                                             AS "УЕТ",
       '-'                                                                                             AS "Классификационный критерий",
       '-'                                                                                             AS "ШРМ",
       '-'                                                                                             AS "МО, направившая",
       '-'                                                                                             AS "Код способа оплаты",
       '-'                                                                                             AS "Новорожденный",
       '-'                                                                                             AS "Представитель",
       '-'                                                                                             AS "Доп. инф. о статусе талона",
       '-'                                                                                             AS "КСЛП",
       '-'                                                                                             AS "Источник оплаты",

       COALESCE(
               TRIM(
                       CASE EXTRACT(MONTH FROM ACCOUNTS.DATACCOUNT)
                           WHEN 1 THEN 'Января' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 2 THEN 'Февраля' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 3 THEN 'Марта' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 4 THEN 'Апреля' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 5 THEN 'Мая' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 6 THEN 'Июня' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 7 THEN 'Июля' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 8 THEN 'Августа' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 9 THEN 'Сентября' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 10 THEN 'Октября' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 11 THEN 'Ноября' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           WHEN 12 THEN 'Декабря' || ' ' || CAST(EXTRACT(YEAR FROM ACCOUNTS.DATACCOUNT) AS VARCHAR(4))
                           END
               ), '-'
       )                                                            AS "Отчетный период выгрузки"
FROM CASESAMB AS ca
         LEFT JOIN LPU ON ca.IDLPU = LPU.ID
         LEFT JOIN TYPESACCOUNTS ON ca.IDTYPEACCOUNT = TYPESACCOUNTS.ID
         LEFT JOIN DOCTORS ON ca.IDDOCTOR = DOCTORS.ID
         LEFT JOIN PRVS ON DOCTORS.PRVS = PRVS.ID
         LEFT JOIN INSURERS ON ca.IDINSURER = INSURERS.ID
         LEFT JOIN SPECIALITIES ON ca.IDSPECIALITY = SPECIALITIES.ID
         LEFT JOIN MKB10 ON ca.IDDGMAIN = MKB10.ID
         LEFT JOIN MKB10 MKB10_CONT1 ON ca.IDDGCONT1 = MKB10_CONT1.ID
         LEFT JOIN MKB10 MKB10_CONT2 ON ca.IDDGCONT2 = MKB10_CONT2.ID
         LEFT JOIN KSG_DS ON ca.IDKSG_DS = KSG_DS.ID
         LEFT JOIN (SELECT a.*
                    FROM ACCOUNTS a
                    WHERE a.DATACCOUNT = (SELECT MAX(sub_a.DATACCOUNT)
                                          FROM ACCOUNTS sub_a
                                          WHERE sub_a.IDCASEAMB = a.IDCASEAMB)) ACCOUNTS ON ca.ID = ACCOUNTS.IDCASEAMB
WHERE ca.DATEUPDATE BETWEEN '{date_start}' AND '{date_end}';
"""
