from __future__ import annotations

import re
from collections import Counter
from typing import Any

SERVICE_CODE_RE = re.compile(
    r"^([AB]\d{2}\.\d{2,3}\.\d{3})(?:\.\d{3})?$",
    re.IGNORECASE,
)

SERVICE_CODE_TOKEN_FIND_RE = re.compile(
    r"[AB]\d{2}\.\d{2,3}\.\d{3}(?:\.\d{3})?",
    re.IGNORECASE,
)

_SERVICE_LIKE_RE = re.compile(r"^[AB]\d{2}[-.]", re.IGNORECASE)


def normalize_dn_service_code(raw: str | None) -> str:
    """Канонический код услуги ДН: точки, верхний регистр (A08.20.017)."""
    code = str(raw or "").strip().upper().replace(",", ".").replace(" ", "")
    code = code.replace("А", "A").replace("В", "B")
    if not code:
        return ""
    if _SERVICE_LIKE_RE.match(code):
        code = code.replace("-", ".")
    match = SERVICE_CODE_RE.match(code)
    if match:
        return match.group(0).upper()
    return code


def extract_service_code_tokens(raw: str) -> frozenset[str]:
    out: set[str] = set()
    for m in SERVICE_CODE_TOKEN_FIND_RE.finditer(str(raw or "")):
        norm = normalize_dn_service_code(m.group(0))
        if norm and SERVICE_CODE_RE.match(norm):
            out.add(norm)
    return frozenset(out)


class ServiceCodeEquivalence:
    """Связь альтернативных кодов одной услуги (B04.047.001 ≡ B04.047.003)."""

    def __init__(self, matrix_services: list[tuple[int, str, str]] | None = None) -> None:
        self._parent: dict[str, str] = {}

        if not matrix_services:
            return
        for row in matrix_services:
            _sid, code, title = row[0], row[1], row[2]
            tokens = extract_service_code_tokens(f"{code} {title}")
            if len(tokens) < 2:
                continue
            root = min(tokens)
            for token in tokens:
                self._union(token, root)

    def _find(self, code: str) -> str:
        self._parent.setdefault(code, code)
        parent = self._parent[code]
        if parent != code:
            self._parent[code] = self._find(parent)
        return self._parent[code]

    def _union(self, a: str, b: str) -> None:
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            self._parent[rb] = ra

    def equivalent(self, code_a: str, code_b: str) -> bool:
        a = normalize_dn_service_code(code_a)
        b = normalize_dn_service_code(code_b)
        if not a or not b:
            return False
        if a == b:
            return True
        if not self._parent:
            return False
        return self._find(a) == self._find(b)


def service_code_base(code: str) -> str:
    norm = normalize_dn_service_code(code)
    if not norm:
        return ""
    match = SERVICE_CODE_RE.match(norm)
    return match.group(1).upper() if match else norm


def service_codes_compatible(
    actual_code: str,
    expected_code: str,
    *,
    code_equiv: ServiceCodeEquivalence | None = None,
) -> bool:
    act = normalize_dn_service_code(actual_code)
    exp = normalize_dn_service_code(expected_code)
    if not act or not exp:
        return False
    if act == exp:
        return True
    if act.startswith(exp + "."):
        return True
    if exp.startswith(act + "."):
        return True
    if code_equiv is not None and code_equiv.equivalent(act, exp):
        return True
    return False


def compare_expected_actual_services(
    expected: dict[str, dict[str, Any]],
    actual: Counter[str],
    *,
    code_equiv: ServiceCodeEquivalence | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    remaining_need: dict[str, int] = {code: int(info.get("qty", 0)) for code, info in expected.items()}
    remaining_actual: Counter[str] = Counter(actual)

    for exp_code in sorted(remaining_need.keys(), key=len, reverse=True):
        need = remaining_need.get(exp_code, 0)
        if need <= 0:
            continue
        for act_code in sorted(list(remaining_actual.keys()), key=len, reverse=True):
            if need <= 0:
                break
            if not service_codes_compatible(act_code, exp_code, code_equiv=code_equiv):
                continue
            take = min(remaining_actual[act_code], need)
            if take <= 0:
                continue
            remaining_need[exp_code] -= take
            remaining_actual[act_code] -= take
            if remaining_actual[act_code] <= 0:
                del remaining_actual[act_code]

    missing = [{"code": code, "qty": qty} for code, qty in sorted(remaining_need.items()) if qty > 0]
    extra = [{"code": code, "qty": int(qty)} for code, qty in sorted(remaining_actual.items()) if qty > 0]
    return missing, extra
