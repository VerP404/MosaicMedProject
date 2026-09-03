"""Обёртки для Dash: редакции, справочники, подбор услуг."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import connection
from django.db.utils import OperationalError, ProgrammingError

from apps.dn_matrix.models import (
    DnDiagnosis,
    DnDiagnosisGroup,
    DnDiagnosisGroupMembership,
    DnDiagnosisSpecialty,
    DnService,
    DnServicePrice,
    DnServicePricePeriod,
    DnSpecialty,
    DnUnavailableService,
    MatrixEdition,
)
from apps.dn_matrix.services.matrix import cap_doctor_visits, normalize_mkb, select_services_for_context
from apps.dn_matrix.services.pick_pricing import format_amount, service_line_qty, sum_services_amount
from apps.dn_matrix.services.service_codes import normalize_dn_service_code

def _service_title_without_code(code: str, title: str) -> str:
    """Убирает код из начала названия, если он уже продублирован в title матрицы."""
    text = (title or "").strip()
    code_n = (code or "").strip()
    if not text:
        return ""
    for prefix in (code_n, str(code_n).replace("-", ".")):
        if not prefix:
            continue
        for sep in (" — ", " – ", " - ", "—", "–", "-"):
            candidate = prefix + sep
            if text.lower().startswith(candidate.lower()):
                return text[len(candidate) :].strip() or text
    return text


PICK_SOURCE_LABELS = {
    "main": "По основному",
    "secondary": "По сопутствующему",
    "main+secondary": "По основному и сопутствующему",
}

SEX_LABELS = {
    "M": "М",
    "F": "Ж",
}


def _without_matrix_tables(default):
    """Импорт Dash не должен падать, если миграции dn_matrix ещё не применены."""

    def deco(fn):
        def wrapped(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except (ProgrammingError, OperationalError):
                try:
                    connection.rollback()
                except Exception:
                    pass
                return default

        return wrapped

    return deco


@_without_matrix_tables(None)
def default_edition() -> MatrixEdition | None:
    active = MatrixEdition.objects.filter(status=MatrixEdition.Status.ACTIVE).order_by("-effective_from", "-id").first()
    if active:
        return active
    return MatrixEdition.objects.exclude(status=MatrixEdition.Status.ARCHIVED).order_by("-effective_from", "-id").first()


@_without_matrix_tables([])
def edition_options() -> list[dict]:
    rows = []
    for e in MatrixEdition.objects.exclude(status=MatrixEdition.Status.ARCHIVED).order_by("-effective_from", "code"):
        suffix = ""
        if e.status == MatrixEdition.Status.ACTIVE:
            suffix = " (active)"
        elif e.status == MatrixEdition.Status.DRAFT:
            suffix = " (черновик)"
        rows.append({"label": f"{e.title}{suffix}", "value": e.id})
    return rows


def get_edition(edition_id: int | None) -> MatrixEdition | None:
    if edition_id:
        return MatrixEdition.objects.filter(pk=edition_id).first()
    return default_edition()


def specialty_options(edition: MatrixEdition) -> list[dict]:
    return [
        {"label": s.title or s.code, "value": s.id}
        for s in edition.specialties.all().order_by("sort_order", "title", "code")
    ]


def diagnosis_options(edition: MatrixEdition, specialty_id: int | None = None) -> list[dict]:
    qs = DnDiagnosis.objects.filter(edition=edition).order_by("mkb_code")
    if specialty_id:
        qs = qs.filter(specialty_links__specialty_id=specialty_id).distinct()
    out = []
    for d in qs:
        title = (d.title or "").strip()
        label = d.mkb_code if not title or title.upper() == d.mkb_code.upper() else f"{d.mkb_code} — {title}"
        out.append({"label": label, "value": d.mkb_code})
    return out


def pick_services(
    edition: MatrixEdition,
    *,
    specialty_id: int,
    mkb: str,
    secondary_mkb_list: list[str] | None = None,
    visits: int = 1,
    patient_sex: str | None = None,
    price_on: date | None = None,
) -> dict:
    visits_capped = cap_doctor_visits(edition, visits)
    services, period, diagnosis_id = select_services_for_context(
        edition,
        specialty_id=specialty_id,
        mkb_code=mkb,
        secondary_mkb_list=secondary_mkb_list or None,
        patient_sex=patient_sex,
        price_on=price_on,
    )

    def is_per_visit(title: str) -> bool:
        return "диспансерный прием" in (title or "").lower()

    services = sorted(
        services,
        key=lambda r: (1 if r.get("unavailable") else 0, 0 if is_per_visit(r["title"]) else 1, r["title"]),
    )
    rows = []
    for s in services:
        unavailable = bool(s.get("unavailable"))
        qty = service_line_qty(s["title"], visits_capped, max_visits=edition.max_doctor_visits)
        price = s.get("price")
        amount = None
        if price is not None:
            amount = Decimal(str(price)) * qty
        sex = s.get("sex_restriction") or ""
        rows.append(
            {
                "Проводится": "не проводится" if unavailable else "да",
                "Код": s["code"],
                "Название": _service_title_without_code(s["code"], s["title"]),
                "Подбор": PICK_SOURCE_LABELS.get(s.get("pick_source") or "", s.get("pick_source") or "—"),
                "Пол": SEX_LABELS.get(sex, "—"),
                "Обязательность": s.get("obligation") or "не задано",
                "Цена за ед.": price or "—",
                "Кол-во": qty,
                "Сумма": format_amount(amount) if amount is not None else "—",
                "_excluded": "1" if unavailable else "0",
            }
        )
    max_visits = min(max(int(edition.max_doctor_visits or 3), 1), 3)
    included = [s for s in services if not s.get("unavailable")]
    excluded = [s for s in services if s.get("unavailable")]
    total, missing = sum_services_amount(services, visits_capped, max_visits=max_visits)
    excluded_total, _ = sum_services_amount(
        excluded, visits_capped, max_visits=max_visits, skip_unavailable=False
    )
    sums: dict[int, str] = {}
    for n in range(1, 4):
        if n <= max_visits:
            amt, _miss = sum_services_amount(services, n, max_visits=max_visits)
            sums[n] = format_amount(amt)
    return {
        "rows": rows,
        "diagnosis_id": diagnosis_id,
        "price_period_id": period.id if period else None,
        "visits": visits_capped,
        "max_visits": max_visits,
        "total": format_amount(total),
        "sums": sums,
        "missing_prices": missing,
        "count": len(included),
        "excluded_count": len(excluded),
        "excluded_total": format_amount(excluded_total),
    }


def directory_specialties(edition: MatrixEdition) -> list[dict]:
    return [
        {"Код": s.code, "Название": s.title, "Порядок": s.sort_order}
        for s in edition.specialties.all().order_by("sort_order", "code")
    ]


def directory_diagnoses(edition: MatrixEdition) -> list[dict]:
    return [
        {
            "МКБ": d.mkb_code,
            "Название": d.title,
            "Категория": d.category.title if d.category_id else "",
        }
        for d in edition.diagnoses.select_related("category").order_by("mkb_code")
    ]


def directory_diagnosis_specialties(edition: MatrixEdition) -> list[dict]:
    kind_labels = dict(DnDiagnosisSpecialty.Kind.choices)
    return [
        {
            "МКБ": row.diagnosis.mkb_code,
            "Диагноз": row.diagnosis.title,
            "Специальность": row.specialty.title,
            "Тип связи": kind_labels.get(row.kind, row.kind),
        }
        for row in DnDiagnosisSpecialty.objects.filter(diagnosis__edition=edition)
        .select_related("diagnosis", "specialty")
        .order_by("diagnosis__mkb_code", "specialty__code", "kind")
    ]


def directory_groups(edition: MatrixEdition) -> list[dict]:
    return [
        {"Код": g.code, "Название": g.title, "Порядок": g.sort_order}
        for g in DnDiagnosisGroup.objects.filter(edition=edition).order_by("sort_order", "code")
    ]


def directory_group_memberships(edition: MatrixEdition) -> list[dict]:
    return [
        {"Группа": m.group.code, "МКБ": m.diagnosis.mkb_code, "Диагноз": m.diagnosis.title}
        for m in DnDiagnosisGroupMembership.objects.filter(group__edition=edition)
        .select_related("group", "diagnosis")
        .order_by("group__code", "diagnosis__mkb_code")[:5000]
    ]


def directory_services(edition: MatrixEdition) -> list[dict]:
    return [
        {
            "Код": s.code,
            "Название": s.title,
            "Пол": SEX_LABELS.get(s.sex_restriction or "", "Любой"),
            "Порядок": s.sort_order,
        }
        for s in DnService.objects.filter(edition=edition).order_by("sort_order", "code")
    ]


def directory_prices(edition: MatrixEdition) -> list[dict]:
    periods = list(DnServicePricePeriod.objects.filter(edition=edition).order_by("-valid_from", "code"))
    period_by_id = {p.id: p for p in periods}
    rows = []
    for pr in DnServicePrice.objects.filter(period__edition=edition).select_related("service", "period"):
        p = period_by_id.get(pr.period_id)
        rows.append(
            {
                "Код": pr.service.code,
                "Название": _service_title_without_code(pr.service.code, pr.service.title),
                "Период": p.title or p.code if p else "",
                "С": p.valid_from.isoformat() if p else "",
                "По": p.valid_to.isoformat() if p and p.valid_to else "",
                "Цена": str(pr.amount),
            }
        )
    return rows


def service_code_options(edition: MatrixEdition) -> list[dict]:
    rows = []
    for s in DnService.objects.filter(edition=edition).order_by("sort_order", "code"):
        code = normalize_dn_service_code(s.code) or s.code
        title = _service_title_without_code(s.code, s.title)
        label = f"{code} — {title}" if title else code
        rows.append({"label": label, "value": code})
    return rows


def unavailable_table(edition: MatrixEdition) -> list[dict]:
    titles = {
        normalize_dn_service_code(s.code) or s.code: _service_title_without_code(s.code, s.title)
        for s in DnService.objects.filter(edition=edition)
    }
    diag_titles = {
        normalize_mkb(d.mkb_code): (d.title or "").strip()
        for d in DnDiagnosis.objects.filter(edition=edition)
    }
    rows = []
    for row in DnUnavailableService.objects.filter(edition=edition).order_by("service_code", "mkb_code"):
        code = row.service_code
        title = titles.get(code) or ""
        mkb = row.mkb_code or ""
        if mkb:
            dtitle = diag_titles.get(mkb, "")
            scope = f"{mkb} — {dtitle}" if dtitle else mkb
        else:
            scope = "Все диагнозы"
        rows.append(
            {
                "id": row.id,
                "Код": code,
                "Название": title or "нет в текущей матрице",
                "Диагноз": scope,
                "Комментарий": row.note or "",
            }
        )
    return rows


def add_unavailable_service(
    edition: MatrixEdition,
    service_code: str,
    mkb_code: str | None = None,
    note: str = "",
) -> tuple[bool, str]:
    code = normalize_dn_service_code(service_code)
    if not code:
        return False, "Выберите услугу."
    mkb = normalize_mkb(mkb_code)
    if mkb and not DnDiagnosis.objects.filter(edition=edition, mkb_code=mkb).exists():
        return False, f"Диагноз {mkb} не найден в этой редакции."
    known = {normalize_dn_service_code(s.code) for s in DnService.objects.filter(edition=edition)}
    if code not in known:
        return False, f"Услуга {code} не найдена в этой редакции."
    obj, created = DnUnavailableService.objects.get_or_create(
        edition=edition,
        service_code=code,
        mkb_code=mkb,
        defaults={"note": (note or "")[:256]},
    )
    if not created:
        return False, "Эта услуга уже в списке «не проводится»."
    return True, "Услуга добавлена в список «не проводится»."


def delete_unavailable_services(edition: MatrixEdition, ids: list[int]) -> int:
    if not ids:
        return 0
    return DnUnavailableService.objects.filter(edition=edition, id__in=ids).delete()[0]
