from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
import re

from django.db.models import Q

from apps.dn_matrix.models import (
    DnDiagnosis,
    DnDiagnosisCategory,
    DnDiagnosisGroup,
    DnDiagnosisGroupMembership,
    DnDiagnosisSpecialty,
    DnService,
    DnServicePrice,
    DnServicePricePeriod,
    DnServiceRequirement,
    DnUnavailableService,
    MatrixEdition,
)
from apps.dn_matrix.services.service_codes import normalize_dn_service_code


def normalize_mkb(code: str | int | float | None) -> str:
    """Нормализует код МКБ; принимает не только str (на случай «кривого» JSON из клиента)."""
    return str(code or "").strip().upper().replace(",", ".").replace(" ", "")


def normalize_patient_sex(raw: str | int | float | None) -> str | None:
    """Нормализация пола пациента: M / F или None."""
    text = str(raw or "").strip().upper()
    if not text:
        return None
    if text in ("M", "М", "MALE", "МУЖ", "МУЖСКОЙ", "МУЖ."):
        return "M"
    if text in ("F", "Ж", "FEMALE", "ЖЕН", "ЖЕНСКИЙ", "ЖЕН."):
        return "F"
    if text.startswith("М"):
        return "M"
    if text.startswith("Ж"):
        return "F"
    return None


def service_matches_patient_sex(svc_sex: str | None, patient_sex: str | None) -> bool:
    """Услуга подходит по полу; при неизвестном поле пациента — без фильтра."""
    sex = str(svc_sex or "").strip()
    if not sex:
        return True
    if not patient_sex:
        return True
    return sex == patient_sex


def category_for_mkb_in_cache(cache: MatrixPickCache, mkb_code: str) -> tuple[str, str] | None:
    did = cache.mkb_to_diagnosis_id.get(normalize_mkb(mkb_code))
    if did is None:
        return None
    return cache.diagnosis_id_to_category.get(did)


def diagnosis_id_for_mkb(edition_id: int, mkb: str) -> int | None:
    norm = normalize_mkb(mkb)
    if not norm:
        return None
    row = DnDiagnosis.objects.filter(edition_id=edition_id, mkb_code=norm).values_list("id", flat=True).first()
    return int(row) if row is not None else None


def _rule_dict(rule: object) -> dict:
    if isinstance(rule, dict):
        return rule
    return {}


def _rule_str_sequence(val: object) -> list:
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    return []


def _prefix_candidates(raw_prefix: str) -> list[str]:
    prefix = normalize_mkb(raw_prefix)
    if not prefix:
        return []
    out = [prefix]
    if re.match(r"^[A-Z]\d$", prefix):
        out.append(prefix[0])
    return out


def expand_group_diagnosis_ids(group: DnDiagnosisGroup) -> set[int]:
    """Явные членства + правило JSON (mkb_codes, mkb_prefixes, category_codes)."""
    ids: set[int] = set(
        DnDiagnosisGroupMembership.objects.filter(group=group).values_list("diagnosis_id", flat=True)
    )
    rule = _rule_dict(group.rule or {})
    edition_id = group.edition_id

    for raw in _rule_str_sequence(rule.get("mkb_codes")):
        did = diagnosis_id_for_mkb(edition_id, str(raw))
        if did is not None:
            ids.add(did)

    for raw in _rule_str_sequence(rule.get("mkb_prefixes")):
        for prefix in _prefix_candidates(str(raw)):
            for pk in DnDiagnosis.objects.filter(edition_id=edition_id, mkb_code__istartswith=prefix).values_list(
                "id", flat=True
            ):
                ids.add(int(pk))

    for cat_code in _rule_str_sequence(rule.get("category_codes")):
        cat = DnDiagnosisCategory.objects.filter(edition_id=edition_id, code=str(cat_code).strip()).first()
        if not cat:
            continue
        for pk in DnDiagnosis.objects.filter(edition_id=edition_id, category_id=cat.id).values_list("id", flat=True):
            ids.add(int(pk))

    return ids


def groups_for_diagnosis(edition_id: int, diagnosis_id: int) -> set[int]:
    out: set[int] = set(
        DnDiagnosisGroupMembership.objects.filter(diagnosis_id=diagnosis_id, group__edition_id=edition_id).values_list(
            "group_id", flat=True
        )
    )
    for g in DnDiagnosisGroup.objects.filter(edition_id=edition_id):
        if diagnosis_id in expand_group_diagnosis_ids(g):
            out.add(g.id)
    return out


def diagnosis_linked_to_specialty(diagnosis_id: int, specialty_id: int) -> bool:
    return DnDiagnosisSpecialty.objects.filter(diagnosis_id=diagnosis_id, specialty_id=specialty_id).exists()


def requirement_row_matches(
    req: DnServiceRequirement,
    specialty_id: int,
    allowed_diagnosis_ids: set[int],
    diagnosis_group_ids: set[int],
) -> bool:
    if req.specialty_id and req.specialty_id != specialty_id:
        return False
    if req.diagnosis_id and req.diagnosis_id not in allowed_diagnosis_ids:
        return False
    if req.diagnosis_group_id and req.diagnosis_group_id not in diagnosis_group_ids:
        return False
    return True


def service_applies(
    service_id: int,
    specialty_id: int,
    allowed_diagnosis_ids: set[int],
    diagnosis_group_ids: set[int],
) -> bool:
    reqs = list(DnServiceRequirement.objects.filter(service_id=service_id))
    if not reqs:
        return False
    return any(requirement_row_matches(r, specialty_id, allowed_diagnosis_ids, diagnosis_group_ids) for r in reqs)


def resolve_price_period(
    edition_id: int,
    *,
    period_id: int | None = None,
    price_on: date | None = None,
) -> DnServicePricePeriod | None:
    if period_id:
        return DnServicePricePeriod.objects.filter(pk=period_id, edition_id=edition_id).first()
    on = price_on or date.today()
    qs = DnServicePricePeriod.objects.filter(edition_id=edition_id, valid_from__lte=on).filter(
        Q(valid_to__isnull=True) | Q(valid_to__gte=on)
    )
    return qs.order_by("-valid_from", "-id").first()


@dataclass
class MatrixPickCache:
    """Предзагрузка матрицы для пакетного подбора."""

    edition_id: int
    mkb_to_diagnosis_id: dict[str, int]
    diagnosis_id_to_category: dict[int, tuple[str, str]]
    diagnosis_specialty: set[tuple[int, int]]
    diagnosis_specialty_billable: set[tuple[int, int]]
    diagnosis_to_groups: dict[int, frozenset[int]]
    services: list[tuple[int, str, str, str]]
    service_sex_by_id: dict[int, str]
    service_sex_by_code: dict[str, str]
    requirements_by_service: dict[int, list[tuple[int | None, int | None, int | None]]]
    periods: list[DnServicePricePeriod]
    prices_by_period_id: dict[int, dict[int, Decimal]]
    period_by_date: dict[date, DnServicePricePeriod | None] = field(default_factory=dict)
    max_doctor_visits: int = 3
    unavailable_codes: frozenset[str] = field(default_factory=frozenset)
    unavailable_codes_by_mkb: dict[str, frozenset[str]] = field(default_factory=dict)


def _resolve_period_from_list(periods: list[DnServicePricePeriod], price_on: date | None) -> DnServicePricePeriod | None:
    on = price_on or date.today()
    best: DnServicePricePeriod | None = None
    for period in periods:
        if period.valid_from > on:
            continue
        if period.valid_to is not None and period.valid_to < on:
            continue
        if best is None or period.valid_from > best.valid_from or (
            period.valid_from == best.valid_from and period.id > best.id
        ):
            best = period
    return best


def _build_diagnosis_group_index(
    edition_id: int,
    mkb_to_diagnosis_id: dict[str, int],
) -> dict[int, set[int]]:
    index: dict[int, set[int]] = defaultdict(set)
    for group_id, diagnosis_id in DnDiagnosisGroupMembership.objects.filter(group__edition_id=edition_id).values_list(
        "group_id", "diagnosis_id"
    ):
        index[int(diagnosis_id)].add(int(group_id))

    all_diagnoses = list(
        DnDiagnosis.objects.filter(edition_id=edition_id).values_list("id", "mkb_code", "category_id")
    )
    cat_by_code = {
        str(code).strip(): int(cid)
        for cid, code in DnDiagnosisCategory.objects.filter(edition_id=edition_id).values_list("id", "code")
    }

    for group in DnDiagnosisGroup.objects.filter(edition_id=edition_id):
        rule = _rule_dict(group.rule or {})
        matched_ids: set[int] = set()
        for raw in _rule_str_sequence(rule.get("mkb_codes")):
            did = mkb_to_diagnosis_id.get(normalize_mkb(str(raw)))
            if did is not None:
                matched_ids.add(did)
        for raw in _rule_str_sequence(rule.get("mkb_prefixes")):
            prefixes = _prefix_candidates(str(raw))
            if not prefixes:
                continue
            for pk, mkb, _cat in all_diagnoses:
                mkb_norm = normalize_mkb(mkb)
                if any(mkb_norm.startswith(prefix) for prefix in prefixes):
                    matched_ids.add(int(pk))
        for cat_code in _rule_str_sequence(rule.get("category_codes")):
            cat_id = cat_by_code.get(str(cat_code).strip())
            if cat_id is None:
                continue
            for pk, _mkb, diag_cat in all_diagnoses:
                if diag_cat == cat_id:
                    matched_ids.add(int(pk))
        for did in matched_ids:
            index[did].add(group.id)
    return {did: frozenset(gids) for did, gids in index.items()}


def build_matrix_pick_cache(edition: MatrixEdition) -> MatrixPickCache:
    edition_id = edition.id
    mkb_to_diagnosis_id: dict[str, int] = {}
    diagnosis_id_to_category: dict[int, tuple[str, str]] = {}
    for pk, mkb, cat_code, cat_title in (
        DnDiagnosis.objects.filter(edition_id=edition_id)
        .select_related("category")
        .values_list("id", "mkb_code", "category__code", "category__title")
    ):
        norm = normalize_mkb(mkb)
        if norm:
            mkb_to_diagnosis_id[norm] = int(pk)
        diagnosis_id_to_category[int(pk)] = (str(cat_code), str(cat_title))

    diagnosis_specialty = {
        (int(did), int(sid))
        for did, sid in DnDiagnosisSpecialty.objects.filter(diagnosis__edition_id=edition_id).values_list(
            "diagnosis_id", "specialty_id"
        )
    }
    diagnosis_specialty_billable = {
        (int(did), int(sid))
        for did, sid in DnDiagnosisSpecialty.objects.filter(
            diagnosis__edition_id=edition_id,
            kind__in=(
                DnDiagnosisSpecialty.Kind.PRIMARY,
                DnDiagnosisSpecialty.Kind.JOINT,
            ),
        ).values_list("diagnosis_id", "specialty_id")
    }
    diagnosis_to_groups = _build_diagnosis_group_index(edition_id, mkb_to_diagnosis_id)

    services = [
        (int(sid), str(code), str(title), str(sex or ""))
        for sid, code, title, sex in DnService.objects.filter(edition_id=edition_id)
        .order_by("sort_order", "code")
        .values_list("id", "code", "title", "sex_restriction")
    ]
    service_sex_by_id = {sid: sex for sid, _code, _title, sex in services}
    service_sex_by_code: dict[str, str] = {}
    for _sid, code, _title, sex in services:
        if sex:
            norm = normalize_dn_service_code(code)
            if norm:
                service_sex_by_code[norm] = sex

    requirements_by_service: dict[int, list[tuple[int | None, int | None, int | None]]] = defaultdict(list)
    for svc_id, spec_id, diag_id, grp_id in DnServiceRequirement.objects.filter(
        service__edition_id=edition_id
    ).values_list("service_id", "specialty_id", "diagnosis_id", "diagnosis_group_id"):
        requirements_by_service[int(svc_id)].append(
            (
                int(spec_id) if spec_id is not None else None,
                int(diag_id) if diag_id is not None else None,
                int(grp_id) if grp_id is not None else None,
            )
        )

    periods = list(DnServicePricePeriod.objects.filter(edition_id=edition_id).order_by("-valid_from", "-id"))
    prices_by_period_id: dict[int, dict[int, Decimal]] = defaultdict(dict)
    for period_id, svc_id, amt in DnServicePrice.objects.filter(period__edition_id=edition_id).values_list(
        "period_id", "service_id", "amount"
    ):
        prices_by_period_id[int(period_id)][int(svc_id)] = amt

    unavailable_codes: set[str] = set()
    unavailable_by_mkb: dict[str, set[str]] = defaultdict(set)
    for raw_code, mkb in DnUnavailableService.objects.filter(edition_id=edition_id).values_list(
        "service_code", "mkb_code"
    ):
        code = normalize_dn_service_code(raw_code)
        if not code:
            continue
        mkb_norm = normalize_mkb(mkb)
        if mkb_norm:
            unavailable_by_mkb[mkb_norm].add(code)
        else:
            unavailable_codes.add(code)

    return MatrixPickCache(
        edition_id=edition_id,
        mkb_to_diagnosis_id=mkb_to_diagnosis_id,
        diagnosis_id_to_category=diagnosis_id_to_category,
        diagnosis_specialty=diagnosis_specialty,
        diagnosis_specialty_billable=diagnosis_specialty_billable,
        diagnosis_to_groups=diagnosis_to_groups,
        services=services,
        service_sex_by_id=service_sex_by_id,
        service_sex_by_code=service_sex_by_code,
        requirements_by_service=dict(requirements_by_service),
        periods=periods,
        prices_by_period_id=dict(prices_by_period_id),
        max_doctor_visits=min(max(int(edition.max_doctor_visits or 3), 1), 3),
        unavailable_codes=frozenset(unavailable_codes),
        unavailable_codes_by_mkb={k: frozenset(v) for k, v in unavailable_by_mkb.items()},
    )


def _requirement_tuple_matches(
    req: tuple[int | None, int | None, int | None],
    specialty_id: int,
    allowed_diagnosis_ids: set[int],
    diagnosis_group_ids: set[int],
) -> bool:
    req_spec, req_diag, req_grp = req
    if req_spec and req_spec != specialty_id:
        return False
    if req_diag and req_diag not in allowed_diagnosis_ids:
        return False
    if req_grp and req_grp not in diagnosis_group_ids:
        return False
    return True


def service_marked_unavailable(cache: MatrixPickCache, service_code: str, mkb_code: str | None) -> bool:
    code = normalize_dn_service_code(service_code)
    if not code:
        return False
    if code in cache.unavailable_codes:
        return True
    mkb = normalize_mkb(mkb_code)
    if not mkb:
        return False
    return code in cache.unavailable_codes_by_mkb.get(mkb, frozenset())


def _service_applies_cached(
    cache: MatrixPickCache,
    service_id: int,
    specialty_id: int,
    allowed_diagnosis_ids: set[int],
    diagnosis_group_ids: set[int],
) -> bool:
    reqs = cache.requirements_by_service.get(service_id)
    if not reqs:
        return False
    return any(
        _requirement_tuple_matches(r, specialty_id, allowed_diagnosis_ids, diagnosis_group_ids) for r in reqs
    )


def _pick_source_for_service(
    cache: MatrixPickCache,
    service_id: int,
    specialty_id: int,
    main_diagnosis_id: int,
    group_main: set[int],
    secondary_diagnosis_ids: set[int],
) -> str:
    if not secondary_diagnosis_ids:
        return "main"

    secondary_groups: set[int] = set()
    for sid in secondary_diagnosis_ids:
        secondary_groups |= set(cache.diagnosis_to_groups.get(sid, ()))

    has_main = False
    has_secondary = False
    for req in cache.requirements_by_service.get(service_id) or []:
        req_spec, req_diag, req_grp = req
        if req_spec and req_spec != specialty_id:
            continue

        if not _requirement_tuple_matches(
            req,
            specialty_id,
            {main_diagnosis_id} | secondary_diagnosis_ids,
            group_main | secondary_groups,
        ):
            continue

        if req_diag is None and req_grp is None:
            has_main = True
            continue

        if (req_diag is None or req_diag == main_diagnosis_id) and (req_grp is None or req_grp in group_main):
            has_main = True

        if req_diag and req_diag in secondary_diagnosis_ids:
            has_secondary = True
        elif req_grp and req_grp not in group_main and req_grp in secondary_groups:
            has_secondary = True

    if has_main and has_secondary:
        return "main+secondary"
    if has_secondary:
        return "secondary"
    return "main"


def _normalize_secondary_mkb_list(
    secondary_mkb_list: list[str] | None,
    secondary_mkb: str | None,
) -> list[str]:
    secondaries: list[str] = []
    if secondary_mkb_list:
        seen: set[str] = set()
        for raw in secondary_mkb_list:
            n = normalize_mkb(str(raw))
            if not n or n in seen:
                continue
            seen.add(n)
            secondaries.append(n)
    if secondary_mkb:
        n = normalize_mkb(secondary_mkb)
        if n and n not in secondaries:
            secondaries.append(n)
    return secondaries


def select_services_from_cache(
    cache: MatrixPickCache,
    *,
    specialty_id: int,
    mkb_code: str,
    price_period_id: int | None = None,
    price_on: date | None = None,
    secondary_mkb: str | None = None,
    secondary_mkb_list: list[str] | None = None,
    patient_sex: str | None = None,
) -> tuple[list[dict], DnServicePricePeriod | None, int | None]:
    diagnosis_id = cache.mkb_to_diagnosis_id.get(normalize_mkb(mkb_code))
    if price_period_id:
        period = next((p for p in cache.periods if p.id == price_period_id), None)
    else:
        on = price_on or date.today()
        if on not in cache.period_by_date:
            cache.period_by_date[on] = _resolve_period_from_list(cache.periods, on)
        period = cache.period_by_date[on]

    if diagnosis_id is None:
        return [], period, None
    if (diagnosis_id, specialty_id) not in cache.diagnosis_specialty:
        return [], period, diagnosis_id

    secondaries = _normalize_secondary_mkb_list(secondary_mkb_list, secondary_mkb)
    group_main = set(cache.diagnosis_to_groups.get(diagnosis_id, ()))
    group_ids = set(group_main)
    secondary_diagnosis_ids: set[int] = set()
    for smkb in secondaries:
        sid2 = cache.mkb_to_diagnosis_id.get(smkb)
        if sid2 is None or sid2 == diagnosis_id:
            continue
        if (sid2, specialty_id) not in cache.diagnosis_specialty:
            continue
        secondary_diagnosis_ids.add(sid2)
        group_ids |= set(cache.diagnosis_to_groups.get(sid2, ()))

    allowed_diagnosis_ids = {diagnosis_id} | secondary_diagnosis_ids
    prices: dict[int, Decimal] = cache.prices_by_period_id.get(period.id, {}) if period else {}
    out: list[dict] = []
    for svc_id, code, title, svc_sex in cache.services:
        if not _service_applies_cached(cache, svc_id, specialty_id, allowed_diagnosis_ids, group_ids):
            continue
        if not service_matches_patient_sex(svc_sex, patient_sex):
            continue
        amt = prices.get(svc_id)
        pick_source = _pick_source_for_service(
            cache,
            svc_id,
            specialty_id,
            diagnosis_id,
            group_main,
            secondary_diagnosis_ids,
        )
        service_code = normalize_dn_service_code(code)
        out.append(
            {
                "id": svc_id,
                "code": service_code,
                "title": title,
                "price": str(amt) if amt is not None else None,
                "currency": "RUB",
                "price_period_id": period.id if period else None,
                "pick_source": pick_source,
                "obligation": "не задано",
                "sex_restriction": svc_sex or None,
                "unavailable": service_marked_unavailable(cache, service_code, mkb_code),
            }
        )
    return out, period, diagnosis_id


def select_services_for_context(
    edition: MatrixEdition,
    *,
    specialty_id: int,
    mkb_code: str,
    price_period_id: int | None = None,
    price_on: date | None = None,
    secondary_mkb: str | None = None,
    secondary_mkb_list: list[str] | None = None,
    pick_cache: MatrixPickCache | None = None,
    patient_sex: str | None = None,
) -> tuple[list[dict], DnServicePricePeriod | None, int | None]:
    """Возвращает (список услуг с ценой), период, id диагноза или None если диагноз не найден."""
    if pick_cache is None:
        pick_cache = build_matrix_pick_cache(edition)
    return select_services_from_cache(
        pick_cache,
        specialty_id=specialty_id,
        mkb_code=mkb_code,
        price_period_id=price_period_id,
        price_on=price_on,
        secondary_mkb=secondary_mkb,
        secondary_mkb_list=secondary_mkb_list,
        patient_sex=patient_sex,
    )


def cap_doctor_visits(edition: MatrixEdition, visits: int) -> int:
    cap = int(getattr(edition, "max_doctor_visits", None) or 3)
    cap = min(max(cap, 1), 3)
    return min(max(int(visits), 1), cap)


def edition_covers_date(edition: MatrixEdition, on: date) -> bool:
    if edition.effective_from > on:
        return False
    if edition.effective_to and edition.effective_to < on:
        return False
    return True


def resolve_edition_for_date(editions: list[MatrixEdition], on: date) -> MatrixEdition | None:
    candidates = [e for e in editions if edition_covers_date(e, on)]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    active = [e for e in candidates if e.status == MatrixEdition.Status.ACTIVE]
    pool = active or candidates
    return max(pool, key=lambda e: (e.effective_from, e.id))
