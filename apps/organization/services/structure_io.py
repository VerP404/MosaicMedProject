"""
Экспорт/импорт структуры МО MosaicMedProject.

- native — полный снимок MedProject (корпусы, отделения, синонимы, участки, назначения)
- portal — medical_structure.json для MosaicPortal import_structure
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.organization.models import (
    Building,
    Department,
    DoctorAssignment,
    KvazarDepartment,
    MedicalOrganization,
    MiskauzDepartment,
    OMSDepartment,
    Station,
)
from apps.personnel.models import DoctorRecord

NATIVE_SCHEMA_VERSION = 1
PORTAL_FORMAT = "mosaicportal_medical_structure"
NATIVE_FORMAT = "mosaicmedproject_organization"

# Детерминированные UUID, чтобы повторный экспорт не плодил новые id
_UUID_NS = uuid.UUID("a3c8e1f0-7b2d-4e9a-9c1f-6d4b8a0e5f21")

_NON_MEDICAL_MARKERS = (
    "общий персонал",
    "общ. персонал",
    "административ",
    "хозяйствен",
    "аху",
)


def _stable_uuid(*parts: Any) -> str:
    key = ":".join(str(p) for p in parts)
    return str(uuid.uuid5(_UUID_NS, key))


def _iso_now() -> str:
    return timezone.now().isoformat()


def _date_iso(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


def _norm_name(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _is_medical_building(name: str, additional_name: str | None = None) -> bool:
    text = _norm_name(f"{name} {additional_name or ''}")
    return not any(marker in text for marker in _NON_MEDICAL_MARKERS)


def _pad_code(index: int, width: int = 2) -> str:
    return str(index).zfill(width)


def _derive_org_code(organization: MedicalOrganization, override: str | None = None) -> str:
    if override and override.strip():
        return override.strip()
    raw = (organization.code_mo or "").strip()
    if not raw:
        return "001"
    # Уже короткий код МО (001 / 003)
    if re.fullmatch(r"\d{1,3}", raw):
        return raw.zfill(3)
    # Иногда хранят полный код вида 360025 — берём хвост из 3 цифр, если похоже
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 3:
        return digits[-3:]
    return raw[:20]


def _prefetch_organization(organization: MedicalOrganization | None = None) -> MedicalOrganization:
    qs = MedicalOrganization.objects.prefetch_related(
        "buildings__departments__oms_departments",
        "buildings__departments__kvazar_departments",
        "buildings__departments__miskauz_departments",
        "buildings__departments__sections__doctor_assignments__doctor__person",
        "buildings__departments__sections__doctor__person",
    )
    if organization is not None:
        return qs.get(pk=organization.pk)
    org = qs.first()
    if org is None:
        raise ValueError("В базе нет медицинской организации")
    return org


# ---------------------------------------------------------------------------
# Native export / import
# ---------------------------------------------------------------------------

def build_native_structure(organization: MedicalOrganization | None = None) -> dict[str, Any]:
    org = _prefetch_organization(organization)
    buildings_out: list[dict[str, Any]] = []

    for building in org.buildings.all().order_by("id"):
        departments_out: list[dict[str, Any]] = []
        for department in building.departments.all().order_by("id"):
            stations_out: list[dict[str, Any]] = []
            for station in department.sections.all().order_by("code", "id"):
                assignments = []
                for assignment in station.doctor_assignments.all().order_by("-start_date", "id"):
                    doctor = assignment.doctor
                    person = doctor.person if doctor else None
                    assignments.append(
                        {
                            "doctor_code": doctor.doctor_code if doctor else None,
                            "person_last_name": getattr(person, "last_name", None),
                            "person_first_name": getattr(person, "first_name", None),
                            "person_patronymic": getattr(person, "patronymic", None),
                            "start_date": _date_iso(assignment.start_date),
                            "end_date": _date_iso(assignment.end_date),
                            "reason_for_transfer": assignment.reason_for_transfer or "",
                        }
                    )
                current_doctor = station.doctor
                stations_out.append(
                    {
                        "code": station.code,
                        "name": station.name or "",
                        "open_date": _date_iso(station.open_date),
                        "close_date": _date_iso(station.close_date),
                        "doctor_code": current_doctor.doctor_code if current_doctor else None,
                        "doctor_assignments": assignments,
                    }
                )

            departments_out.append(
                {
                    "name": department.name,
                    "additional_name": department.additional_name or "",
                    "description": department.description or "",
                    "oms_departments": [
                        {"name": item.name}
                        for item in department.oms_departments.all().order_by("name", "id")
                    ],
                    "kvazar_departments": [
                        {"name": item.name}
                        for item in department.kvazar_departments.all().order_by("name", "id")
                    ],
                    "miskauz_departments": [
                        {"name": item.name}
                        for item in department.miskauz_departments.all().order_by("name", "id")
                    ],
                    "stations": stations_out,
                }
            )

        buildings_out.append(
            {
                "name": building.name,
                "additional_name": building.additional_name or "",
                "name_kvazar": building.name_kvazar or "",
                "name_miskauz": building.name_miskauz or "",
                "address": building.address or "",
                "description": building.description or "",
                "departments": departments_out,
            }
        )

    return {
        "schema_version": NATIVE_SCHEMA_VERSION,
        "format": NATIVE_FORMAT,
        "exported_at": _iso_now(),
        "organization": {
            "name": org.name,
            "name_kvazar": org.name_kvazar or "",
            "name_miskauz": org.name_miskauz or "",
            "address": org.address or "",
            "phone_number": org.phone_number or "",
            "email": org.email or "",
            "code_mo": org.code_mo or "",
            "oid_mo": org.oid_mo or "",
            "buildings": buildings_out,
        },
    }


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (ValueError, AttributeError, TypeError):
        return None


def _find_doctor(doctor_code: str | None) -> DoctorRecord | None:
    if not doctor_code:
        return None
    return DoctorRecord.objects.filter(doctor_code=doctor_code).order_by("-id").first()


@transaction.atomic
def import_native_structure(
    data: dict[str, Any],
    *,
    clear_tree: bool = False,
    link_doctors: bool = True,
) -> dict[str, int]:
    """
    Импорт native JSON в текущую МО MedProject.
    clear_tree=True удаляет корпуса/отделения/участки перед загрузкой.
    """
    if data.get("format") not in (None, NATIVE_FORMAT):
        # допускаем старые файлы без format, если есть organization
        if "organization" not in data:
            raise ValueError(f"Неверный format: ожидается {NATIVE_FORMAT}")

    org_data = data.get("organization")
    if not isinstance(org_data, dict):
        raise ValueError('Неверный формат: отсутствует секция "organization"')

    org = MedicalOrganization.objects.first()
    if org is None:
        org = MedicalOrganization.objects.create(
            name=org_data.get("name") or "МО",
            name_kvazar=org_data.get("name_kvazar") or "",
            name_miskauz=org_data.get("name_miskauz") or "",
            address=org_data.get("address") or "",
            phone_number=org_data.get("phone_number") or "",
            email=org_data.get("email") or "noreply@example.com",
            code_mo=org_data.get("code_mo") or "",
            oid_mo=org_data.get("oid_mo") or "",
        )
    else:
        for field in (
            "name",
            "name_kvazar",
            "name_miskauz",
            "address",
            "phone_number",
            "email",
            "code_mo",
            "oid_mo",
        ):
            value = org_data.get(field)
            if value is not None and value != "":
                setattr(org, field, value)
        org.save()

    stats = {
        "buildings": 0,
        "departments": 0,
        "oms": 0,
        "kvazar": 0,
        "miskauz": 0,
        "stations": 0,
        "assignments": 0,
    }

    if clear_tree:
        org.buildings.all().delete()

    for building_data in org_data.get("buildings") or []:
        building, _ = Building.objects.update_or_create(
            organization=org,
            name=building_data.get("name") or "Корпус",
            defaults={
                "additional_name": building_data.get("additional_name") or "",
                "name_kvazar": building_data.get("name_kvazar") or "",
                "name_miskauz": building_data.get("name_miskauz") or "",
                "address": building_data.get("address") or None,
                "description": building_data.get("description") or None,
            },
        )
        stats["buildings"] += 1

        for dept_data in building_data.get("departments") or []:
            department, _ = Department.objects.update_or_create(
                building=building,
                name=dept_data.get("name") or "Отделение",
                defaults={
                    "additional_name": dept_data.get("additional_name") or "",
                    "description": dept_data.get("description") or None,
                },
            )
            stats["departments"] += 1

            # Синонимы: пересобираем по спискам из файла
            department.oms_departments.all().delete()
            department.kvazar_departments.all().delete()
            department.miskauz_departments.all().delete()

            for item in dept_data.get("oms_departments") or []:
                name = ((item.get("name") if isinstance(item, dict) else str(item)) or "").strip()
                if name:
                    OMSDepartment.objects.create(department=department, name=name)
                    stats["oms"] += 1

            for item in dept_data.get("kvazar_departments") or []:
                name = ((item.get("name") if isinstance(item, dict) else str(item)) or "").strip()
                if name:
                    KvazarDepartment.objects.create(department=department, name=name)
                    stats["kvazar"] += 1

            for item in dept_data.get("miskauz_departments") or []:
                name = ((item.get("name") if isinstance(item, dict) else str(item)) or "").strip()
                if name:
                    MiskauzDepartment.objects.create(department=department, name=name)
                    stats["miskauz"] += 1

            for station_data in dept_data.get("stations") or []:
                code = (station_data.get("code") or "").strip()
                if not code:
                    continue
                doctor = _find_doctor(station_data.get("doctor_code")) if link_doctors else None
                station, _ = Station.objects.update_or_create(
                    department=department,
                    code=code,
                    defaults={
                        "name": station_data.get("name") or "",
                        "open_date": _parse_date(station_data.get("open_date")),
                        "close_date": _parse_date(station_data.get("close_date")),
                        "doctor": doctor,
                    },
                )
                stats["stations"] += 1

                if link_doctors:
                    for assignment_data in station_data.get("doctor_assignments") or []:
                        a_doctor = _find_doctor(assignment_data.get("doctor_code"))
                        start_date = _parse_date(assignment_data.get("start_date"))
                        if not a_doctor or not start_date:
                            continue
                        DoctorAssignment.objects.update_or_create(
                            station=station,
                            doctor=a_doctor,
                            start_date=start_date,
                            defaults={
                                "end_date": _parse_date(assignment_data.get("end_date")),
                                "reason_for_transfer": assignment_data.get("reason_for_transfer") or "",
                            },
                        )
                        stats["assignments"] += 1

    return stats


# ---------------------------------------------------------------------------
# Portal export
# ---------------------------------------------------------------------------

def _index_portal_external_ids(portal_data: dict[str, Any] | None) -> dict[str, str]:
    """Индекс external_id из эталонного medical_structure.json Portal."""
    index: dict[str, str] = {}
    if not portal_data:
        return index

    for region in portal_data.get("regions") or []:
        rc = str(region.get("region_code") or "")
        if region.get("external_id"):
            index[f"region:{rc}"] = str(region["external_id"])
            index[f"region:name:{_norm_name(region.get('name'))}"] = str(region["external_id"])

        for org in region.get("organizations") or []:
            oc = str(org.get("org_code") or "")
            if org.get("external_id"):
                index[f"org:{rc}/{oc}"] = str(org["external_id"])
                index[f"org:name:{rc}/{_norm_name(org.get('name'))}"] = str(org["external_id"])

            for building in org.get("buildings") or []:
                bc = str(building.get("building_code") or "")
                if building.get("external_id"):
                    if bc:
                        index[f"building:{bc}"] = str(building["external_id"])
                    index[
                        f"building:name:{rc}/{oc}/{_norm_name(building.get('name'))}"
                    ] = str(building["external_id"])

                for department in building.get("departments") or []:
                    dc = str(department.get("department_code") or "")
                    if department.get("external_id"):
                        if dc:
                            index[f"department:{dc}"] = str(department["external_id"])
                        index[
                            f"department:name:{bc}/{_norm_name(department.get('name'))}"
                        ] = str(department["external_id"])

                    for synonym in department.get("synonyms") or []:
                        if synonym.get("external_id"):
                            key = (
                                f"synonym:{dc}/"
                                f"{synonym.get('external_system')}/"
                                f"{_norm_name(synonym.get('name'))}"
                            )
                            index[key] = str(synonym["external_id"])

                    for district in department.get("districts") or []:
                        dic = str(district.get("district_code") or "")
                        if district.get("external_id"):
                            if dic:
                                index[f"district:{dic}"] = str(district["external_id"])
                            index[
                                f"district:name:{dc}/{_norm_name(district.get('name'))}"
                            ] = str(district["external_id"])
    return index


def _resolve_id(index: dict[str, str], *keys: str, fallback_parts: tuple[Any, ...]) -> str:
    for key in keys:
        if key and key in index:
            return index[key]
    return _stable_uuid(*fallback_parts)


def build_portal_medical_structure(
    organization: MedicalOrganization | None = None,
    *,
    region_code: str = "36",
    region_name: str = "Воронеж",
    org_code: str | None = None,
    merge_from: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Конвертация структуры MedProject → medical_structure.json Portal.

    merge_from — опциональный эталонный Portal JSON: подставляет существующие
    external_id / коды по совпадению имён и org_code, чтобы не плодить дубликаты.
    """
    org = _prefetch_organization(organization)
    region_code = (region_code or "36").strip()
    region_name = (region_name or "Воронеж").strip()
    resolved_org_code = _derive_org_code(org, org_code)
    full_org_code = f"{region_code}.{resolved_org_code}"
    id_index = _index_portal_external_ids(merge_from)
    now = _iso_now()

    buildings_out: list[dict[str, Any]] = []
    total_departments = 0
    total_districts = 0
    total_synonyms = 0

    for b_idx, building in enumerate(org.buildings.all().order_by("id"), start=1):
        building_code = f"{full_org_code}.{_pad_code(b_idx)}"
        # если в эталоне корпус с таким именем уже есть — попробуем взять его код
        name_key = f"building:name:{region_code}/{resolved_org_code}/{_norm_name(building.name)}"
        if name_key in id_index and merge_from:
            for region in merge_from.get("regions") or []:
                if str(region.get("region_code")) != region_code:
                    continue
                for m_org in region.get("organizations") or []:
                    if str(m_org.get("org_code")) != resolved_org_code:
                        continue
                    for m_b in m_org.get("buildings") or []:
                        if _norm_name(m_b.get("name")) == _norm_name(building.name) and m_b.get(
                            "building_code"
                        ):
                            building_code = str(m_b["building_code"])
                            break

        building_id = _resolve_id(
            id_index,
            f"building:{building_code}",
            name_key,
            fallback_parts=("building", building.pk),
        )

        departments_out: list[dict[str, Any]] = []
        for d_idx, department in enumerate(building.departments.all().order_by("id"), start=1):
            department_code = f"{building_code}.{_pad_code(d_idx)}"
            dept_name_key = f"department:name:{building_code}/{_norm_name(department.name)}"
            if merge_from:
                for region in merge_from.get("regions") or []:
                    for m_org in region.get("organizations") or []:
                        for m_b in m_org.get("buildings") or []:
                            if str(m_b.get("building_code")) != building_code:
                                continue
                            for m_d in m_b.get("departments") or []:
                                if _norm_name(m_d.get("name")) == _norm_name(department.name) and m_d.get(
                                    "department_code"
                                ):
                                    department_code = str(m_d["department_code"])
                                    break

            department_id = _resolve_id(
                id_index,
                f"department:{department_code}",
                dept_name_key,
                fallback_parts=("department", department.pk),
            )

            synonyms_out: list[dict[str, Any]] = []
            for item in department.oms_departments.all().order_by("name", "id"):
                synonyms_out.append(
                    {
                        "external_id": _resolve_id(
                            id_index,
                            f"synonym:{department_code}/weboms/{_norm_name(item.name)}",
                            fallback_parts=("synonym", "weboms", item.pk),
                        ),
                        "name": item.name,
                        "external_system": "weboms",
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            for item in department.kvazar_departments.all().order_by("name", "id"):
                synonyms_out.append(
                    {
                        "external_id": _resolve_id(
                            id_index,
                            f"synonym:{department_code}/kvazar/{_norm_name(item.name)}",
                            fallback_parts=("synonym", "kvazar", item.pk),
                        ),
                        "name": item.name,
                        "external_system": "kvazar",
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            for item in department.miskauz_departments.all().order_by("name", "id"):
                synonyms_out.append(
                    {
                        "external_id": _resolve_id(
                            id_index,
                            f"synonym:{department_code}/miskauz/{_norm_name(item.name)}",
                            fallback_parts=("synonym", "miskauz", item.pk),
                        ),
                        "name": item.name,
                        "external_system": "miskauz",
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                )

            districts_out: list[dict[str, Any]] = []
            for s_idx, station in enumerate(
                department.sections.all().order_by("code", "id"), start=1
            ):
                district_code = f"{department_code}.{_pad_code(s_idx)}"
                district_name = station.code or station.name or f"Участок {s_idx}"
                districts_out.append(
                    {
                        "external_id": _resolve_id(
                            id_index,
                            f"district:{district_code}",
                            f"district:name:{department_code}/{_norm_name(district_name)}",
                            fallback_parts=("district", station.pk),
                        ),
                        "name": district_name,
                        "description": station.name or None,
                        "district_code": district_code,
                        "date_start": _date_iso(station.open_date),
                        "date_end": _date_iso(station.close_date),
                        "created_at": now,
                        "updated_at": now,
                    }
                )

            total_departments += 1
            total_districts += len(districts_out)
            total_synonyms += len(synonyms_out)

            departments_out.append(
                {
                    "external_id": department_id,
                    "name": department.name,
                    "department_code": department_code,
                    "date_start": None,
                    "date_end": None,
                    "created_at": now,
                    "updated_at": now,
                    "synonyms": synonyms_out,
                    "districts": districts_out,
                }
            )

        buildings_out.append(
            {
                "external_id": building_id,
                "name": building.name,
                "short_name": ((building.name_kvazar or "")[:50] or None),
                "additional_name": building.additional_name or None,
                "building_code": building_code,
                "is_medical": _is_medical_building(building.name, building.additional_name),
                "date_start": None,
                "date_end": None,
                "created_at": now,
                "updated_at": now,
                "departments": departments_out,
            }
        )

    region_id = _resolve_id(
        id_index,
        f"region:{region_code}",
        f"region:name:{_norm_name(region_name)}",
        fallback_parts=("region", region_code),
    )
    org_id = _resolve_id(
        id_index,
        f"org:{region_code}/{resolved_org_code}",
        f"org:name:{region_code}/{_norm_name(org.name)}",
        fallback_parts=("organization", org.pk),
    )

    return {
        "export_info": {
            "exported_at": now,
            "source": "mosaicmedproject",
            "format": PORTAL_FORMAT,
            "schema_version": 1,
            "total_regions": 1,
            "total_organizations": 1,
            "total_buildings": len(buildings_out),
            "total_departments": total_departments,
            "total_districts": total_districts,
            "total_department_synonyms": total_synonyms,
            "medproject": {
                "organization_id": org.pk,
                "code_mo": org.code_mo or "",
                "oid_mo": org.oid_mo or "",
            },
        },
        "regions": [
            {
                "external_id": region_id,
                "name": region_name,
                "region_code": region_code,
                "organizations": [
                    {
                        "external_id": org_id,
                        "name": org.name,
                        "org_code": resolved_org_code,
                        "oid_mo": org.oid_mo or "",
                        "full_code": full_org_code,
                        "created_at": now,
                        "updated_at": now,
                        "buildings": buildings_out,
                    }
                ],
            }
        ],
    }
