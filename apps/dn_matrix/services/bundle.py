from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

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
    DnSpecialty,
    MatrixEdition,
)
from apps.dn_matrix.services.matrix import normalize_mkb
from apps.dn_matrix.services.service_codes import normalize_dn_service_code


SCHEMA_VERSION = 1


def _bundle_service_code(raw: str) -> str:
    code = normalize_dn_service_code(raw)
    return (code or str(raw).strip())[:32]


def compute_bundle_checksum(payload: dict) -> str:
    body = {k: v for k, v in payload.items() if k != "checksum"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_bundle(edition: MatrixEdition) -> dict:
    e = edition
    data: dict = {
        "schema_version": SCHEMA_VERSION,
        "edition": {
            "code": e.code,
            "title": e.title,
            "effective_from": e.effective_from.isoformat(),
            "effective_to": e.effective_to.isoformat() if e.effective_to else None,
            "status": e.status,
            "notes": e.notes or "",
            "max_doctor_visits": e.max_doctor_visits,
        },
        "specialties": [
            {"code": s.code, "title": s.title, "sort_order": s.sort_order}
            for s in e.specialties.order_by("sort_order", "code")
        ],
        "diagnosis_categories": [
            {
                "code": c.code,
                "title": c.title,
                "parent_code": (c.parent.code if c.parent_id else None),
                "sort_order": c.sort_order,
            }
            for c in e.diagnosis_categories.order_by("sort_order", "code")
        ],
        "diagnoses": [
            {
                "mkb_code": d.mkb_code,
                "title": d.title,
                "category_code": d.category.code,
            }
            for d in e.diagnoses.select_related("category").order_by("mkb_code")
        ],
        "diagnosis_specialties": [
            {
                "mkb_code": ds.diagnosis.mkb_code,
                "specialty_code": ds.specialty.code,
                "kind": ds.kind,
            }
            for ds in DnDiagnosisSpecialty.objects.filter(diagnosis__edition=e)
            .select_related("diagnosis", "specialty")
            .order_by("diagnosis__mkb_code", "specialty__code", "kind")
        ],
        "diagnosis_groups": [
            {"code": g.code, "title": g.title, "rule": g.rule or {}, "sort_order": g.sort_order}
            for g in e.diagnosis_groups.order_by("sort_order", "code")
        ],
        "diagnosis_group_memberships": [
            {"group_code": m.group.code, "mkb_code": m.diagnosis.mkb_code}
            for m in DnDiagnosisGroupMembership.objects.filter(group__edition=e)
            .select_related("group", "diagnosis")
            .order_by("group__code", "diagnosis__mkb_code")
        ],
        "services": [
            {
                "code": _bundle_service_code(s.code),
                "title": s.title,
                "sort_order": s.sort_order,
                "sex_restriction": s.sex_restriction or "",
            }
            for s in e.services.order_by("sort_order", "code")
        ],
        "service_price_periods": [
            {
                "code": p.code,
                "title": p.title or "",
                "valid_from": p.valid_from.isoformat(),
                "valid_to": p.valid_to.isoformat() if p.valid_to else None,
            }
            for p in e.price_periods.order_by("-valid_from", "code")
        ],
        "service_prices": [
            {
                "period_code": pr.period.code,
                "service_code": _bundle_service_code(pr.service.code),
                "amount": str(pr.amount),
                "currency": pr.currency,
            }
            for pr in DnServicePrice.objects.filter(period__edition=e).select_related("period", "service")
        ],
        "service_requirements": [
            {
                "service_code": _bundle_service_code(r.service.code),
                "specialty_code": r.specialty.code if r.specialty_id else None,
                "mkb_code": r.diagnosis.mkb_code if r.diagnosis_id else None,
                "diagnosis_group_code": r.diagnosis_group.code if r.diagnosis_group_id else None,
            }
            for r in DnServiceRequirement.objects.filter(service__edition=e).select_related(
                "service", "specialty", "diagnosis", "diagnosis_group"
            )
        ],
    }
    data["checksum"] = compute_bundle_checksum(data)
    return data


def verify_bundle_checksum(data: dict) -> None:
    declared = data.get("checksum")
    if not isinstance(declared, str):
        raise ValidationError({"checksum": "Отсутствует или некорректен checksum."})
    actual = compute_bundle_checksum(data)
    if actual != declared:
        raise ValidationError({"checksum": "Checksum не совпадает с содержимым пакета."})


def _import_model_map(apps):
    if apps is None:
        return {
            "MatrixEdition": MatrixEdition,
            "DnSpecialty": DnSpecialty,
            "DnDiagnosisCategory": DnDiagnosisCategory,
            "DnDiagnosis": DnDiagnosis,
            "DnDiagnosisSpecialty": DnDiagnosisSpecialty,
            "DnDiagnosisGroup": DnDiagnosisGroup,
            "DnDiagnosisGroupMembership": DnDiagnosisGroupMembership,
            "DnService": DnService,
            "DnServicePricePeriod": DnServicePricePeriod,
            "DnServicePrice": DnServicePrice,
            "DnServiceRequirement": DnServiceRequirement,
        }
    return {
        "MatrixEdition": apps.get_model("dn_matrix", "MatrixEdition"),
        "DnSpecialty": apps.get_model("dn_matrix", "DnSpecialty"),
        "DnDiagnosisCategory": apps.get_model("dn_matrix", "DnDiagnosisCategory"),
        "DnDiagnosis": apps.get_model("dn_matrix", "DnDiagnosis"),
        "DnDiagnosisSpecialty": apps.get_model("dn_matrix", "DnDiagnosisSpecialty"),
        "DnDiagnosisGroup": apps.get_model("dn_matrix", "DnDiagnosisGroup"),
        "DnDiagnosisGroupMembership": apps.get_model("dn_matrix", "DnDiagnosisGroupMembership"),
        "DnService": apps.get_model("dn_matrix", "DnService"),
        "DnServicePricePeriod": apps.get_model("dn_matrix", "DnServicePricePeriod"),
        "DnServicePrice": apps.get_model("dn_matrix", "DnServicePrice"),
        "DnServiceRequirement": apps.get_model("dn_matrix", "DnServiceRequirement"),
    }


@transaction.atomic
def import_bundle(data: dict, *, apps=None, activate: bool = False) -> MatrixEdition:
    """Импорт: создаёт или обновляет издание по code. По умолчанию статус draft."""
    M = _import_model_map(apps)
    MatrixEditionModel = M["MatrixEdition"]

    verify_bundle_checksum(data)
    if int(data.get("schema_version", 0)) != SCHEMA_VERSION:
        raise ValidationError({"schema_version": "Поддерживается только schema_version=1."})

    ed = data.get("edition") or {}
    code = (ed.get("code") or "").strip()
    if not code:
        raise ValidationError({"edition": {"code": "Обязательное поле."}})

    def parse_date(val):
        if val is None or val == "":
            return None
        if isinstance(val, str):
            return datetime.strptime(val[:10], "%Y-%m-%d").date()
        return val

    eff_from = parse_date(ed.get("effective_from"))
    if eff_from is None:
        raise ValidationError({"edition": {"effective_from": "Обязательное поле даты."}})
    eff_to = parse_date(ed.get("effective_to")) if ed.get("effective_to") else None

    raw_max_visits = ed.get("max_doctor_visits")
    if raw_max_visits is None or raw_max_visits == "":
        max_doctor_visits = 1 if eff_from < date(2026, 4, 1) else 3
    else:
        max_doctor_visits = min(max(int(raw_max_visits), 1), 3)

    status = getattr(getattr(MatrixEditionModel, "Status", None), "DRAFT", "draft")
    if activate:
        status = getattr(getattr(MatrixEditionModel, "Status", None), "ACTIVE", "active")

    edition, _created = MatrixEditionModel.objects.update_or_create(
        code=code,
        defaults={
            "title": str(ed.get("title") or code)[:256],
            "effective_from": eff_from,
            "effective_to": eff_to,
            "status": status,
            "notes": str(ed.get("notes") or "")[:10000],
            "max_doctor_visits": max_doctor_visits,
        },
    )

    M["DnServiceRequirement"].objects.filter(service__edition=edition).delete()
    M["DnServicePrice"].objects.filter(period__edition=edition).delete()
    M["DnServicePricePeriod"].objects.filter(edition=edition).delete()
    M["DnService"].objects.filter(edition=edition).delete()
    M["DnDiagnosisGroupMembership"].objects.filter(group__edition=edition).delete()
    M["DnDiagnosisSpecialty"].objects.filter(diagnosis__edition=edition).delete()
    M["DnDiagnosis"].objects.filter(edition=edition).delete()
    M["DnDiagnosisGroup"].objects.filter(edition=edition).delete()
    M["DnDiagnosisCategory"].objects.filter(edition=edition).delete()
    M["DnSpecialty"].objects.filter(edition=edition).delete()

    specs = [
        M["DnSpecialty"](
            edition=edition,
            code=str(row["code"]).strip()[:64],
            title=str(row.get("title") or row["code"])[:256],
            sort_order=int(row.get("sort_order") or 0),
        )
        for row in data.get("specialties") or []
    ]
    M["DnSpecialty"].objects.bulk_create(specs)

    cat_by_code: dict[str, object] = {}
    cats = []
    for row in data.get("diagnosis_categories") or []:
        c = M["DnDiagnosisCategory"](
            edition=edition,
            parent=None,
            code=str(row["code"]).strip()[:64],
            title=str(row.get("title") or row["code"])[:256],
            sort_order=int(row.get("sort_order") or 0),
        )
        cat_by_code[c.code] = c
        cats.append(c)
    M["DnDiagnosisCategory"].objects.bulk_create(cats)
    cat_by_code = {c.code: c for c in M["DnDiagnosisCategory"].objects.filter(edition=edition)}
    parent_updates = []
    for row in data.get("diagnosis_categories") or []:
        pcode = row.get("parent_code")
        if not pcode:
            continue
        child = cat_by_code.get(str(row["code"]).strip())
        parent = cat_by_code.get(str(pcode).strip())
        if child and parent:
            child.parent = parent
            parent_updates.append(child)
    if parent_updates:
        M["DnDiagnosisCategory"].objects.bulk_update(parent_updates, ["parent"])

    diagnoses = []
    for row in data.get("diagnoses") or []:
        mkb = normalize_mkb(str(row["mkb_code"]))
        ccode = str(row["category_code"]).strip()
        cat = cat_by_code.get(ccode)
        if not cat:
            raise ValidationError({"diagnoses": f"Неизвестная категория {ccode} для МКБ {mkb}"})
        diagnoses.append(
            M["DnDiagnosis"](edition=edition, category=cat, mkb_code=mkb, title=str(row.get("title") or mkb)[:512])
        )
    M["DnDiagnosis"].objects.bulk_create(diagnoses)

    diag_by_mkb = {d.mkb_code: d for d in M["DnDiagnosis"].objects.filter(edition=edition)}
    spec_by_code = {s.code: s for s in M["DnSpecialty"].objects.filter(edition=edition)}

    spec_links = []
    for row in data.get("diagnosis_specialties") or []:
        mkb = normalize_mkb(str(row["mkb_code"]))
        sc = str(row["specialty_code"]).strip()
        d = diag_by_mkb.get(mkb)
        s = spec_by_code.get(sc)
        if not d or not s:
            raise ValidationError({"diagnosis_specialties": f"Не найдены сущности для {mkb}/{sc}"})
        spec_links.append(
            M["DnDiagnosisSpecialty"](
                diagnosis=d,
                specialty=s,
                kind=str(row.get("kind") or "primary")[:16],
            )
        )
    M["DnDiagnosisSpecialty"].objects.bulk_create(spec_links)

    groups = [
        M["DnDiagnosisGroup"](
            edition=edition,
            code=str(row["code"]).strip()[:64],
            title=str(row.get("title") or row["code"])[:256],
            rule=row.get("rule") or {},
            sort_order=int(row.get("sort_order") or 0),
        )
        for row in data.get("diagnosis_groups") or []
    ]
    M["DnDiagnosisGroup"].objects.bulk_create(groups)
    group_by_code = {g.code: g for g in M["DnDiagnosisGroup"].objects.filter(edition=edition)}

    memberships = []
    seen_memberships: set[tuple[int, int]] = set()
    for row in data.get("diagnosis_group_memberships") or []:
        gc = str(row["group_code"]).strip()
        mkb = normalize_mkb(str(row["mkb_code"]))
        g = group_by_code.get(gc)
        d = diag_by_mkb.get(mkb)
        if not g or not d:
            raise ValidationError({"diagnosis_group_memberships": f"Нет группы/диагноза {gc}/{mkb}"})
        key = (g.id, d.id)
        if key in seen_memberships:
            continue
        seen_memberships.add(key)
        memberships.append(M["DnDiagnosisGroupMembership"](group=g, diagnosis=d))
    M["DnDiagnosisGroupMembership"].objects.bulk_create(memberships)

    services = [
        M["DnService"](
            edition=edition,
            code=_bundle_service_code(str(row["code"])),
            title=str(row.get("title") or row["code"])[:512],
            sort_order=int(row.get("sort_order") or 0),
            sex_restriction=str(row.get("sex_restriction") or row.get("sex") or "")[:1],
        )
        for row in data.get("services") or []
    ]
    M["DnService"].objects.bulk_create(services)
    svc_by_code = {s.code: s for s in M["DnService"].objects.filter(edition=edition)}

    periods = [
        M["DnServicePricePeriod"](
            edition=edition,
            code=str(row["code"]).strip()[:64],
            title=str(row.get("title") or "")[:256],
            valid_from=parse_date(row["valid_from"]),
            valid_to=parse_date(row["valid_to"]) if row.get("valid_to") else None,
        )
        for row in data.get("service_price_periods") or []
    ]
    M["DnServicePricePeriod"].objects.bulk_create(periods)
    period_by_code = {p.code: p for p in M["DnServicePricePeriod"].objects.filter(edition=edition)}

    prices = []
    for row in data.get("service_prices") or []:
        p = period_by_code.get(str(row["period_code"]).strip())
        s = svc_by_code.get(_bundle_service_code(str(row["service_code"])))
        if not p or not s:
            raise ValidationError({"service_prices": "Неверный period_code или service_code"})
        prices.append(
            M["DnServicePrice"](
                period=p,
                service=s,
                amount=Decimal(str(row["amount"])),
                currency=str(row.get("currency") or "RUB")[:8],
            )
        )
    M["DnServicePrice"].objects.bulk_create(prices)

    requirements = []
    for row in data.get("service_requirements") or []:
        s = svc_by_code.get(_bundle_service_code(str(row["service_code"])))
        if not s:
            raise ValidationError({"service_requirements": "Неизвестная услуга"})
        sp = row.get("specialty_code")
        mk = row.get("mkb_code")
        gc = row.get("diagnosis_group_code")
        spec_o = spec_by_code.get(str(sp).strip()) if sp not in (None, "") else None
        diag_o = diag_by_mkb.get(normalize_mkb(str(mk))) if mk not in (None, "") else None
        grp_o = group_by_code.get(str(gc).strip()) if gc not in (None, "") else None
        if spec_o is None and diag_o is None and grp_o is None:
            raise ValidationError(
                {"service_requirements": "Каждая строка должна задавать специальность, МКБ или группу."}
            )
        requirements.append(
            M["DnServiceRequirement"](
                service=s,
                specialty=spec_o,
                diagnosis=diag_o,
                diagnosis_group=grp_o,
            )
        )
    M["DnServiceRequirement"].objects.bulk_create(requirements)

    return edition
