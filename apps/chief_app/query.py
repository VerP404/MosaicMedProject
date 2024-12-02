def base_query(year, months, inogorodniy, sanction, amount_null,
               building_ids=None,
               department_ids=None,
               profile_ids=None,
               doctor_ids=None,
               initial_input_date_start=None, initial_input_date_end=None,
               treatment_start=None, treatment_end=None,
               cel_list=None, status_list=None):
    building_filter = ""
    department_filter = ""
    profile_filter = ""
    doctor_filter = ""
    inogorodniy_filter = ""
    sanction_filter = ""
    amount_null_filter = ""
    treatment = ""
    initial_input = ""
    cels = ""
    status = ""

    if cel_list:
        status = "AND status IN (" + ",".join(f"'{cel}'" for cel in cel_list) + ")"
    if status_list:
        status = "AND status IN (" + ",".join(f"'{cel}'" for cel in status_list) + ")"

    if building_ids:
        building_filter = f"AND building_id IN ({','.join(map(str, building_ids))})"
    if department_ids:
        department_filter = f"AND department_id IN ({','.join(map(str, department_ids))})"

    if profile_ids:
        profile_filter = f"AND profile_id IN ({','.join(map(str, profile_ids))})"

    if doctor_ids:
        doctor_filter = f"AND doctor_id IN ({','.join(map(str, doctor_ids))})"

    if inogorodniy == '1':
        inogorodniy_filter = f"AND inogorodniy = false"
    if inogorodniy == '2':
        inogorodniy_filter = f"AND inogorodniy = true"

    if sanction == '1':
        sanction_filter = f"AND sanctions = '-'"
    if sanction == '2':
        sanction_filter = f"AND sanctions != '-'"

    if amount_null == '1':
        amount_null_filter = f"AND amount_numeric != '0'"
    if amount_null == '2':
        amount_null_filter = f"AND amount_numeric = '0'"

    if treatment_start and treatment_end:
        treatment = (f"AND to_date(treatment_end, 'DD-MM-YYYY') BETWEEN to_date('{treatment_start}', "
                     f"'DD-MM-YYYY') and to_date('{treatment_end}', 'DD-MM-YYYY')")

    if initial_input_date_start and initial_input_date_end:
        initial_input = (f"AND to_date(initial_input_date, 'DD-MM-YYYY') BETWEEN to_date('{initial_input_date_start}', "
                         f"'DD-MM-YYYY') and to_date('{initial_input_date_end}', 'DD-MM-YYYY')")

        return f""" with oms as е(select *
                    from data_oms
                     WHERE report_year = '{year}' 
                           AND report_month_number IN ({months})
                               {inogorodniy_filter}
                               {sanction_filter}
                               {amount_null_filter}
                               {building_filter}
                               {department_filter}
                               {profile_filter}
                               {doctor_filter}
                               {treatment}
                               {initial_input}
                               {cels}
                               {status}
                               )
        """
