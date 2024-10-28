def build_sql_filters(**kwargs):
    filters = []
    if kwargs.get("building_ids"):
        building_ids_str = ', '.join(map(str, kwargs["building_ids"]))
        filters.append(f"AND department.building_id IN ({building_ids_str})")

    if kwargs.get("department_ids"):
        department_ids_str = ', '.join(map(str, kwargs["department_ids"]))
        filters.append(f"AND doctor.department_id IN ({department_ids_str})")

    if kwargs.get("profile_ids"):
        profile_ids_str = ', '.join(map(str, kwargs["profile_ids"]))
        filters.append(f"AND doctor.profile_id IN ({profile_ids_str})")

    if kwargs.get("doctor_ids"):
        doctor_ids_str = ', '.join(map(str, kwargs["doctor_ids"]))
        filters.append(f"AND doctor.id IN ({doctor_ids_str})")

    return " ".join(filters)
