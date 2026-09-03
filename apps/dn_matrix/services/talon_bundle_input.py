"""Разбор файла простановки и сбор строк из непрошедших."""

from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any

import pandas as pd

from apps.dn_matrix.services.batch_pick import parse_mkb_list
from apps.dn_matrix.services.matrix import normalize_mkb
from apps.dn_matrix.services.talon_bundle import TalonBundleItem, extract_doctor_id, norm_enp


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        val = row.get(key)
        if val is None:
            continue
        text = str(val).strip()
        if text:
            return text
    return ""

_COL_ALIASES: dict[str, tuple[str, ...]] = {
    "enp": ("енп", "enp", "полис", "номер полиса"),
    "doctor": ("код врача", "врач", "doctor", "doctor_id", "код", "id врача"),
    "corpus": ("корпус", "корп", "building", "подразделение"),
    "date_from": ("дата начала", "начало", "date_from", "дата с", "с", "period_from"),
    "date_to": ("дата окончания", "окончание", "date_to", "дата по", "по", "period_to"),
    "ds1": ("основной мкб", "основной диагноз", "диагноз", "ds1", "мкб", "основной"),
    "ds2": ("сопутствующие мкб", "сопутствующие", "диагноз 2", "ds2", "сопутствующий"),
    "profile": ("профиль", "специальность", "specialty", "профиль дн"),
    "category": ("категория", "группа 168н", "группа основного", "группа"),
    "birth": ("дата рождения", "др", "dr", "дата рожд", "рождение"),
}


def _norm_col(name: object) -> str:
    return str(name or "").replace("\ufeff", "").strip().lower().replace("ё", "е")


def _map_columns(df: pd.DataFrame) -> dict[str, str]:
    found: dict[str, str] = {}
    by_norm = {_norm_col(c): c for c in df.columns}
    for key, aliases in _COL_ALIASES.items():
        for alias in aliases:
            if alias in by_norm:
                found[key] = by_norm[alias]
                break
    return found


def _cell_str(val: object) -> str:
    if val is None:
        return ""
    if hasattr(val, "item") and not isinstance(val, (bytes, str, datetime, date)):
        try:
            val = val.item()
        except (ValueError, AttributeError, OverflowError):
            pass
    try:
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    if isinstance(val, int) and not isinstance(val, bool):
        return str(val)
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, date):
        return val.isoformat()
    text = str(val).strip()
    if text.endswith(".0") and text.replace(".", "", 1).isdigit():
        return text[:-2]
    return text


def parse_date_cell(val: object) -> date | None:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    text = _cell_str(val)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d.%m.%y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    try:
        ts = pd.to_datetime(val, dayfirst=True, errors="coerce")
    except Exception:
        return None
    if pd.isna(ts):
        return None
    return ts.date()


def parse_input_dataframe(df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[str]]:
    """Строки файла: ЕНП, врач, корпус, даты; диагнозы/профиль — если колонки есть."""
    warnings: list[str] = []
    if df is None or df.empty:
        return [], ["Файл пустой."]
    cols = _map_columns(df)
    if "enp" not in cols:
        return [], ["В файле нет колонки ЕНП."]
    if "doctor" not in cols:
        warnings.append("Нет колонки «Код врача» — будет использовано поле на форме.")
    if "corpus" not in cols:
        warnings.append("Нет колонки «Корпус» — будет использовано поле на форме.")
    if "date_from" not in cols or "date_to" not in cols:
        warnings.append("Нет колонок дат — будет использован интервал на форме.")
    rows: list[dict[str, Any]] = []
    for idx, raw in enumerate(df.to_dict("records"), start=2):
        enp = norm_enp(_cell_str(raw.get(cols["enp"])))
        if not enp:
            warnings.append(f"Строка {idx}: нет ЕНП.")
            continue
        doctor = _cell_str(raw.get(cols["doctor"])) if "doctor" in cols else ""
        corpus = _cell_str(raw.get(cols["corpus"])) if "corpus" in cols else ""
        date_from = parse_date_cell(raw.get(cols["date_from"])) if "date_from" in cols else None
        date_to = parse_date_cell(raw.get(cols["date_to"])) if "date_to" in cols else None
        ds1 = normalize_mkb(_cell_str(raw.get(cols["ds1"]))) if "ds1" in cols else ""
        ds2 = parse_mkb_list(_cell_str(raw.get(cols["ds2"]))) if "ds2" in cols else []
        profile = _cell_str(raw.get(cols["profile"])) if "profile" in cols else ""
        category = _cell_str(raw.get(cols["category"])) if "category" in cols else ""
        birth = parse_date_cell(raw.get(cols["birth"])) if "birth" in cols else None
        rows.append(
            {
                "enp": enp,
                "doctor": doctor,
                "corpus": corpus,
                "date_from": date_from,
                "date_to": date_to,
                "ds1": ds1,
                "ds2": ds2,
                "profile": profile,
                "category": category,
                "birth": birth,
            }
        )
    if not rows:
        warnings.append("После разбора не осталось строк с ЕНП.")
    return rows, warnings


def read_upload_dataframe(raw: bytes, filename: str) -> pd.DataFrame:
    name = (filename or "").lower()
    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    elif name.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(raw))
    else:
        df = None
        for enc in ("utf-8-sig", "utf-8", "cp1251"):
            for sep in (";", ",", "\t"):
                try:
                    candidate = pd.read_csv(io.BytesIO(raw), encoding=enc, sep=sep)
                except Exception:
                    continue
                if candidate is not None and not candidate.empty:
                    df = candidate
                    break
            if df is not None:
                break
        if df is None:
            df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig", sep=None, engine="python")
    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
    return df


def _index_not_passed(rows: list[dict[str, Any]], *, grouped: bool) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows or []:
        enp = norm_enp(_first_present(row, ("ЕНП", "enp")))
        if not enp:
            continue
        out.setdefault(enp, []).append(row)
    return out


def _item_from_not_passed_row(
    row: dict[str, Any],
    *,
    grouped: bool,
    doctor: str,
    corpus: str,
    date_from: date | None,
    date_to: date | None,
) -> TalonBundleItem | None:
    enp = norm_enp(_first_present(row, ("ЕНП", "enp")))
    if not enp:
        return None
    if grouped:
        ds1 = normalize_mkb(_first_present(row, ("Основной МКБ", "main_mkb")))
        ds2 = parse_mkb_list(_first_present(row, ("Сопутствующие МКБ", "accompanying")))
        profile = _first_present(row, ("Профиль", "main_profile"))
        category = _first_present(row, ("Группа основного", "main_category", "Группа 168н"))
        row_doctor = _first_present(row, ("Врач", "main_doctor"))
        birth_raw = _first_present(row, ("Дата рождения", "dr"))
    else:
        ds1 = normalize_mkb(_first_present(row, ("МКБ", "ds_code", "Основной МКБ")))
        ds2 = []
        profile = _first_present(row, ("Профиль", "profile_cluster"))
        category = _first_present(row, ("Группа 168н", "category_168n"))
        row_doctor = _first_present(row, ("Врач", "doctor"))
        birth_raw = _first_present(row, ("Дата рождения", "dr"))
    if not ds1:
        return None
    doctor_id = extract_doctor_id(doctor) or extract_doctor_id(row_doctor) or (doctor or "").strip()
    return TalonBundleItem(
        enp=enp,
        ds1=ds1,
        ds2_list=ds2,
        specialty=profile,
        doctor_id=doctor_id,
        corpus=corpus,
        category_168n=category,
        date_from=date_from,
        date_to=date_to,
        birth_date=parse_date_cell(birth_raw) if birth_raw else None,
    )


def items_from_not_passed_rows(
    rows: list[dict[str, Any]],
    *,
    grouped: bool,
    doctor: str = "",
    corpus: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[TalonBundleItem], list[str]]:
    warnings: list[str] = []
    items: list[TalonBundleItem] = []
    empty = 0
    for row in rows or []:
        item = _item_from_not_passed_row(
            row,
            grouped=grouped,
            doctor=doctor,
            corpus=corpus,
            date_from=date_from,
            date_to=date_to,
        )
        if item is None:
            empty += 1
            continue
        items.append(item)
    if empty:
        warnings.append(f"Пропущено строк непрошедших без ЕНП/МКБ: {empty}.")
    if not items:
        warnings.append("Нет строк непрошедших для простановки.")
    return items, warnings


def _profile_matches(row_profile: str, wanted: str) -> bool:
    a = (row_profile or "").strip().lower().replace("ё", "е")
    b = (wanted or "").strip().lower().replace("ё", "е")
    return bool(a and b and a == b)


def enrich_file_rows_with_not_passed(
    file_rows: list[dict[str, Any]],
    not_passed_rows: list[dict[str, Any]],
    *,
    grouped: bool = True,
    default_doctor: str = "",
    default_corpus: str = "",
    default_date_from: date | None = None,
    default_date_to: date | None = None,
) -> tuple[list[TalonBundleItem], list[str]]:
    """Файл даёт ЕНП/врача/корпус/даты; диагнозы и профиль — из непрошедших, если в файле пусто."""
    warnings: list[str] = []
    indexed = _index_not_passed(not_passed_rows, grouped=grouped)
    items: list[TalonBundleItem] = []

    for raw in file_rows:
        enp = norm_enp(raw.get("enp"))
        if not enp:
            continue
        doctor = extract_doctor_id(raw.get("doctor")) or _cell_str(raw.get("doctor")) or default_doctor
        corpus = _cell_str(raw.get("corpus")) or default_corpus
        date_from = raw.get("date_from") or default_date_from
        date_to = raw.get("date_to") or default_date_to
        file_ds1 = normalize_mkb(raw.get("ds1") or "")
        file_ds2 = list(raw.get("ds2") or [])
        file_profile = _cell_str(raw.get("profile"))
        file_category = _cell_str(raw.get("category"))
        file_birth = raw.get("birth")
        if not isinstance(file_birth, date):
            file_birth = parse_date_cell(file_birth)

        if file_ds1:
            items.append(
                TalonBundleItem(
                    enp=enp,
                    ds1=file_ds1,
                    ds2_list=file_ds2,
                    specialty=file_profile,
                    doctor_id=doctor,
                    corpus=corpus,
                    category_168n=file_category,
                    date_from=date_from,
                    date_to=date_to,
                    birth_date=file_birth,
                )
            )
            continue

        matches = list(indexed.get(enp) or [])
        if file_profile:
            filtered = [
                r
                for r in matches
                if _profile_matches(
                    _first_present(r, ("Профиль", "main_profile", "profile_cluster")),
                    file_profile,
                )
            ]
            if filtered:
                matches = filtered
            else:
                warnings.append(f"ЕНП {enp}: профиль «{file_profile}» не найден среди непрошедших.")
        if not matches:
            warnings.append(f"ЕНП {enp}: нет непрошедших — нечем заполнить диагнозы.")
            continue
        if len(matches) > 1:
            warnings.append(f"ЕНП {enp}: {len(matches)} профиля в непрошедших — по талону на каждый.")
        for row in matches:
            item = _item_from_not_passed_row(
                row,
                grouped=grouped,
                doctor=doctor,
                corpus=corpus,
                date_from=date_from,
                date_to=date_to,
            )
            if item is None:
                continue
            if not item.doctor_id:
                item.doctor_id = doctor
            if not item.corpus:
                item.corpus = corpus
            if file_birth:
                item.birth_date = file_birth
            items.append(item)

    if not items:
        warnings.append("Не удалось собрать ни одного талона из файла.")
    return items, warnings
